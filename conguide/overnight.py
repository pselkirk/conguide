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

""" Find overnight sessions (entirely within 'Late Night' slices). """

import argparse
import sys

from . import config, session
from .times import Day, Time

def add_args(subparsers):
    parser = subparsers.add_parser('overnight',
                                   help='find overnight sessions')
    parser.add_argument('--infile', action='store',
                        help='input file name')
    parser.add_argument('--start', action='store',
                        help='start time')
    parser.add_argument('--end', action='store',
                        help='end time')
    parser.set_defaults(func=main)

def main(args):
    cfg_start = cfg_end = None
    try:
        for section in config.sections():
            if section.startswith('grid slice indesign'):
                if config.get(section, 'name') == 'Late Night':
                    cfg_start = config.get(section, 'start')
                    cfg_end = config.get(section, 'end')
                    break
    except AttributeError:
        pass
    if not args.start:
        args.start = cfg_start
    if not args.end:
        args.end = cfg_end
    if not args.start or not args.end:
        print('error: Late Night slice not found in config, and start and/or end not specified on command line')
        exit(1)

    fn = args.infile or config.get('input files', 'schedule')
    (sessions, participants) = session.read(fn)
    
    day = None
    start = Time(args.start)
    end = Time(args.end)
    t24 = Time('24:00')
    if start >= t24:
        start -= t24
        end -= t24

    for i, day in enumerate(Day.days):
        overnight = {}
        for time in day.time:
            if time >= start and time < end:
                for s in time.sessions:
                    if time + s.duration < end:
                        try:
                            overnight[s.room].append(s)
                        except KeyError:
                            overnight[s.room] = [s]
                        if not s.room.usage:
                            s.room.usage = '%s/%s' % (s.track, s.type)
        if overnight:
            print(Day.days[i-1])
            for room in sorted(overnight):
                print('Overnight %s (%s)' % (room.usage, room.name))
                for s in overnight[room]:
                    print('%s %s' % (s.time, s.title))
                print('')
            print('')
