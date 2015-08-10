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

class Session:

    def __init__(self):
        # XXX
        self.track = None
        self.type = None

    def __lt__(self, other):
        return (other and \
                ((self.time.day < other.time.day) or \
                 ((self.time.day == other.time.day) and \
                  ((self.time < other.time) or \
                   ((self.time == other.time) and \
                    (((not self.index or not other.index) and (self.room < other.room)) or \
                     (self.index < other.index)))))))
