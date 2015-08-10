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

""" Consistency checks for guidebook csv files. """

import uncsv

verbose = False

titles = {}
for row in uncsv.read('guidebook.csv'):
    title = row['Session Title']
    if title in titles:
        print('duplicate session title "%s"' % title)
    else:
        titles[title] = 0

names = {}
for row in uncsv.read('guidebook-bios.csv'):
    name = row['Name']
    if name in names:
        print('duplicate name "%s"' % name)
    else:
        names[name] = 0

for row in uncsv.read('guidebook-links.csv'):
    name = row['Item Name (Optional)']
    title = row['Link To Session Name (Optional)']
    if not name in names:
        print('name "%s" not found in guidebook-bios.csv' % name)
    else:
        names[name] += 1
    if not title in titles:
        print('title "%s" not found in guidebook.csv' % title)
    else:
        titles[title] += 1

for name, count in names.items():
    if not count:
        print('no sessions for "%s"' % name)

if verbose:
    for title, count in titles.items():
        if not count:
            print('no participants for "%s"' % title)
