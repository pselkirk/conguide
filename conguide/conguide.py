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

    # schedule
    parser_schedule = subparsers.add_parser('schedule', add_help=False,
                                            help='generate the "TV Guide" style listing')
    add_modes(parser_schedule, ['t', 'h', 'x', 'a'])
    add_io(parser_schedule)
    parser_schedule.add_argument('--no-prune', dest='prune', action='store_false',
                                 help='don\'t prune participants to save space (xml only)')
    parser_schedule.set_defaults(func=schedule.main)

    # xref
    parser_xref = subparsers.add_parser('xref', add_help=False,
                                        help='generate the program participant index')
    add_modes(parser_xref, ['t', 'h', 'x', 'a'])
    add_io(parser_xref)
    parser_xref.set_defaults(func=xref.main)

    # featured
    parser_featured = subparsers.add_parser('featured', add_help=False,
                                            help='generate the "featured event" listing')
    add_modes(parser_featured, ['t', 'h', 'x', 'a'])
    add_io(parser_featured)
    parser_featured.add_argument('--research', action='store_true',
                                 help='identify likely candidates for "featured" list')
    parser_featured.set_defaults(func=featured.main)

    # tracks
    parser_tracks = subparsers.add_parser('tracks', add_help=False,
                                          help='generate the index by track or area')
    add_modes(parser_tracks, ['t', 'h', 'x', 'a'])
    add_io(parser_tracks)
    parser_tracks.set_defaults(func=tracks.main)

    # grid
    parser_grid = subparsers.add_parser('grid', add_help=False,
                                        help='generate the daily grids')
    add_modes(parser_grid, ['h', 'x', 'i', 'a'])
    add_io(parser_grid)
    parser_grid.set_defaults(func=grid.main)

    # bios
    parser_bios = subparsers.add_parser('bios', add_help=False,
                                        help='generate the program participant bios')
    add_modes(parser_bios, ['t', 'h', 'x', 'a'])
    add_io(parser_bios)
    parser_bios.set_defaults(func=bios.main)

    # all
    parser_all = subparsers.add_parser('all', add_help=False,
                                        help='generate all reports')
    add_modes(parser_all, ['t', 'h', 'x', 'i', 'a'])
    add_io(parser_all)
    parser_all.set_defaults(func=all_reports)

    # guidebook
    parser_guidebook = subparsers.add_parser('guidebook',
                                             help='generate the csv files for Guidebook')
    parser_guidebook.add_argument('--infile', action='store',
                                  help='input file name')
    parser_guidebook.add_argument('--check', action='store_true',
                                  help='check the generated guidebook csv files')
    parser_guidebook.add_argument('-v', '--verbose', action='store_true',
                                  help='verbose output')
    parser_guidebook.set_defaults(func=guidebook.main)

    # count
    parser_count = subparsers.add_parser('count',
                                         help='count sessions, rooms, etc.')
    parser_count.add_argument('-v', '--verbose', action='store_true',
                              help='verbose output')
    parser_count.add_argument('files', nargs=argparse.REMAINDER,
                              help='one or more data snapshots')
    parser_count.set_defaults(func=count.main)

    # changes
    parser_changes = subparsers.add_parser('changes',
                                           help='compare data snapshots')
    parser_changes.add_argument('-v', '--verbose', action='store_true',
                                help='verbose output')
    parser_changes.add_argument('-s', '--sessionid', action='store_true',
                                help='print session id')
    parser_changes.add_argument('-t', '--by_title', action='store_true',
                                help='use session title instead of sessionid')
    parser_changes.add_argument('-b', '--bios', action='store_true',
                                help='compare bios files rather than schedule files')
    parser_changes.add_argument('files', nargs=argparse.REMAINDER,
                                help='one or more database files')
    parser_changes.set_defaults(func=changes.main)

    # problems
    parser_problems = subparsers.add_parser('problems',
                                            help='find common problems in the data file')
    parser_problems.add_argument('--infile', action='store',
                                 help='input file name')
    parser_problems.add_argument('--duration', action='store', default='12hr',
                                 help='what duration is "too long" (default 12hr)')
    parser_problems.set_defaults(func=problems.main)

    # backup
    parser_backup = subparsers.add_parser('backup',
                                         help='back up important files')
    parser_backup.add_argument('files', nargs=argparse.REMAINDER,
                               help='extra files to back up')
    parser_backup.set_defaults(func=backup.main)

    # parse that command line
    args = parser.parse_args()

    config.debug = args.debug
    config.quiet = args.quiet
    config.cfgfile = args.cfg

    if not hasattr(args, 'infile'):
        args.infile = None
    fn = args.infile or config.get('input files', 'schedule')
    config.source_date = time.ctime(os.path.getmtime(fn))

    # run the reports
    args.func(args)

if __name__ == '__main__':
    sys.exit(main())
