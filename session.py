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

import re

import config
import participant
import uncsv
from room import Room
from times import Day, Time, Duration

class Session:

    def __init__(self, row, participants, quiet=False, raw=False):
        'init from csv.DictReader()'
        self.sessionid = row['sessionid']
        self.day = config.day[row['day']]
        self.time = Time(row['time'])
        self.duration = Duration(row['duration'])
        try:
            self.room = config.room[row['room']]
        except KeyError:
            if not quiet:
                print('new room %s' % row['room'])
            self.room = Room(row['room'])
            config.room[self.room.name] = self.room
            config.room[self.room.index] = self.room
        try:
            for r in config.room_combo[row['room']]:
                r.sessions.append(self)
        except KeyError:
            self.room.sessions.append(self)
        self.track = row['track']
        self.type = row['type']
        self.tracktype = (row['track'], row['type'])
        self.title = row['title']
        self.description = row['description']
        self.participants = row['participants']
        if raw:
            self.participants = re.sub(r'^ ', '', self.participants)
        self.moderator = None
        if self.participants:
            # chname has to operate on the full participants string
            # because some of the target names have commas in them
            for k,v in config.chname.items():
                self.participants = self.participants.replace(k, v)
            partic = re.split(r', ?', self.participants)
            for i, p in enumerate(partic):
                (p, mod) = re.subn(r' ?\(m\)', '', p)
                if p in participants:
                    p = participants[p]
                else:
                    p = participant.Participant(p)
                    participants[p.pubsname] = p
                p.sessions.append(self)
                if mod:
                    self.moderator = p
                partic[i] = p
            self.participants = sorted(partic)
        else:
            self.participants = []

    def __lt__(self, other):
        return (other and ((self.day < other.day) or \
                           ((self.day == other.day) and \
                            ((self.time < other.time) or \
                             ((self.time == other.time) and \
                              (self.room < other.room))))))

def read(fn, quiet=False, raw=False):
    sessions = []
    participants = {}
    first = True
    for row in uncsv.read(fn, raw):
        if first:
            if row['day'] != config.day[0].shortname:
                # con doesn't start on Friday
                if config.debug:
                    print('con starts on %s rather than %s' %
                          (config.day[row['day']].name, config.day[0].name))
                # rotate the day array
                i = config.day[row['day']].index
                config.days = config.days[i:] + config.days[:i]
                for i, shortname in enumerate(config.days):
                    day = config.day[shortname]
                    day.index = i
                    config.day[i] = day
            first = False
        sessionid = row['sessionid']
        if sessionid in config.noprint:
            continue
        room = row['room']
        if not raw:
            if room in config.chroom:
                row['room'] = config.chroom[room]
            if sessionid in config.chroom:
                row['room'] = config.chroom[sessionid]
            if sessionid in config.chtitle:
                row['title'] = config.chtitle[sessionid]
            if sessionid in config.chdescr:
                row['description'] = config.chdescr[sessionid]
        s = Session(row, participants, quiet, raw)
        sessions.append(s)
    sessions = sorted(sessions)
    for i, s in enumerate(sessions, start=1):
        s.index = i
    # set a global for the number of days in the con
    Day.index = sessions[len(sessions) - 1].day.index + 1
    return (sessions, participants)

if __name__ == '__main__':
    config.parseConfig(config.CFG)
    (sessions, participants) = read(config.filenames['schedule', 'input'])

# --count
# --diff
# --titlen
# --textlen

    for s in sessions:
        print('%03d %s %s %d %s' % \
            (s.index, s.day, s.time, s.room.index, s.title))
    print(len(sessions))

    for v in sorted(participants.values()):
        if config.PY3:
            exec("print(v.pubsname, end=': ')")
            for s in v.sessions:
                exec("print(s.index, end=' ')")
            print()
        else:
            exec("print '%s: ' % v.pubsname,")
            for s in v.sessions:
                exec("print s.index,")
            print
