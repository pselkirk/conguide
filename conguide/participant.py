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

import re

import config

class Participant(object):

    def __init__(self, name):
        self._readconfig()

        self.name = name
        self.sessions = []
        try:
            # configured sortkey (usually unhyphenated last name)
            self.sortkey = Participant.sortname[name].lower()
        except KeyError:
            # sortkey = Lastname Firstname Middle
            nn = name.split(' ')
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

    def _readconfig(self):
        Participant._readconfig = lambda x: None
        Participant.sortname = {}
        try:
            for name, sortkey in config.items('participant sort name'):
                Participant.sortname[name] = sortkey.lower()
        except config.NoSectionError:
            pass

    def __lt__(self, other):
        return (other and (self.sortkey < other.sortkey))

    def __eq__(self, other):
        return (other and (self.sortkey == other.sortkey))

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.name


def read(fn, participants):
    import importlib
    value = config.get('input file importer', 'reader')
    try:
        filereader = importlib.import_module(value)
    except ImportError:
        filereader = importlib.import_module('.' + value, 'conguide')
    return filereader.read_bios(fn, participants)
