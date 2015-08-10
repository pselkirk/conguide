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

import argparse

import participant
import uncsv

debug = False
verbose = False
participants = [{}, {}]

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--debug', action='store_true',
                    help='add debugging/trace information')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='print full description changes')
parser.add_argument('files', nargs=argparse.REMAINDER,
                    help='one or two snapshots of PubBio.csv')
args = parser.parse_args()
debug = args.debug
verbose = args.verbose

if not args.files or len(args.files) > 2:
    print('specify one or two .csv files')
    parser.print_help()
    exit(1)
elif len(args.files) == 1:
    args.files.append('PubBio.csv')

def read(fn):
    participants = {}
    for row in uncsv.read(fn):
        p = participant.Participant(row['pubsname'])
        p.badgeid = row['badgeid']
        p.firstname = row['firstname']
        p.lastname = row['lastname']
        p.bio = row['bio']
        participants[p.badgeid] = p
    return participants

participants[0] = read(args.files[0])
participants[1] = read(args.files[1])

added = []
removed = []
ch_name = []
ch_pubsname = []
ch_bio = []

def pheader(p):
    name = '%s %s' % (p.firstname, p.lastname)
    string = '%s: %s' % (p.badgeid, name)
    if p.pubsname != name:
        string += ' (%s)' % p.pubsname
    return string

for p in sorted(participants[1].values()):
    if not p.badgeid in participants[0]:
        added.append(pheader(p))

for p in sorted(participants[0].values()):
    ph = pheader(p)
    if debug:
        print(ph)
    p1 = participants[1].get(p.badgeid)
    if not p1:
        removed.append(ph)
        continue
    if p1.firstname != p.firstname or p1.lastname != p.lastname:
        ch_name.append('%s -> %s %s' % (ph, p1.firstname, p1.lastname))
    if p1.pubsname != p.pubsname:
        ch_pubsname.append('%s: %s -> %s' % (ph, p.pubsname, p1.pubsname))
    if p1.bio != p.bio:
        if verbose:
            ch_bio.append('%s: %s -> %s' % (ph, p.bio, p1.bio))
        else:
            ch_bio.append(ph)

if added:
    print('\nadded participants:\n%s' % '\n'.join(added))
if removed:
    print('\nremoved participants:\n%s' % '\n'.join(removed))
if ch_name:
    print('\nname changes:\n%s' % '\n'.join(ch_name))
if ch_pubsname:
    print('\npubsname changes:\n%s' % '\n'.join(ch_pubsname))
if ch_bio:
    print('\nbio changes:\n%s' % '\n'.join(ch_bio))
