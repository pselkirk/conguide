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

"""A front-end driver module to generate Convention Guide content.

usage: pocketprogram.py [-?] [-c CFG] [-d] [-q] [-t] [-h] [-x] [-i] [-a]

optional arguments:
  -?, --help            show this help message and exit
  -c CFG, --config CFG  config file (default "arisia.cfg")
  -d, --debug           add debugging/trace information
  -q, --quiet           suppress warning messages
  -t, --text            text output
  -h, --html            html output
  -x, --xml             InDesign xml output
  -i, --indesign        InDesign tagged text output
  -a, --all             all output modes

Depending on configuration, this generates schedule, program participant
cross-reference (xref), featured sessions, and track list.

"""

import codecs
import re

import config

class Output(object):
    """ Parent class for TextOutput etc. in schedule.py etc. """

    def __init__(self, fn, fd=None, codec='utf-8'):
        if fd:
            self.f = fd
            self.leaveopen = True
        else:
            #self.f = open(fn, 'w')
            self.f = codecs.open(fn, 'w', codec)
            self.leaveopen = False

    def __del__(self):
        if not self.leaveopen:
            self.f.close()

    def cleanup(self, text):
        if text:
            # convert dashes
            # the much-misunderstood n-dash
            text = re.sub(r'(\d) *- *(\d)', r'\1'+u'\u2013'+r'\2', text)
            # m--dash, m -- dash, etc.
            text = re.sub(r' *-{2,} *', u'\u2014', text)
            # m - dash
            text = re.sub(r' +- +', u'\u2014', text)

            # convert quotes
            # right quote before abbreviated years and decades ('70s)
            text = re.sub(r'\'([0-9])', u'\u2019'+r'\1', text)
            # beginning single quote -> left
            text = re.sub(r'^\'', u'\u2018', text)
            # ending single quote -> right
            text = re.sub(r'\'$', u'\u2019', text)
            # left single quote
            text = re.sub(r'([^\w,.!?])\'(\w)', r'\1'+u'\u2018'+r'\2', text)
            # all remaining single quotes -> right
            text = re.sub(r'\'', u'\u2019', text)
            # beginning double quote -> left
            text = re.sub(r'^"', u'\u201c', text)
            # ending double quote -> right
            text = re.sub(r'"$', u'\u201d', text)
            # left double quote
            text = re.sub(r'([^\w,.!?])"(\w)', r'\1'+u'\u201c'+r'\2', text)
            # all remaining double quotes -> right
            text = re.sub(r'"', u'\u201d', text)

        return text

    def fillTemplate(self, template, session):
        # for optional data, replace square brackets with non-printing
        # characters, so we don't collide with square brackets in session
        # title or description
        # 02 = STX (start of text), 03 = ETX (end of text)
        template = template.replace('[', u'\u0002')
        template = template.replace(']', u'\u0003')
        # tokenize the template, and replace all field names with values
        fields = re.split(r'(\W+)', template)
        for i, tag in enumerate(fields):
            try:
                if re.match(r'\w+', tag):
                    fields[i] = eval('self.str%s(session)' % tag.capitalize())
                    if tag.isupper():
                        fields[i] = fields[i].upper()
            except AttributeError:
                None
        # reassemble the filled-in template
        str = ''.join(fields)
        # remove optional fields without data
        while i:
            (str, i) = re.subn(ur'\u0002[^\u0002\u0003\w]*\u0003', '', str)
        str = re.sub(ur'[\u0002\u0003]', '', str)
        return str

    def strDay(self, session):
        return str(session.time.day)

    def strTime(self, session):
        return str(session.time)

    def strIndex(self, session):
        return str(session.index)

    def strTitle(self, session):
        return self.cleanup(session.title)

    def strTrack(self, session):
        return str(self.track)

    def strType(self, session):
        return str(self.type)

    def strDuration(self, session):
        return str(session.duration)

    def strLevel(self, session):
        return str(session.room.level)

    def strRoom(self, session):
        return str(session.room)

    def strIcons(self, session):
        return ''

    def strDescription(self, session):
        return self.cleanup(session.description)

    def strParticipants(self, session):
        if session.participants:
            pp = []
            for p in session.participants:
                #name = str(p)
                name = p.__str__()
                if p in session.moderators:
                    name += u'\u00A0(m)'
                pp.append(name)
            return self.cleanup(', '.join(pp))
        else:
            return ''

    def strTags(self, session):
        try:
            if session.tags:
                return '#%s' % ', #'.join(session.tags)
            else:
                return ''
        except AttributeError:
            return ''


if __name__ == '__main__':
    import bios
    import cmdline
    import featured
    import grid
    import schedule
    import tracklist as tracks
    import xref

    args = cmdline.cmdline()
    config.filereader.read(config.filenames['schedule', 'input'])
    if ('bios', 'input') in config.filenames:
        config.filereader.read_bios(config.filenames['bios', 'input'])

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
                            source = config.participants
                        else:
                            source = config.sessions
                        writer(output(config.filenames[report, mode]), source)

    if args.xml and ('pocketprogram', 'xml') in config.filenames:
        f = codecs.open(config.filenames['pocketprogram', 'xml'], 'w', 'utf-8', 'replace')
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<pocketprogram>\n')
        schedule.write(schedule.XmlOutput(None, f), config.sessions)
        featured.write(featured.XmlOutput(None, f), config.sessions)
        tracks.write(tracks.XmlOutput(None, f), config.sessions)
        xref.write(xref.XmlOutput(None, f), config.participants)
        f.write('</pocketprogram>\n')
        f.close()
