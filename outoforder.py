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

""" Find participants who might be sorted out of order. """

import difflib

import config
import session
import uncsv

config.parseConfig(config.CFG)

ps = []
config.filereader.read(config.filenames['schedule', 'input'])
for p in sorted(config.participants.values()):
    ps.append(p.pubsname)

pb = []
for p in uncsv.read('PubBio.csv'):
    pubsname = p['pubsname']
    if pubsname in config.chname:
        pubsname = config.chname[pubsname]
    pb.append(pubsname)

for line in difflib.unified_diff(pb, ps):
    print(line)
