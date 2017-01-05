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

""" Find common problems in pocketprogram.csv. """

import argparse
import re

import config
import session
from times import Duration

def add_args(subparsers):
    parser = subparsers.add_parser('problems',
                                   help='find common problems in the data file')
    parser.add_argument('--infile', action='store',
                        help='input file name')
    parser.add_argument('--long-duration', action='store', dest='duration', default='12hr',
                        help='what duration is "too long" (default 12hr)')
    parser.add_argument('--short-description', type=int, action='store', dest='short', default=40,
                        help = 'what description length is too short (default 40)')
    parser.set_defaults(func=main)

def main(args):
    fn = args.infile or config.get('input files', 'schedule')
    (sessions, participants) = session.read(fn)
    
    def check(text, func, duration=False):
        found = False
        for s in sessions:
            if func(s):
                if not found:
                    print(text)
                    found = True
                if duration:
                    print('%4s %s (%s)' % (s.sessionid, s.title, s.duration))
                else:
                    print('%4s %s' % (s.sessionid, s.title))
        if found:
            print('')
    
    def lower(s):
        for w in s.title.split(' '):
            if w.islower() and len(w) > 3 and not re.search(r'\d', w) and \
               w != 'with' and w != 'from' and w != 'into':
                return True
        return False
    
    def upper(s):
        for w in s.title.split(' '):
            if w.isupper() and len(w) > 3 and not re.search(r'\d', w) and \
               w != 'SF/F' and w != 'LARP' and w != 'RPG' and w != 'BDSM' and w != 'D&D':
                return True
        return False
    
    check('room "Other"', lambda s: s.room.name == 'Other')
    #check('bogus m-dash', lambda s: re.search(r'\S-\s', s.title))
    check('lowercase words in title', lower)
    check('uppercase words in title', upper)
    check('day in title', lambda s: re.search(r'\wday', s.title))
    check('[bracket text] in title', lambda s: re.search(r'[\[\]]', s.title))
    check('no description', lambda s: not s.description)
    check('short description (%d)' % args.short, lambda s: len(s.description) > 0 and len(s.description) < args.short)
    check('[bracket text] in description', lambda s: re.search(r'[\[\]]', s.description))
    check('no period at end of description', lambda s: (s.participants and re.search(r'\w$', s.description)))
    check('no duration', lambda s: s.duration == Duration('0'))
    check('negative duration', lambda s: s.duration < Duration('0'))
    check('long duration (%s)' % args.duration, lambda s: s.duration >= Duration(args.duration), duration=True)
