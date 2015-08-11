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

import config
from participant import Participant
from room import Level, Room
from times import Day, Time, Duration

class Session(object):

    def __init__(self, row):
        'init from csv.DictReader()'

        if row['room'] in config.chroom:
            row['room'] = config.chroom[row['room']]
        if row['sessionid'] in config.chroom:
            row['room'] = config.chroom[row['sessionid']]
        if row['sessionid'] in config.chtitle:
            row['title'] = config.chtitle[row['sessionid']]
        if row['sessionid'] in config.chdescr:
            row['description'] = config.chdescr[row['sessionid']]

        self.sessionid = row['sessionid']
        try:
            self.index = int(row['index'])
        except (KeyError, TypeError):
            self.index = 0

        try:
            day = config.days[row['day']]
        except KeyError:
            if config.debug:
                print('info: new day %s' % row['day'])
            day = Day(row['day'])
            config.days[row['day']] = day
        try:
            time = day.time[row['time']]
        except KeyError:
            if config.debug:
                print('info: new time %s %s' % (row['day'], row['time']))
            time = Time(row['time'], day)
            day.time[row['time']] = time
        self.time = time
        time.session.append(self)

        self.duration = Duration(row['duration'])

        try:
            level = config.levels[row['level']]
        except KeyError:
            try:
                if not config.quiet:
                    print('warning: new level %s' % row['level'])
                level = Level(row['level'])
                config.levels[level.name] = level
                config.levels[level.name] = level
            except KeyError:
                level = None

        try:
            room = config.rooms[row['room']]
        except KeyError:
            if not config.quiet:
                print('warning: new room %s' % row['room'])
            room = Room(row['room'])
            room.level = level
            config.rooms[room.name] = room
            config.rooms[room.index] = room
        self.room = room
        room.sessions.append(self)

        self.tracks = row['tracks']
        try:
            self.track = self.tracks[0]
        except IndexError:
            self.track = None

        self.type = row['type']
        self.tags = row['tags']
        self.title = row['title']
        self.description = row['description']

        self.participants = []
        for name in row['participants']:
            try:
                p = config.participants[name]
            except KeyError:
                if config.debug:
                    print('info: new participant %s' % name)
                p = Participant(name)
                config.participants[name] = p
            self.participants.append(p)
            p.sessions.append(self)
        #self.participants = sorted(self.participants)

        self.moderators = []
        for name in row['moderators']:
            p = config.participants[name]
            self.moderators.append(p)

    def __lt__(self, other):
        return (other and \
                ((self.time.day < other.time.day) or \
                 ((self.time.day == other.time.day) and \
                  ((self.time < other.time) or \
                   ((self.time == other.time) and \
                    (((not self.index or not other.index) and \
                      (self.room < other.room)) or \
                     (self.index < other.index)))))))

