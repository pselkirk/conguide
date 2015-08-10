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

import csv
import re

import config

def read(fn, raw=False):
    """ Read a CSV file, and return a list of dicts. """
    out = []
    if config.PY3:
        f = open(fn, 'rt', encoding='utf-8', newline='')
    else:
        f = open(fn, 'rb')
    reader = csv.DictReader(f)
    for row in reader:
        if not raw:
            row = cleanup(row)
        out.append(row)
    return out

def cleanup(row):
    for key in row:
        if config.PY3:
            field = row[key]
        else:
            field = row[key].decode('utf-8')

        # convert all whitespace (including newlines) to single spaces
        field = re.sub(r'\s+', ' ', field)

        # remove extraneous whitespace
        field = re.sub(r'^ ', '', field) # leading space
        field = re.sub(r' $', '', field) # trailing space
        field = re.sub(r' ([,.;])', r'\1', field) # space before punctuation

        # try to guess where italics were intended
        field = re.sub(r'(?<!\w)_([^_]+?)_(?!\w)', r'<i>\1</i>', field) # _italic_
        field = re.sub(r'(?<!\w)\*([^*]+?)\*(?!\w)', r'<i>\1</i>', field) # *italic*

        # Let's don't mess with unicode that's already there;
        # let's concentrate on converting ascii to appropriate unicode

        # XXX filter bad unicode
        #field = re.sub(u'\u202a', '', field)
        #field = re.sub(u'\u202c', '', field)

        # convert dashes
        field = re.sub(r'(\d) *- *(\d)', r'\1'+u'\u2013'+r'\2', field) # the much-misunderstood n-dash
        field = re.sub(r' *-{2,} *', u'\u2014', field)   # m--dash, m -- dash, etc.
        field = re.sub(r' +- +', u'\u2014', field)       # m - dash

        # right quote before abbreviated years and decades ('70s)
        field = re.sub(r'\'([0-9])', u'\u2019'+r'\1', field)

        # convert quotes
        field = re.sub(r'^\'', u'\u2018', field) # beginning single quote -> left
        field = re.sub(r'\'$', u'\u2019', field) # ending single quote -> right
        field = re.sub(r'([^\w,.!?])\'(\w)', r'\1'+u'\u2018'+r'\2', field) # left single quote
        field = re.sub(r'\'', u'\u2019', field)  # all remaining single quotes -> right

        field = re.sub(r'^"', u'\u201c', field)  # beginning double quote -> left
        field = re.sub(r'"$', u'\u201d', field)  # ending double quote -> right
        field = re.sub(r'([^\w,.!?])"(\w)', r'\1'+u'\u201c'+r'\2', field) # left double quote
        field = re.sub(r'"', u'\u201d', field)   # all remaining double quotes -> right

        row[key] = field
    return row

if __name__ == '__main__':
    ses = read('some.csv')
    for row in ses:
        print(row)
