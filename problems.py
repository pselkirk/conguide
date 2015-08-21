#!/usr/bin/env python

""" Find common problems in pocketprogram.csv. """

import argparse
import re

import cmdline
import config
import session
from times import Duration

parent = cmdline.cmdlineParser(modes=False)
parser = argparse.ArgumentParser(add_help=False, parents=[parent])
parser.add_argument('--duration', action='store', default='12hr',
                    help='what duration is "too long" (default 12hr)')
args = cmdline.cmdline(parser, modes=False)
(sessions, participants) = session.read(config.get('input files', 'schedule'))

def check(text, func, duration=False):
    found = False
    for s in sessions:
        if func(s):
            if not found:
                print(text)
                found = True
            if duration:
                print('%4s %s (%s)' % (s.sessionid, s.title, s.duration))
            else:
                print('%4s %s' % (s.sessionid, s.title))
    if found:
        print('')

def lower(s):
    for w in s.title.split(' '):
        if w.islower() and len(w) > 3 and not re.search(r'\d', w) and \
           w != 'with' and w != 'from' and w != 'into':
            return True
    return False

check('room "Other"', lambda s: s.room.name == 'Other')
check('all uppercase', lambda s: s.title.isupper())
check('bogus m-dash', lambda s: re.search(r'\S-\s', s.title))
check('day in title', lambda s: re.search(r'\wday\W', s.title))
check('[bracket text] in title', lambda s: re.search(r'[\[\]]', s.title))
check('lowercase words in title', lower)
#check('no description', lambda s: not s.description)
#check('no period', lambda s: re.search(r'\w$', s.description))
check('no duration', lambda s: s.duration == Duration('0'))
check('negative duration', lambda s: s.duration < Duration('0'))
check('long duration', lambda s: s.duration >= Duration(args.duration), duration=True)
