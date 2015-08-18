#!/usr/bin/env python

# Copyright (c) 2014-2015, Paul Selkirk
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

""" Read schedule data from a CSV file created by the Zambia database. """

import csv
import re

import config
from participant import Participant
from session import Session

def csv_reader(fn):
    """Create a CSV reader. This works around differences between Python 2.7 and
    3.x handling of UTF-8.
    """

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

def read(fn):
    """ Read a CSV file, and create the global ``sessions`` list. """

    reader = csv_reader(fn)
    for row in reader:
        if not config.PY3:
            for key in row:
                row[key] = row[key].decode('utf-8')

        row['tracks'] = [row['track']]
        row['tags'] = []

        if row['participants']:
            mods = []
            # chname has to operate on the full participants string
            # because some of the target names have commas in them
            for k, v in config.chname.items():
                row['participants'] = row['participants'].replace(k, v)
            partic = re.split(r', ?', row['participants'])
            for i, p in enumerate(partic):
                (p, mod) = re.subn(r' ?\(m\)', '', p)
                if mod:
                    mods.append(p)
                partic[i] = p
            row['participants'] = partic
            row['moderators'] = mods
        else:
            row['participants'] = []
            row['moderators'] = []

        # cleanup
        for k in row:
            minimal = (k not in ['title', 'description'])
            row[k] = cleanup(row[k], minimal)

        # make a new session from this data
        session = Session(row)
        config.sessions.append(session)

    # sort
    config.sessions = sorted(config.sessions)
    # NOTE this changes the data type
    config.days = sorted(config.days.values())
    for day in config.days:
        day.time = sorted(day.time.values())

    # add session index
    for i, s in enumerate(config.sessions, start=1):
        s.index = i

def cleanup(field, minimal=False):
    # convert all whitespace (including newlines) to single spaces
    if type(field) is list:
        for i, f in enumerate(field):
            field[i] = cleanup(f)

    elif (type(field) is str) or (not config.PY3 and type(field) is unicode):
        # convert all whitespace (including newlines) to single spaces
        field = re.sub(r'\s+', ' ', field)

        # remove extraneous whitespace
        field = re.sub(r'^ ', '', field) # leading space
        field = re.sub(r' $', '', field) # trailing space
        field = re.sub(r' ([,.;])', r'\1', field) # space before punctuation

        if not minimal:
            # try to guess where italics were intended
             # _italic_
            field = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<i>\1</i>', field)
             # *italic*
            field = re.sub(r'(?<!\w)\*([^*]+?)\*(?!\w)', r'<i>\1</i>', field)

    return field

def read_bios(fn):
    """ Read the bios file, identify participants without sessions,
    and add fields for bios.py.
    """
    reader = csv_reader(fn)
    for row in reader:
        for key in row:
            if not config.PY3:
                row[key] = row[key].decode('utf-8')
            row[key] = cleanup(row[key])
        pubsname = row['pubsname']
        if pubsname in config.chname:
            pubsname = config.chname[pubsname]
        if not pubsname in config.participants:
            if not config.quiet:
                print('warning: new participant %s' % pubsname)
            config.participants[pubsname] = Participant(pubsname)
        config.participants[pubsname].firstname = row['firstname']
        config.participants[pubsname].lastname = row['lastname']
        config.participants[pubsname].bio = row['bio']
        config.participants[pubsname].badgeid = row['badgeid']

if __name__ == '__main__':
    import cmdline

    args = cmdline.cmdline(io=True, modes=False)
    read(args.infile)

    for s in config.sessions:
        print(s.index)
        print('%s %s (%s)' % (s.time.day, s.time, s.duration))
        print(s.room)
        print(s.title)
        print(s.description)
        if s.participants:
            pp = []
            for p in s.participants:
                name = p.__str__()
                if p in s.moderators:
                    name += ' (m)'
                pp.append(name)
            print(', '.join(pp))
        print('')

    for p in sorted(config.participants.values()):
        ss = []
        for s in p.sessions:
            ss.append(str(s.index))
        print('%s: %s' % (p, ', '.join(ss)))
