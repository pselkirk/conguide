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

import argparse
import re

import config
import uncsv

debug = False
nitems = []
day = {}
time = {}
duration = {}
room = {}
track = {}
type = {}
tracktype = {}
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

    if debug:
        print('%d: %s' % (i, fn))

    nitems.append(0)

    db = uncsv.read(fn, raw=True)

    for row in db:
        nitems[i] += 1
        incr(day, row['day'], i)
        incr(time, row['time'], i)
        incr(duration, row['duration'], i)
        incr(room, row['room'], i)
        incr(track, row['track'], i)
        incr(type, row['type'], i)
        incr(tracktype, (row['track'],row['type']), i)
        if not row['participants']:
            row['participants'] = '(no participants)'
        for p in row['participants'].split(','):
            p = re.sub('^ +', '', p)
            p = re.sub(' +$', '', p)
            p = re.sub(' ?\(m\)', '', p)
            incr(partic, p, i)

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true',
                    help='add debugging/trace information')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='verbose output')
parser.add_argument('files', nargs=argparse.REMAINDER,
                    help='one or more snapshots of pocketprogram.csv')
args = parser.parse_args()
debug = args.debug

if not args.files:
    count('pocketprogram.csv', 0)
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
report('room', room)
if (args.verbose):
    report('track', track)
    report('type', type)
report('track,type', tracktype)
if (args.verbose):
    report('participants', partic)
