#!/usr/bin/env python

""" find overnight sessions (entirely within 'late night' slices) """
# fold this into grid.py eventually

import argparse
import re

import config
import session
from times import Day, Time

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-?', '--help', action='help',
                    help='show this help message and exit')
parser.add_argument('-c', '--config', dest='cfg', default=config.CFG,
                    help='config file (default "%s")' % config.CFG)
parser.add_argument('-q', '--quiet', action='store_true',
                    help='suppress warning messages')
parser.add_argument('-h', '--html', action='store_true',
                    help='html output')
parser.add_argument('-x', '--xml', action='store_true',
                    help='InDesign xml output')
parser.add_argument('-i', '--indesign', action='store_true',
                    help='InDesign tagged text output')
parser.add_argument('--infile', action='store',
                    help='input file name')
args = parser.parse_args()
config.cfgfile = args.cfg
config.quiet = args.quiet
if args.html + args.xml + args.indesign != 1:
    print('error: exactly one output mode must be specified\n')
    parser.print_help()
    exit(1)

session.read(args.infile or config.get('input files', 'schedule'))

overnight = {}
day = None
t24 = Time('24:00')

for mode in ('html', 'xml', 'indesign'):
    if eval('args.' + mode):
        for section in config.sections():
            if re.match('grid slice ' + mode, section):
                name = config.get(section, 'name')
                if name == 'Late Night':
                    start = Time(config.get(section, 'start'))
                    end = Time(config.get(section, 'end'))
                    if start >= t24:
                        start -= t24
                        end -= t24
                    for i, day in enumerate(Day.days):
                        overnight = {}
                        for time in day.time:
                            if time >= start and time < end:
                                for s in time.sessions:
                                    if time + s.duration < end:
                                        try:
                                            overnight[s.room].append(s)
                                        except KeyError:
                                            overnight[s.room] = [s]
                                        if not s.room.usage:
                                            s.room.usage = s.type.capitalize()
                        if overnight:
                            print(Day.days[i-1])
                            for room in sorted(overnight):
                                print('Overnight %s (%s)' % (room.usage, room.name))
                                for s in overnight[room]:
                                    print('%s %s' % (s.time, s.title))
                                print('')
                            print('')
                    exit(0)
