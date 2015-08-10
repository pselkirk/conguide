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
    import tracklist
    import xref

    (args, sessions, participants) = cmdline.cmdline()
    if ('bios', 'input') in config.filenames:
        participants = participant.read(config.filenames['bios', 'input'], participants)
    if ('grid', 'text') in config.filenames or \
       ('grid', 'html') in config.filenames or \
       ('grid', 'indesign') in config.filenames:
        matrix = grid.matrix(sessions)

    if args.text:
        if ('schedule', 'text') in config.filenames:
            schedule.write(schedule.TextOutput(config.filenames['schedule', 'text']), sessions)
        if ('featured', 'text') in config.filenames:
            featured.write(featured.TextOutput(config.filenames['featured', 'text']), sessions)
        if ('tracks', 'text') in config.filenames:
            tracklist.write(tracklist.TextOutput(config.filenames['tracks', 'text']), sessions)
        if ('xref', 'text') in config.filenames:
            xref.write(xref.TextOutput(config.filenames['xref', 'text']), participants)
        if ('bios', 'text') in config.filenames:
            bios.write(bios.TextOutput(config.filenames['bios', 'text']), participants)
        #if ('grid', 'text') in config.filenames:
        #    grid.write(grid.TextOutput(config.filenames['grid', 'text']), matrix)

    if args.html:
        if ('schedule', 'html') in config.filenames:
            schedule.write(schedule.HtmlOutput(config.filenames['schedule', 'html']), sessions)
        if ('featured', 'html') in config.filenames:
            featured.write(featured.HtmlOutput(config.filenames['featured', 'html']), sessions)
        if ('tracks', 'html') in config.filenames:
            tracklist.write(tracklist.HtmlOutput(config.filenames['tracks', 'html']), sessions)
        if ('xref', 'html') in config.filenames:
            xref.write(xref.HtmlOutput(config.filenames['xref', 'html']), participants)
        if ('bios', 'html') in config.filenames:
            bios.write(bios.HtmlOutput(config.filenames['bios', 'html']), participants)
        if ('grid', 'html') in config.filenames:
            grid.write(grid.HtmlOutput(config.filenames['grid', 'html']), matrix)

    if args.xml:
        if ('pocketprogram', 'xml') in config.filenames:
            f = codecs.open(config.filenames['pocketprogram', 'xml'], 'w', 'utf-8', 'replace')
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<pocketprogram>\n')
            schedule.write(schedule.XmlOutput(None, f), sessions)
            featured.write(featured.XmlOutput(None, f), sessions)
            tracklist.write(tracklist.XmlOutput(None, f), sessions)
            xref.write(xref.XmlOutput(None, f), participants)
            f.write('</pocketprogram>\n')
            f.close()
        # bios are in the souvenir book, and regenerating them every time we
        # regenerate the pocket program will only annoy me.
        #if ('bios', 'xml') in config.filenames:
        #    bios.write(bios.XmlOutput(config.filenames['bios', 'xml']), participants)

    if args.indesign:
        if ('grid', 'indesign') in config.filenames:
            grid.write(grid.IndesignOutput(config.filenames['grid', 'indesign']), matrix)
