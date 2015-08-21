#!/usr/bin/env python

""" find overnight sessions (entirely within 'late night' slices) """
# fold this into grid.py eventually

import re

import cmdline
import config
import session
from times import Day, Time

overnight = {}
day = None
t24 = Time('24:00')

args = cmdline.cmdline()
session.read(config.get('input files', 'schedule'))

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
                                for s in time.session:
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
