#!/usr/bin/env python

""" find overnight sessions (entirely within 'late night' slices) """
# fold this into grid.py eventually

import cmdline
import config
import times

overnight = {}
day = None
t24 = times.Time('24:00')

args = cmdline.cmdline()
config.filereader.read(config.filenames['schedule', 'input'])

for mode in ('html', 'xml', 'indesign'):
    if eval('args.' + mode):
        for slice in config.slice[mode]:
            if slice.name == 'Late Night':
                if slice.start >= t24:
                    slice.start -= t24
                    slice.end -= t24
                for i in range(Day.index):
                    day = Day.days[i]
                    print(day)
                    overnight = {}
                    for time in day.time:
                        if time >= slice.start and time < slice.end:
                            for s in time.session:
                                if time + s.duration < slice.end:
                                    try:
                                        overnight[s.room].append(s)
                                    except KeyError:
                                        overnight[s.room] = [s]
                                    if not s.room.usage:
                                        s.room.usage = s.type.capitalize()
                    for room in sorted(overnight):
                        print('Overnight %s (%s)' % (room.usage, room.name))
                        for s in overnight[room]:
                            print('%s %s' % (s.time, s.title))
                        print('')
                    print('')
                exit(0)
