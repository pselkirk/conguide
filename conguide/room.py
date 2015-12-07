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

class Level(object):
    index = 0

    def __init__(self, name):
        self._readconfig()
        self.index = Level.index
        Level.index += 1
        self.name = name
        self.pubsname = name
        self.rooms = []

        Level.levels[name] = self

    def _readconfig(self):
        Level._readconfig = lambda x: None
        Level.levels = {}
        Room.rooms = {}
        for section in config.sections():
            m = re.match(r'(level|venue) (.*)', section)
            if m:
                name = m.group(2)
                #Level.levels[name] = Level(name)
                l = Level(name)
                try:
                    #Level.levels[name].pubsname = config.get(section, 'pubsname')
                    l.pubsname = config.get(section, 'pubsname')
                except config.NoOptionError:
                    pass
                rooms = config.get(section, 'rooms')
                for rname in re.split(r',\s*', rooms):
                    #Room.rooms[rname] = Room(rname, Level.levels[name])
                    #Level.levels[name].rooms.append(Room.rooms[rname])
                    r = Room(rname, l)
                    l.rooms.append(r)

            m = re.match(r'room (.*)', section)
            if m:
                name = m.group(1)
                try:
                    Room.rooms[name].pubsname = config.get(section, 'pubsname')
                except config.NoOptionError:
                    pass
                try:
                    Room.rooms[name].usage = config.get(section, 'usage')
                except config.NoOptionError:
                    pass
                try:
                    rooms = re.split(r',\s*', config.get(section, 'grid room'))
                    for i, r in enumerate(rooms):
                        # change room name to Room instance
                        rooms[i] = Room.rooms[r]
                    Room.rooms[name].gridrooms = rooms
                except config.NoOptionError:
                    pass

    def __lt__(self, other):
        return (other and (self.index < other.index))

    def __str__(self):
        return self.pubsname

# This inherits from Level purely to get access to _readconfig(),
# so we can read the configuration from either class.
class Room(Level):
    index = 0

    def __init__(self, name, level=None):
        self._readconfig()
        self.index = Room.index
        Room.index += 1
        self.level = level
        self.name = name
        self.pubsname = name
        self.usage = None
        self.sessions = []
        Room.rooms[name] = self

    def __lt__(self, other):
        return (other and (self.index < other.index))

    def __str__(self):
        return self.pubsname

if __name__ == '__main__':
    import cmdline

    args = cmdline.cmdline(io=True, modes=False)

    # force reading of config
    r = Room('unused')
    del Room.rooms['unused']

    for r in sorted(Room.rooms.values()):
        print('%s: %s' % (r.name, r.level))
    print('')
    for l in sorted(Level.levels.values()):
        print(l.name)
        for r in sorted(l.rooms):
            print('\t' + r.name)
