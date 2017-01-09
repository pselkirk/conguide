#!/usr/bin/env python

# Copyright (c) 2014-2017, Paul Selkirk
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

""" Show what rooms are in use, how many items are scheduled each day, etc.
This can be run against a single data file, or multiple data files. """

from __future__ import print_function

import argparse

import config
import session

ncolumns = 0
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
        hash[value] = [0 for j in range(ncolumns)]
        hash[value][i] = 1

def count(fn, i):

    if config.debug:
        print('%d: %s' % (i, fn))

    (sessions, participants) = session.read(fn, reset=True)

    for s in sessions:
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

def report(name, hash, limit):
    print('\n%s (%d)' % (name, len(hash)))
    for key in sorted(hash):
        while (len(hash[key]) < limit):
            hash[key].append(0)        # pad
        for val in hash[key]:
            print(val, end='\t')
        print(key)

def add_args(subparsers):
    parser = subparsers.add_parser('count',
                                   help='count sessions, rooms, etc.')
    parser.add_argument('-v', '--verbose', action='store_true',
                              help='verbose output')
    parser.add_argument('-t', '--terse', action='store_true',
                              help='terse output (only report the total)')
    parser.add_argument('files', nargs=argparse.REMAINDER,
                              help='one or more data snapshots')
    parser.set_defaults(func=main)

def main(args):
    if not args.files:
        args.files = [config.get('input files', 'schedule')]

    global ncolumns, nitems
    ncolumns = len(args.files)
    nitems = [0 for i in range(ncolumns)]

    for i, fn in enumerate(args.files):
        count(fn, i)

    for n in nitems:
        print(n, end='\t')
    print('sessions')
    if (args.terse):
        return
    limit = len(args.files)
    report('day', day, limit)
    report('time', time, limit)
    if (args.verbose):
        report('duration', duration, limit)
        report('level', level, limit)
        report('room', room, limit)
    report('level,room', levelroom, limit)
    if (args.verbose):
        report('track', track, limit)
        report('type', type, limit)
    report('track,type', tracktype, limit)
    report('tag', tag, limit)
    if (args.verbose):
        report('participants', partic, limit)
