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

"""A front-end driver module to generate Convention Guide content.

| usage: conguide.py [-?] [-c CFG] [-d] [-q] [-t] [-h] [-x] [-i] [-a]
| 
| optional arguments:
|   -?, --help            show this help message and exit
|   -c CFG, --config CFG  config file (default "arisia.cfg")
|   -d, --debug           add debugging/trace information
|   -q, --quiet           suppress warning messages
|   -t, --text            text output
|   -h, --html            html output
|   -x, --xml             InDesign xml output
|   -i, --indesign        InDesign tagged text output
|   -a, --all             all output modes

Depending on configuration, this generates schedule, program participant
cross-reference (xref), featured sessions, and track list.

"""

import argparse
import codecs
import os
import sys
import time

import config
import bios
import featured
import grid
import output
import participant
import schedule
import session
import tracks
import xref
import guidebook
import count
import changes
import problems
import backup
from __init__ import __prog__, __version__

# search the working directory for [input file importer]
sys.path[0:0] = '.'

def all_reports(args):
    # generate all reports
    schedule.main(args)
    xref.main(args)
    featured.main(args)
    tracks.main(args)
    grid.main(args)
    bios.main(args)
    if args.xml:
        try:
            f = codecs.open(config.get('output files xml', 'conguide'),
                            'w', 'utf-8', 'replace')
        except KeyError:
            pass
        else:
            (sessions, participants) = session.read(config.get('input files', 'schedule'))
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<conguide>\n')
            schedule.write(schedule.XmlOutput(None, f), sessions)
            featured.write(featured.XmlOutput(None, f), sessions)
            tracks.write(tracks.XmlOutput(None, f), sessions)
            xref.write(xref.XmlOutput(None, f), participants)
            f.write('</conguide>\n')
            f.close()

def add_modes(parser, modes):
    if 'h' in modes:
        parser.add_argument('-?', '--help', action='help',
                            help='show this help message and exit')
    for mode in modes:
        if mode == 't':
            parser.add_argument('-t', '--text', action='store_true',
                        help='text output')
        elif mode == 'h':
            parser.add_argument('-h', '--html', action='store_true',
                                help='html output')
        elif mode == 'x':
            parser.add_argument('-x', '--xml', action='store_true',
                                help='InDesign xml output')
        elif mode == 'i':
            parser.add_argument('-i', '--indesign', action='store_true',
                                help='InDesign tagged text output')
        elif mode == 'a':
            parser.add_argument('-a', '--all', action='store_true',
                                help='all output modes')

def add_io(parser):
    parser.add_argument('--infile', action='store',
                        help='input file name')
    parser.add_argument('--outfile', action='store',
                        help='output file name')

def main():
    # command line
    parser = argparse.ArgumentParser(add_help=False, prog=__prog__)
    parser.set_defaults(func=all_reports)
    subparsers = parser.add_subparsers()

    # global options
    parser.add_argument('-?', '--help', action='help',
                        help='show this help message and exit')
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument('-c', '--config', dest='cfg', default=config.CFG,
                        help='config file (default "%s")' % config.CFG)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='add debugging/trace information')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='suppress warning messages')
 
    # subcommand-specific options
    schedule.add_args(subparsers)
    xref.add_args(subparsers)
    featured.add_args(subparsers)
    tracks.add_args(subparsers)
    grid.add_args(subparsers)
    bios.add_args(subparsers)

    # all of the previous reports at once
    parser_all = subparsers.add_parser('all', add_help=False,
                                        help='generate all reports')
    add_modes(parser_all, ['t', 'h', 'x', 'i', 'a'])
    add_io(parser_all)
    parser_all.set_defaults(func=all_reports)

    # more subcommands
    guidebook.add_args(subparsers)
    count.add_args(subparsers)
    changes.add_args(subparsers)
    problems.add_args(subparsers)
    backup.add_args(subparsers)

    # parse that command line
    args = parser.parse_args()

    config.debug = args.debug
    config.quiet = args.quiet
    config.cfgfile = args.cfg

    try:
        fn = args.infile or config.get('input files', 'schedule')
    except AttributeError:
        fn = config.get('input files', 'schedule')
    config.source_date = time.ctime(os.path.getmtime(fn))

    # run the subcommand
    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
