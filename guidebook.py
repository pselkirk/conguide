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

""" Generate 3 inter-related csv files for Guidebook. """

import argparse
import codecs
import csv
import re
import time

import config
import featured
import participant
import session
from times import Day

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-?', '--help', action='help',
                    help='show this help message and exit')
parser.add_argument('-c', '--config', dest='cfg', default=config.CFG,
                    help='config file (default "%s")' % config.CFG)
parser.add_argument('-d', '--debug', action='store_true',
                    help='add debugging/trace information')
parser.add_argument('-q', '--quiet', action='store_true',
                    help='suppress warning messages')
parser.add_argument('--infile', action='store',
                    help='input file name')
args = parser.parse_args()
config.debug = args.debug
config.quiet = args.quiet
config.cfgfile = args.cfg
if args.infile:
    config.set('input files', 'schedule', args.infile)

(sessions, participants) = session.read(config.get('input files', 'schedule'))
participant.read(config.get('input files', 'bios'), participants)

sched = open('guidebook.csv', 'w')
schedwriter = csv.writer(sched)
schedwriter.writerow(['Session Title',
                      'Date (4/21/2011)',
                      'Time Start',
                      'Time End',
                      'Room/Location',
                      'Schedule Track (Optional)',
                      'Description (Optional)'])

links = open('guidebook-links.csv', 'wb')
linkswriter = csv.writer(links)
linkswriter.writerow(['Item ID (Optional)',
                      'Item Name (Optional)',
                      'Link To Session ID (Optional)',
                      'Link To Session Name (Optional)',
                      'Link To Item ID (Optional)',
                      'Link To Item Name (Optional)'])

bios = open('guidebook-bios.csv', 'w')
bioswriter = csv.writer(bios)
bioswriter.writerow(['Name',
                     'Location (i.e. Table/Booth or Room Numbers)',
                     'Description (Optional)'])

# read configuration
start = time.strptime(config.get('convention', 'start'), '%Y-%m-%d')
# time.struct_time(tm_year=2014, tm_mon=1, tm_mday=17, tm_hour=0,
# tm_min=0, tm_sec=0, tm_wday=4, tm_yday=17, tm_isdst=-1)
tracks = []
try:
    for area, expr in config.items('tracks classifier'):
        expr = expr.replace('track', 'session.track')
        expr = expr.replace('type', 'session.type')
        expr = re.sub(r'room == (\'\w+\')',
                      r'session.room == Room.rooms[\1]', expr)
        area = area.replace(' - ', u'\u2014')
        tracks.append((area, expr))
except config.NoSectionError:
    pass
featured = []
try:
    for (sessionid, unused) in config.items('featured sessions'):
        featured.append(sessionid)
except config.NoSectionError:
    pass

for i, day in enumerate(Day.days):
    # XXX breaks if con spans the end of a month
    day.date = '%02d/%02d/%04d' % (start.tm_mon, start.tm_mday + i, start.tm_year)

titles = {}
for session in sessions:
    begin = re.sub('([AP]M)', r' \1'.upper(), str(session.time).upper())
    end = re.sub('([AP]M)', r' \1',
                 str(session.time + session.duration).upper())

    track = session.track
    for t, expr in tracks:
        if eval(expr):
            track = t
            break
    if session.sessionid in featured:
        track += '; Featured Events'

    if session.title in titles:
        titles[session.title] += 1
        title = '%s (%d)' % (session.title, titles[session.title])
    else:
        titles[session.title] = 1
        title = session.title

    def writerow(writer, row):
        writer.writerow([codecs.encode(f, 'utf-8') for f in row])

    writerow(schedwriter, [title, session.time.day.date, begin, end,
                           str(session.room), track, session.description])

    for p in session.participants:
        writerow(linkswriter, ['', p.name, '', title, '', ''])

for p in sorted(participants.values()):
    try:
        bio = p.bio
    except AttributeError:
        bio = ''
    writerow(bioswriter, [p.name, '', bio])

sched.close()
links.close()
bios.close()
