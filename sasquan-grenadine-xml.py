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

import xml.etree.ElementTree
import csv
import re
import sys

import config
from participant import Participant
from room import Level, Room
from session import Session
from times import Day, Time, Duration

def read(fn):
    """ Read an XML file, and return an array of sesions and an array of participants. """
    global sessions, participants
    sessions = []
    participants = {}
    curday = None

    for timeslot in xml.etree.ElementTree.parse(fn).getroot():
        assert timeslot.tag == 'time'
        start = timeslot[0]
        assert(start.tag == 'start')
        assert(start[0].tag == 'day')
        day = start[0].text
        assert(start[1].tag == 'time')
        time = start[1].text
        if day != curday:
            curday = day
            d = Day(day)
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
        t = Time(time, d)
        d.times.append(t)
        t.sessions = []
        
        for item in timeslot[1:]:
            assert(item.tag == 'item')
            s = Session()
            s.time = t
            parse_item(s, item)
            sessions.append(s)
            t.sessions.append(s)
        t.sessions = sorted(t.sessions)

    sessions = sorted(sessions)
    return (sessions, participants)

def parse_item(session, element):
    for a in element:
        if a.tag == 'venue':
            parse_venue(session, a)
        if a.tag == 'room':
            parse_room(session, a)
        elif a.tag == 'details':
            parse_details(session, a)

def cleanup(field, minimal=False):
    # convert all whitespace (including newlines) to single spaces
    field = re.sub(r'\s+', ' ', field)

    if not minimal:
        # change bold to italic
        field = re.sub(r'<(/?)em>', r'<\1i>', field)
        field = re.sub(r'<(/?)strong>', r'<\1i>', field)
        # <strong><em> (redundant but not technically wrong) -> <i><i>
        #field = re.sub(r'<i><i>', r'<i>', field)
        #field = re.sub(r'</i></i>', r'</i>', field)

        # change explicit line breaks to newline
        field = re.sub(r'<br ?/> ?', r'\n', field)
        field = re.sub(r'</p> ?<p> ?', r'\n', field)
        field = re.sub(r'^<p>(.*)</p>$', r'\1', field)
        field = re.sub(r' ?<p>', r'\n', field)
        field = re.sub(r'</p>', r'', field)

        # lists - hack for one session
        field = re.sub(r' ?<ul> ?', r'', field)
        field = re.sub(r' ?</ul> ?', r'\n\n', field)
        field = re.sub(r'<li> ?', r'\n<li>', field)

        # remove html tags we can't/won't support in print
        field = re.sub(r'</?span.*?> ?', r'', field)
        field = re.sub(r'</?div.*?> ?', r'', field)
        field = re.sub(r'</?hr.*?> ?', r'', field)
        field = re.sub(r'</?a.*?> ?', r'', field)
        field = re.sub(r'</?font.*?> ?', r'', field)

        # remove wtf
        field = re.sub('​', '', field)

    # remove extraneous whitespace
    field = re.sub(r'^\s+', '', field) # leading space
    field = re.sub(r'\s+$', '', field) # trailing space
    field = re.sub(r'\s+([,.;])', r'\1', field) # space before punctuation
    
    return field

def parse_venue(session, element):
    level = element.text
    try:
        session.level = config.level[level]
    except KeyError:
        if not config.quiet:
            sys.stderr.write('warning: new level %s\n' % level)
        session.level = Level(level)
        config.level[session.level.name] = session.level
        config.level[session.level.index] = session.level

def parse_room(session, element):
    room = element.text
    try:
        session.room = config.room[room]
    except KeyError:
        if not config.quiet:
            sys.stderr.write('warning: new room %s\n' % room)
        session.room = Room(room)
        #session.room.level = session.level
        config.room[session.room.name] = session.room
        config.room[session.room.index] = session.room
    try:
        for r in config.room_combo[room]:
            r.sessions.append(session)
    except KeyError:
        session.room.sessions.append(session)

def parse_details(session, element):
    for a in element:
        if a.tag == 'reference_number':
            parse_reference(session, a)
        elif a.tag == 'duration':
            parse_duration(session, a)
        elif a.tag == 'format':
            parse_format(session, a)
        #elif a.tag == 'tracks':
        #    parse_tracks(session, a)
        elif a.tag == 'tags':
            parse_tags(session, a)
        elif a.tag == 'title':
            parse_title(session, a)
        elif a.tag == 'description':
            parse_description(session, a)
        elif a.tag == 'people':
            parse_people(session, a)
        elif a.tag == 'xx':
            parse_xx(session, a)
        # ignore unused tracks, sigh
        # ignore short_title, short_description

def parse_reference(session, element):
    try:
        ref = int(element.text)
    except TypeError:
        ref = 0
        if not config.quiet:
            sys.stderr.write('warning: %s %s %s: empty reference_number element\n' % (session.time.day, session.time, session.room))
    session.sessionid = ref
    session.index = ref

def parse_duration(session, element):
    if element.text == '1':
        # e.g. Dealers Room Closes
        element.text = '0'
    session.duration = Duration(element.text)

def parse_format(session, element):
    session.type = element.text

def parse_tags(session, element):
    session.tags = []
    for a in element:
        assert(a.tag == 'tag')
        # XXX suppress duplicate tags (better done in database, eh?)
        if a.text in session.tags:
            if not config.quiet:
                sys.stderr.write('warning: %d: duplicate tag %s\n' % (session.index, a.text))
        else:            
            session.tags.append(a.text)
        # XXX create a Tag class (value, array of sessions) so we can xref

def parse_title(session, element):
    session.title = cleanup(element.text)

def parse_description(session, element):
    if element.text:
        session.description = cleanup(element.text)
    else:
        session.description = ''

def parse_people(session, element):
    global participants
    session.moderator = []
    session.participants = []
    for a in element:
        assert(a.tag == 'participant' or a.tag == 'moderator')
        for b in a:
            if b.tag == 'name':
                name = cleanup(b.text, minimal=True)
                # ignore job_title, company
        # XXX chname
        if (name in participants):
            p = participants[name]
        else:
            p = Participant(name)
            participants[name] = p
        session.participants.append(p)
        if a.tag == 'moderator':
            session.moderator.append(p)
        p.sessions.append(session)

if __name__ == '__main__':
    import sys

    import cmdline
    
    args = cmdline.cmdline(io=True, modes=False)
    (sessions, participants) = read(args.infile)

    for s in sessions:
        print('%04d' % s.index)
        print('%s %s (%s)' % (s.time.day, s.time, s.duration))
        print(s.room)
        print(s.title)
        print(s.description)
        if s.participants:
            pp = []
            for p in s.participants:
                name = p.__str__()
                if p in s.moderator:
                    name += ' (m)'
                pp.append(name)
            print(', '.join(pp))
        if s.tags:
            print('#' + ', #'.join(s.tags))
        print('\n')

    for p in sorted(participants.values()):
        ss = []
        for s in p.sessions:
            ss.append(str(s.index))
        print('%s: %s' % (str(p), ', '.join(ss)))
