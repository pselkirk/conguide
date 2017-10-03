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

""" Find repeated sessions. Output is formatted for arisia.cfg. """

import argparse

from . import config, session

title = {}
descr = {}
dup_t = {}
dup_d = {}

debug = False
verbose = False

def add_args(subparsers):
    parser = subparsers.add_parser('dup',
                                   help='find duplicate sessions')
    parser.add_argument('--infile', action='store',
                        help='input file name')
    parser.add_argument('--description-length', '--len', action='store', dest='length', default=1, type=int,
                        help='ignore description shorter than this (default 1)')
    parser.set_defaults(func=main)

def main(args):
    fn = args.infile or config.get('input files', 'schedule')
    (sessions, participants) = session.read(fn)
    
    for s in sessions:
        if len(s.description) >= args.length:

            if s.title in title:
                dup_t[s] = title[s.title]
            else:
                title[s.title] = s

            if s.description in descr:
                dup_d[s] = descr[s.description]
            else:
                descr[s.description] = s

    if dup_t:
        print('# by title')
        for s in sorted(dup_t):
            print('%s = %s\t# %s (%d)' % (s.sessionid, title[s.title].sessionid, s.title, len(s.description)))

    if dup_d:
        print('# by description')
        for s in sorted(dup_d):
            print('%s = %s\t# %s (%d)' % (s.sessionid, descr[s.description].sessionid, s.title, len(s.description)))
