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

import argparse

import config
from participant import Participant
import session
import times

nitems = []
day = {}
time = {}
duration = {}
level = {}
room = {}
levelroom = {}
track = {}
type = {}
tracktype = {}
tag = {}
partic = {}

def incr(hash, value, i):
    try:
        hash[value][i] += 1
    except KeyError:
        hash[value] = [0 for i in range(i+1)]
        hash[value][i] = 1
    except IndexError:
        hash[value].append(1)

def count(fn, i):

    if config.debug:
        print('%d: %s' % (i, fn))

    nitems.append(0)

    session.read(fn)

    for s in session.Session.sessions:
        nitems[i] += 1
        incr(day, str(s.time.day), i)
        incr(time, str(s.time), i)
        incr(duration, str(s.duration), i)
        incr(level, str(s.room.level), i)
        incr(room, str(s.room), i)
        incr(levelroom, (str(s.room.level), str(s.room)), i)
        incr(track, str(s.track), i)
        incr(type, str(s.type), i)
        incr(tracktype, (str(s.track), str(s.type)), i)
        if not s.participants:
            incr(partic, '(no participants)', i)
        else:
            for p in s.participants:
                incr(partic, p.__str__(), i)
        if not s.tags:
            incr(tag, '(no tags)', i)
        else:
            for t in s.tags:
                incr(tag, t, i)

    # reinitialize for the next count
    session.Session.sessions = []
    Participant.participants = {}

parser = argparse.ArgumentParser()
parser.add_argument('-c', '--config', dest='cfg', default=config.CFG,
                    help='config file (default "%s")' % config.CFG)
parser.add_argument('-d', '--debug', action='store_true',
                    help='add debugging/trace information')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='don\t print warning messages')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='verbose output')
parser.add_argument('files', nargs=argparse.REMAINDER,
                    help='one or more snapshots of pocketprogram.csv')
args = parser.parse_args()
config.debug = args.debug
config.quiet = args.quiet
config.cfgfile = args.cfg
verbose = args.verbose

if not args.files:
    count(config.get('input files', 'schedule'), 0)
else:
    for i, fn in enumerate(args.files):
        count(fn, i)

def report(name, hash):
    print('\n%s (%d)' % (name, len(hash)))
    for key in sorted(hash):
        while (len(hash[key]) < len(args.files)):
            hash[key].append(0)
        for val in hash[key]:
            if config.PY3:
                exec("print(val, end='\t')")
            else:
                exec("print '%d\t' % val,")
        print(key)

for n in nitems:
    if config.PY3:
        exec("print(n, end='\t')")
    else:
        exec("print '%d\t' % n,")
print('program items')
report('day', day)
report('time', time)
if (args.verbose):
    report('duration', duration)
report('level', level)
report('room', room)
report('level,room', levelroom)
if (args.verbose):
    report('track', track)
    report('type', type)
report('track,type', tracktype)
report('tag', tag)
if (args.verbose):
    report('participants', partic)
