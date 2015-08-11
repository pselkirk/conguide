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

import codecs
import csv
import re

import cfgparse
import config
import session

cfgparse.parseConfig(config.CFG)
config.filereader.read(config.filenames['schedule', 'input'])
config.filereader.read_bios(config.filenames['bios', 'input'])

sched = open('guidebook.csv', 'w')
schedwriter = csv.writer(sched)
schedwriter.writerow(['Session Title', 'Date (4/21/2011)',
                      'Time Start', 'Time End', 'Room/Location',
                      'Schedule Track (Optional)', 'Description (Optional)'])

links = open('guidebook-links.csv', 'wb')
linkswriter = csv.writer(links)
linkswriter.writerow(['Item ID (Optional)', 'Item Name (Optional)',
                      'Link To Session ID (Optional)',
                      'Link To Session Name (Optional)',
                      'Link To Item ID (Optional)',
                      'Link To Item Name (Optional)'])

bios = open('guidebook-bios.csv', 'w')
bioswriter = csv.writer(bios)
bioswriter.writerow(['Name', 'Location (i.e. Table/Booth or Room Numbers)',
                     'Description (Optional)'])

for i, day in enumerate(config.day):
    # XXX breaks if con spans the end of a month
    day.date = '%02d/%02d/%04d' % \
               (config.start.tm_mon,
                config.start.tm_mday + i,
                config.start.tm_year)

titles = {}
for session in config.sessions:
    begin = re.sub('([AP]M)', r' \1'.upper(), str(session.time).upper())
    end = re.sub('([AP]M)', r' \1',
                 str(session.time + session.duration).upper())

    track = session.track
    for t, expr in config.tracks:
        if eval(expr):
            track = t
            break
    if session.sessionid in config.featured:
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

for p in sorted(config.participants.values()):
    try:
        bio = p.bio
    except AttributeError:
        bio = ''
    writerow(bioswriter, [p.name, '', bio])

sched.close()
links.close()
bios.close()
