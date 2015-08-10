#!/usr/bin/env python

""" Find repeated sessions. Output is formatted for arisia.cfg. """

import config
import session

title = {}
descr = {}
dup_t = {}
dup_d = {}

config.parseConfig(config.CFG)
(sessions, participants) = session.read(config.filenames['schedule', 'input'])

for s in sessions:
    if s.title in title:
        dup_t[s] = title[s.title]
    else:
        title[s.title] = s

    if s.description in descr:
        dup_d[s] = descr[s.description]
    else:
        descr[s.description] = s

if dup_t:
    print '# by title'
    for s in sorted(dup_t):
        print('%s = %s\t# %s' % (s.sessionid, title[s.title].sessionid, s.title))

if dup_d:
    print '# by description'
    for s in sorted(dup_d):
        print('%s = %s\t# %s' % (s.sessionid, descr[s.description].sessionid, s.title))
