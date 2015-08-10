#!/usr/bin/env python

# Copyright (c) 2014, Paul Selkirk
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

""" Back up important files. """

import argparse
import os, os.path
import time

# *.csv are input data files from zambia
# Schedule-with-changes.html is a generated file with a link to the previous
backups = [ 'pocketprogram.csv', 'PubBio.csv', 'Schedule-with-changes.html' ]

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true',
                    help='debug/dry run')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='quiet output')
parser.add_argument('files', nargs=argparse.REMAINDER,
                    help='extra files to back up')
args = parser.parse_args()
debug = args.debug
quiet = args.quiet and not args.debug

for fn in backups + args.files:
    if os.path.exists(fn):
        # get the date portion of the file timestamp
        # e.g. pocketprogram.csv -> pocketprogram.2014-01-14.csv
        fdate = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(fn)))
        (name, ext) = os.path.splitext(fn)
        bn = name + '.' + fdate + ext
        if os.path.exists(bn):
            # rename the older backup, so it will be before the new one in
            # a directory listing
            # (use '-' because windows can't handle ':' in file name)
            # e.g. pocketprogram.2014-01-14.csv -> pocketprogram.2014-01-14.17-58-46.csv
            ftime = time.strftime('%H-%M-%S', time.localtime(os.path.getmtime(bn)))
            bbn = name + '.' + fdate + '.' + ftime + ext
            if not quiet:
                print('%s -> %s' % (bn, bbn))
            if not debug:
                os.rename(bn, bbn)
        if not quiet:
            print('%s -> %s' % (fn, bn))
        if not debug:
            os.rename(fn, bn)
