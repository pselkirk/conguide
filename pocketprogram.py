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

import codecs

import config

class Output:

    def __init__(self, fn, fd=None):
        if fd:
            self.f = fd
            self.leaveopen = True
        else:
            #self.f = open(fn, 'w')
            self.f = codecs.open(fn, 'w', 'utf-8', 'replace')
            self.leaveopen = False

    def __del__(self):
        if not self.leaveopen:
            self.f.close()

if __name__ == '__main__':
    import bios
    import cmdline
    import featured
    import grid
    import participant
    import schedule
    import tracklist as tracks
    import xref

    args = cmdline.cmdline()
    (sessions, participants) = config.filereader.read(config.filenames['schedule', 'input'])
    if ('bios', 'input') in config.filenames:
        participants = config.filereader.read_bios(config.filenames['bios', 'input'], participants)

    for mode in ('text', 'html', 'xml', 'indesign'):
        if eval('args.' + mode):
            for report in ('schedule', 'featured', 'tracks', 'xref', 'bios', 'grid'):
                if (report, mode) in config.filenames:
                    writer = eval(report + '.write')
                    try:
                        output = eval('%s.%sOutput' % (report, mode.capitalize()))
                    except AttributeError:
                        # e.g. 'module' object has no attribute 'XmlOutput'
                        # output function is not defined for that mode
                        None
                    else:
                        if report in ('xref', 'bios'):
                            source = participants
                        else:
                            source = sessions
                        writer(output(config.filenames[report, mode]), source)

    if args.xml and ('pocketprogram', 'xml') in config.filenames:
        f = codecs.open(config.filenames['pocketprogram', 'xml'], 'w', 'utf-8', 'replace')
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<pocketprogram>\n')
        schedule.write(schedule.XmlOutput(None, f), sessions)
        featured.write(featured.XmlOutput(None, f), sessions)
        tracks.write(tracks.XmlOutput(None, f), sessions)
        xref.write(xref.XmlOutput(None, f), participants)
        f.write('</pocketprogram>\n')
        f.close()
