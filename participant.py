#!/usr/bin/env python

# Copyright (c) 2014, Paul Selkirk
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

import re

import config
import uncsv

class Participant:

    def __init__(self, pubsname):
        self.pubsname = pubsname
        self.sessions = []
        try:
            # configured sortkey (usually unhyphenated last name)
            self.sortkey = config.sortname[pubsname].lower()
        except KeyError:
            # sortkey = Lastname Firstname Middle
            nn = pubsname.split(' ')
            # the last token is usually the last name
            first = nn[:-1]
            last = nn[-1]
            # some common exceptions to the rule
            if first and \
               (re.match(r'd[aeiou]l?$', first[-1], re.IGNORECASE) or \
                re.match(r'v[ao]n$', first[-1], re.IGNORECASE) or \
                re.match(r'[JS]r\.?$', last) or \
                re.match(r'I+$', last) or \
                re.match(r'[^A-Za-z]+$', last) or \
                last == 'PhD' or last == 'DVM'):
                # last two tokens are the last name
                first = nn[:-2]
                last = ' '.join(nn[-2:])
            # remove punctuation for sorting purposes
            last = re.sub(r'\W', ' ', last, re.UNICODE)
            # mash it together and  make it case-insensitive
            self.sortkey = ' '.join([last] + first).lower()

    def __lt__(self, other):
        return (other and (self.sortkey < other.sortkey))

    def __eq__(self, other):
        return (other and (self.sortkey == other.sortkey))

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.pubsname

def read(fn, participants, quiet=False):
    """ Read the bios file, identify participants without sessions,
    and add fields for bios.py.
    """
    for row in uncsv.read(fn):
        pubsname = row['pubsname']
        if pubsname in config.chname:
            pubsname = config.chname[pubsname]
        if not pubsname in participants:
            if not quiet:
                print('new participant "%s"' % pubsname)
            participants[pubsname] = Participant(pubsname)
        participants[pubsname].firstname = row['firstname']
        participants[pubsname].lastname = row['lastname']
        participants[pubsname].bio = row['bio']
        participants[pubsname].badgeid = row['badgeid']
    return participants

if __name__ == '__main__':
    config.parseConfig(config.CFG)
    participants = read(config.filenames['bios', 'input'], {}, quiet=True)
    for p in sorted(participants.values()):
        print(p.pubsname)
    print(len(participants))
