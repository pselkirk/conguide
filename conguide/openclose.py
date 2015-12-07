#!/usr/bin/env python

""" report opening and closing times for fixed functions """

# This is all specific to Sasquan, where they have program items like Art
# Show Opens and Art Show Closes. For the most part, the Open item has the
# duration of the function, but a couple are off by 5 minutes, and all the
# Children's Program items are 15 minutes.
#
# Anyway, I suppress these items in the main body of the grid, but I want
# to gather them into a small list to put in an inset box in the grid.

import argparse
import re

import cmdline
import config
import session
from times import Day, Duration

parent = cmdline.cmdlineParser(modes=False)
parser = argparse.ArgumentParser(add_help=False, parents=[parent])
parser.add_argument('--raw', action='store_true',
                    help='print raw opening and closing entries')
args = cmdline.cmdline(parser, modes=False)
session.read(config.get('input files', 'schedule'))

exprs = []
try:
    expr = config.get('grid no print', 'title starts with')
    exprs.append('session.title.startswith((%s))' % expr)
except (config.NoSectionError, config.NoOptionError):
    pass
try:
    expr = config.get('grid no print', 'title ends with')
    exprs.append('session.title.endswith((%s))' % expr)
except (config.NoSectionError, config.NoOptionError):
    pass
noprint = ' or '.join(exprs)

for day in Day.days:
    print(day)
    openclose = []
    for time in day.time:
        for session in time.session:
            # [grid no print]
            # title ends with = 'Open', 'Opens', 'Close', 'Closes', 'Lunch', 'Dinner'
            if noprint and eval(noprint):
                if args.raw:
                    print('%s %s (%s)' % (session.title, session.time, session.duration))
                else:
                    m = re.search(r'(.*?) ?Open', session.title)
                    if m:
                        title = m.group(1)
                        title = re.sub(' Re-$', '', title)
                        session.shorttitle = title
                        openclose.append(session)
                    else:
                        m = re.match(r'(\S+ )', session.title)
                        i = len(openclose) - 1
                        while i >= 0:
                            open = openclose[i]
                            if open.title.startswith(m.group(1)):
                                end = open.time + open.duration
                                if end != session.time:
                                    t = session.time - open.time
                                    duration = Duration(t.__str__(mode='24hr'))
                                    if not config.quiet:
                                        print('warning: %s duration (%s) does not match %s (%s = %d min)' % (open.title, open.duration, session.title, duration, duration.hour * 60 + duration.minute))
                                    openclose[i].duration = duration
                                break
                            i -= 1
                        if i < 0:
                            if not config.quiet:
                                print('warning: %s: matching Open not found' % session.title)

    for session in openclose:
        print(u'%s: %s\u2013%s' % (session.shorttitle, str(session.time), str(session.time + session.duration)))

    print('')
