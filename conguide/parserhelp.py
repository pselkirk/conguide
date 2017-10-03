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

"""Helper functions for argument parsers"""

import argparse

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

