#!/usr/bin/env python

# Copyright (c) 2014, Paul Selkirk
#
# Permission to use, copy, modify, and/or distribute this software for
# any purpose with or without fee is hereby granted, provided that the
# above copyright notice and this permission notice appear in all
# copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL
# WARRANTIES WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE
# AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL
# DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR
# PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER
# TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
# PERFORMANCE OF THIS SOFTWARE.

import csv
import re
import sys

import config
from participant import Participant
from room import Room
from session import Session
from times import Day, Time, Duration

def csv_reader(fn):
    if config.PY3:
        f = open(fn, 'rt', encoding='utf-8', newline='')
    else:
        f = open(fn, 'rb')
    reader = csv.DictReader(f)
    # lowercase field names
    fieldnames = reader.fieldnames
    for (i, name) in enumerate(fieldnames):
        fieldnames[i] = name.lower()
    reader.fieldnames = fieldnames
    return reader

def read(fn, raw=False):
    """ Read a CSV file, and return an array of sesions and an array of participants. """
    global sessions, participants
    sessions = []
    participants = {}
    curday = None
    curtime = None

    reader = csv_reader(fn)
    for row in reader:
        if not config.PY3:
            for key in row:
                row[key] = row[key].decode('utf-8')
        if row['day'] != curday:
            curday = row['day']
            d = Day(row['day'])
            # look up day in global list
            # we could make day[] a dict, indexed by number and name,
            # but that would complicate things, so we do it the C way
            found = False
            for dd in config.day:
                if dd == d:
                    d = dd
                    found = True
                    break
            if not found:
                d.index = len(config.day)
                config.day.append(d)
                d.times = []
        if row['time'] != curtime:
            curtime = row['time']
            t = Time(row['time'])
            t.day = d
            d.times.append(t)
            t.sessions = []
        s = Session()
        s.sessionid = row['sessionid']
        s.index = 0
        s.time = t
        parse_duration(s, row['duration'])
        parse_room(s, row['room'])
        parse_track(s, row['track'])
        parse_type(s, row['type'])
        parse_title(s, row['title'], raw)
        parse_description(s, row['description'], raw)
        parse_participants(s, row['participants'])
        sessions.append(s)
        t.sessions.append(s)

    sessions = sorted(sessions)
    # add session index
    for i, s in enumerate(sessions, start=1):
        s.index = i

    return (sessions, participants)

def parse_duration(session, text):
    session.duration = Duration(text)

def parse_room(session, text):
    if text in config.chroom:
        text = config.chroom[text]
    if session.sessionid in config.chroom:
        text = config.chroom[session.sessionid]
    try:
        session.room = config.room[text]
    except KeyError:
        if not config.quiet:
            sys.stderr.write('warning: new room %s\n' % text)
        session.room = Room(text)
        config.room[session.room.name] = session.room
        config.room[session.room.index] = session.room
    try:
        for r in config.room_combo[text]:
            r.sessions.append(session)
    except KeyError:
        session.room.sessions.append(session)

def parse_track(session, text):
    # XXX add Track class, to simplify tracklist.py
    session.track = text

def parse_type(session, text):
    session.type = text

def parse_title(session, text, raw):
    if session.sessionid in config.chtitle:
        text = config.chtitle[session.sessionid]
    session.title = text

def parse_description(session, text, raw):
    if session.sessionid in config.chdescr:
        text = config.chdescr[session.sessionid]
    elif not raw:
        text = cleanup(text)
    session.description = text

def parse_participants(session, text):
    global participants
    session.moderator = []
    session.participants = []
    if text:
        # chname has to operate on the full participants string
        # because some of the target names have commas in them
        for k,v in config.chname.items():
            text = text.replace(k, v)
        partic = re.split(r', ?', text)
        for i, p in enumerate(partic):
            (p, mod) = re.subn(r' ?\(m\)', '', p)
            p = cleanup(p, minimal=True)
            if p in participants:
                p = participants[p]
            else:
                p = Participant(p)
                participants[p.pubsname] = p
            p.sessions.append(session)
            # Arisia has at most one moderator per session, but Worldcon
            # allows multiple moderators, whatever that means, so the code
            # supports a list of moderators
            if mod:
                session.moderator.append(p)
            partic[i] = p
        # For Arisia, I prefer to sort the participants.
        # For Worldcon, I don't bother.
        # This really should be a flag in the config file.
        session.participants = sorted(partic)

def cleanup(field, minimal=False):
    # convert all whitespace (including newlines) to single spaces
    field = re.sub(r'\s+', ' ', field)

    # remove extraneous whitespace
    field = re.sub(r'^ ', '', field) # leading space
    field = re.sub(r' $', '', field) # trailing space
    field = re.sub(r' ([,.;])', r'\1', field) # space before punctuation

    if not minimal:
        # try to guess where italics were intended
        field = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<i>\1</i>', field) # _italic_
        field = re.sub(r'(?<!\w)\*([^*]+?)\*(?!\w)', r'<i>\1</i>', field) # *italic*

        # Let's don't mess with unicode that's already there;
        # let's concentrate on converting ascii to appropriate unicode

        # XXX filter bad unicode
        #field = re.sub(u'\u202a', '', field)
        #field = re.sub(u'\u202c', '', field)

        # convert dashes
        field = re.sub(r'(\d) *- *(\d)', r'\1'+u'\u2013'+r'\2', field) # the much-misunderstood n-dash
        field = re.sub(r' *-{2,} *', u'\u2014', field)   # m--dash, m -- dash, etc.
        field = re.sub(r' +- +', u'\u2014', field)       # m - dash

        # right quote before abbreviated years and decades ('70s)
        field = re.sub(r'\'([0-9])', u'\u2019'+r'\1', field)

        # convert quotes
        field = re.sub(r'^\'', u'\u2018', field) # beginning single quote -> left
        field = re.sub(r'\'$', u'\u2019', field) # ending single quote -> right
        field = re.sub(r'([^\w,.!?])\'(\w)', r'\1'+u'\u2018'+r'\2', field) # left single quote
        field = re.sub(r'\'', u'\u2019', field)  # all remaining single quotes -> right

        field = re.sub(r'^"', u'\u201c', field)  # beginning double quote -> left
        field = re.sub(r'"$', u'\u201d', field)  # ending double quote -> right
        field = re.sub(r'([^\w,.!?])"(\w)', r'\1'+u'\u201c'+r'\2', field) # left double quote
        field = re.sub(r'"', u'\u201d', field)   # all remaining double quotes -> right

    return field

def read_bios(fn, participants):
    """ Read the bios file, identify participants without sessions,
    and add fields for bios.py.
    """
    reader = csv_reader(fn)
    for row in reader:
        for key in row:
            if not config.PY3:
                row[key] = row[key].decode('utf-8')
            row[key] = cleanup(row[key], minimal=True)
        pubsname = row['pubsname']
        if pubsname in config.chname:
            pubsname = config.chname[pubsname]
        if not pubsname in participants:
            if not config.quiet:
                print('new participant "%s"' % pubsname)
            participants[pubsname] = Participant(pubsname)
        participants[pubsname].firstname = row['firstname']
        participants[pubsname].lastname = row['lastname']
        participants[pubsname].bio = cleanup(row['bio'])
        participants[pubsname].badgeid = row['badgeid']
    return participants

if __name__ == '__main__':
    import sys

    import cmdline
    
    args = cmdline.cmdline(io=True, modes=False)
    (sessions, participants) = read(args.infile)

    for s in sessions:
        print('%04d' % s.index)
        print('%s %s (%s)' % (s.time.day, s.time, s.duration))
        print(s.room)
        print(s.title.encode('utf-8'))
        print(s.description.encode('utf-8'))
        if s.participants:
            pp = []
            for p in s.participants:
                name = p.__str__()
                if p in s.moderator:
                    name += ' (m)'
                pp.append(name)
            print(', '.join(pp).encode('utf-8'))
        print('\n')

    for p in sorted(participants.values()):
        ss = []
        for s in p.sessions:
            ss.append(str(s.index))
        print('%s: %s' % (p.__str__().encode('utf-8'), ', '.join(ss)))
