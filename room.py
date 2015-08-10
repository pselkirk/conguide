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

class Level:
    index = 0

    def __init__(self, name, rooms=None):
        self.index = Level.index
        Level.index += 1
        self.name = name
        self.pubsname = name
        self.rooms = rooms

    def __lt__(self, other):
        return (other and (self.index < other.index))

    def __str__(self):
        return self.pubsname

class Room:
    index = 0

    def __init__(self, name, level=None):
        self.index = Room.index
        Room.index += 1
        self.level = level
        self.name = name
        self.pubsname = name
        self.usage = None
        self.sessions = []

    def __lt__(self, other):
        return (other and (self.index < other.index))

    def __str__(self):
        return self.pubsname

if __name__ == '__main__':
    import sys
    import config

    try:
        config.parseConfig(sys.argv[1])
    except IndexError:
        config.parseConfig(config.CFG)

    for r in config.room:
        print('%s\t%s' % (r, config.room[r]))
