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

""" Process command line options, and read the input files. """

import argparse
import os.path, time

import config

# To call without adding command line options, do this:
#    (args, sessions, participants) = cmdline.cmdline()
#
# To call with additional options, do something like this:
#    parent = cmdline.cmdlineParser()
#    parser = argparse.ArgumentParser(add_help=False, parents=[parent])
#    parser.add_argument('-f', '--frob', action='store_true',
#                        help='frobnicate the output')
#    (args, sessions, participants) = cmdline.cmdline(parser)

def cmdlineParser(io=False, modes=True):

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-?', '--help', action='help',
                        help='show this help message and exit')
    parser.add_argument('-c', '--config', dest='cfg', default=config.CFG,
                        help='config file (default "%s")' % config.CFG)
    parser.add_argument('-d', '--debug', action='store_true',
                        help='add debugging/trace information')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='suppress warning messages')
    if modes:
        parser.add_argument('-t', '--text', action='store_true',
                            help='text output')
        parser.add_argument('-h', '--html', action='store_true',
                            help='html output')
        parser.add_argument('-x', '--xml', action='store_true',
                            help='InDesign xml output')
        parser.add_argument('-i', '--indesign', action='store_true',
                            help='InDesign tagged text output')
        parser.add_argument('-a', '--all', action='store_true',
                            help='all output modes')
    if io:
        parser.add_argument('--infile', action='store',
                            help='input file name')
        parser.add_argument('--outfile', action='store',
                            help='output file name')
    return parser

def cmdline(parser=None, io=False, modes=True):

    if not parser:
        parser = cmdlineParser(io, modes)

    args = parser.parse_args()
    config.debug = args.debug
    config.quiet = args.quiet
    config.cfgfile = args.cfg

    if modes:
        if args.all:
            args.text = True
            args.html = True
            args.xml = True
            args.indesign = True
        elif not (args.text or args.html or args.xml or args.indesign):
            print('error: at least one output mode must be specified\n')
            parser.print_help()
            exit(1)

        if io and args.outfile and \
           (args.text + args.html + args.xml + args.indesign > 1):
            print('error: --outfile requires exactly one output mode\n')
            parser.print_help()
            exit(1)

    if io:
        if args.infile:
            config.set('input files', 'schedule', args.infile)
        else:
            args.infile = config.get('input files', 'schedule')

    config.source_date = time.ctime(os.path.getmtime(config.get('input files', 'schedule')))

    return args

if __name__ == '__main__':
    args = cmdline(io=True)
    print(args)
