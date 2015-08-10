#!/usr/bin/env python

""" find overnight sessions (entirely within 'late night' slices) """
# fold this into grid.py eventually

import config
import session
import times

overnight = {}
day = None

config.parseConfig(config.CFG)
(sessions, participants) = session.read(config.filenames['schedule', 'input'])

def out():
    if not overnight:
        return
    print day
    for room in sorted(overnight):
        if room.usage:
            print('Overnight %s (%s)' % (room.usage, room.name))
        elif 'TV' in room.name:
            print('Overnight TV (%s)' % room.name)
        else:
            print('Overnight ?? (%s)' % room.name)
        for s in overnight[room]:
            print '%s %s' % (s.time, s.title)
        print

for s in sessions:
    if s.day != day:
        out()
        day = s.day
        overnight = {}
    if s.time > times.Time('01:00') and  \
       s.time + s.duration < times.Time('08:30'):
        try:
            overnight[s.room].append(s)
        except KeyError:
            overnight[s.room] = [s]
out()
