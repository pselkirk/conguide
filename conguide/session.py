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

import re

import config
from participant import Participant
from room import Level, Room
from times import Day, Time, Duration

class Session(object):

    curday = ('', None)
    curtime = ('', None)

    def __init__(self, row, participants=None):
        self._readconfig()
        if row['room'] in Session.chroom:
            row['room'] = Session.chroom[row['room']]
        if row['sessionid'] in Session.chroom:
            row['room'] = Session.chroom[row['sessionid']]
        if row['sessionid'] in Session.chtitle:
            row['title'] = Session.chtitle[row['sessionid']]
        if row['sessionid'] in Session.chdescr:
            row['description'] = Session.chdescr[row['sessionid']]
        if row['sessionid'] in Session.chpartic:
            row['participants'] = Session.chpartic[row['sessionid']]

        self.sessionid = row['sessionid']
        try:
            self.index = int(row['index'])
        except (KeyError, TypeError):
            self.index = 0

        if row['day'] == Session.curday[0]:
            day = Session.curday[1]
        else:
            if config.debug:
                print('info: new day %s' % row['day'])
            day = Day(row['day'])
            Session.curday = (row['day'], day)
        if row['time'] == Session.curtime[0]:
            time = Session.curtime[1]
        else:
            if config.debug:
                print('info: new time %s' % row['time'])
            time = Time(row['time'], day)
            Session.curtime = (row['time'], time)
            day.time.append(time)
        self.time = time
        time.sessions.append(self)

        self.duration = Duration(row['duration'])

        try:
            level = row['level']
        except KeyError:
            level = None
        else:
            try:
                level = Level.levels[level]
            except AttributeError:
                # force Level.__init__() to read the config
                level = Level('unused')
                del Level.levels['unused']
                try:
                    level = Level.levels[row['level']]
                except KeyError:
                    if not config.quiet:
                        print('warning: new level %s' % row['level'])
                    level = Level(row['level'])
                    Level.levels[level.name] = level
                    Level.levels[level.name] = level
            except KeyError:
                if not config.quiet:
                    print('warning: new level %s' % row['level'])
                level = Level(row['level'])
                Level.levels[level.name] = level
                Level.levels[level.name] = level

        try:
            room = Room.rooms[row['room']]
        except AttributeError:
            # force Room.__init__() to read the config
            room = Room('unused')
            del Room.rooms['unused']
            try:
                room = Room.rooms[row['room']]
            except KeyError:
                if not config.quiet:
                    print('warning: new room %s' % row['room'])
                room = Room(row['room'])
                room.level = level
                Room.rooms[room.name] = room
                Room.rooms[room.index] = room
        except KeyError:
            if not config.quiet:
                print('warning: new room %s' % row['room'])
            room = Room(row['room'])
            room.level = level
            Room.rooms[room.name] = room
            Room.rooms[room.index] = room
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
                p = participants[name]
            except KeyError:
                if config.debug:
                    print('info: new participant %s' % name)
                p = Participant(name)
                participants[name] = p
            self.participants.append(p)
            p.sessions.append(self)
        # XXX local policy
        #self.participants = sorted(self.participants)

        self.moderators = []
        for name in row['moderators']:
            p = participants[name]
            self.moderators.append(p)

    def _readconfig(self):
        Session._readconfig = lambda x: None
        Session.chroom = {}
        try:
            for name, rename in config.items('session change room'):
                Session.chroom[name] = rename
        except config.NoSectionError:
            pass
        Session.chtitle = {}
        try:
            for sessionid, rename in config.items('session change title'):
                Session.chtitle[sessionid] = rename
        except config.NoSectionError:
            pass
        Session.chdescr = {}
        try:
            for sessionid, rename in config.items('session change description'):
                Session.chdescr[sessionid] = rename
        except config.NoSectionError:
            pass
        Session.chpartic = {}
        try:
            for sessionid, rename in config.items('session change participants'):
                Session.chpartic[sessionid] = re.split(r', ?', rename)
        except config.NoSectionError:
            pass
        Session.noprint = {}
        try:
            for (sessionid, unused) in config.items('session do not print'):
                Session.noprint[sessionid] = True
        except config.NoSectionError:
            pass

    def __lt__(self, other):
        return (other and \
                ((self.time.day < other.time.day) or \
                 ((self.time.day == other.time.day) and \
                  ((self.time < other.time) or \
                   ((self.time == other.time) and \
                    (((not self.index or not other.index) and \
                      (self.room < other.room)) or \
                     (self.index < other.index)))))))

def read(fn, reset=False):
    # Read [participant change name] here because we want to check the
    # chname dict before instantiating the first participant, or even the
    # first session.
    Participant.chname = {}
    try:
        for name, rename in config.items('participant change name'):
            Participant.chname[name] = rename
    except config.NoSectionError:
        pass

    import importlib
    value = config.get('input file importer', 'reader')
    try:
        filereader = importlib.import_module(value)
    except ImportError:
        filereader = importlib.import_module('conguide.' + value)
    if reset:
        filereader.sessions = []
        filereader.participants = {}
    return filereader.read(fn)
