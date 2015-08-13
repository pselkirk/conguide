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
import pocketprogram

class Output(pocketprogram.Output):

    def writeXref(self, participant):
        if participant.sessions:
            self.f.write(self.strName(participant))
            self.f.write(self.strSessions(participant))

class TextOutput(Output):

    def strName(self, participant):
        return '%s: ' % participant.__str__()

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append(str(s.sessionid))
        return '%s\n' % ', '.join(ss)

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        title = config.convention + ' Program Participant Cross-Reference'
        self.f.write(config.html_header % (title, '', title,
                                           config.source_date))

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strName(self, participant):
        return '<dl><dt><b>%s</b></dt>\n' % participant

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append('<dd>%s %s <a href="%s#%s">%s</a></dd>' % \
                      (s.time.day.shortname, s.time,
                       config.filenames['schedule', 'html'], s.sessionid,
                       self.cleanup(s.title)))
        return '%s\n</dl>\n' % '\n'.join(ss)

    def writeXref(self, participant):
        if participant.sessions:
            self.f.write('<a name="%s"></a>' % re.sub(r'\W', '', participant.__str__()))
            Output.writeXref(self, participant)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<xrefs>')

    def __del__(self):
        self.f.write('</xrefs>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def strName(self, participant):
        return '<xref><xr-name>%s</xr-name>: ' % participant

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append(str(s.index))
        return '<xr-sessions>%s</xr-sessions></xref>\n' % ', '.join(ss)

def write(output, participants):

    for p in sorted(participants.values()):
        output.writeXref(p)

if __name__ == '__main__':
    import cmdline

    args = cmdline.cmdline(io=True)
    config.filereader.read(config.filenames['schedule', 'input'])

    if args.text:
        if args.outfile:
            write(TextOutput(args.outfile), config.participants)
        elif ('xref', 'text') in config.filenames:
            write(TextOutput(config.filenames['xref', 'text']),
                  config.participants)

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile), config.participants)
        elif ('xref', 'html') in config.filenames:
            write(HtmlOutput(config.filenames['xref', 'html']),
                  config.participants)

    if args.xml:
        if args.outfile:
            write(XmlOutput(args.outfile), config.participants)
        elif ('xref', 'html') in config.filenames:
            write(XmlOutput(config.filenames['xref', 'xml']),
                  config.participants)
