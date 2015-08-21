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

import copy
import re

import config
import participant
import pocketprogram
import session

class Output(pocketprogram.Output):

    def __init__(self, fn, fd=None):
        pocketprogram.Output.__init__(self, fn, fd)
        self.__readconfig()

    def __readconfig(self):
        Output.__readconfig = lambda x: None
        Output.template = {}
        try:
            for key, value in config.items('xref template'):
                Output.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

    def writeXref(self, participant):
        if participant.sessions:
            self.f.write(self.strName(participant))
            self.f.write(self.strSessions(participant))

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()

    def __readconfig(self):
        TextOutput.__readconfig = lambda x: None
        TextOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('xref template text'):
                TextOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

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
        self.__readconfig()
        title = self.convention + ' Program Participant Cross-Reference'
        self.f.write(config.html_header % (title, '', title, config.source_date))

    def __readconfig(self):
        HtmlOutput.__readconfig = lambda x: None
        HtmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('xref template html'):
                HtmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

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
                       config.get('output files html', 'schedule'),
                       s.sessionid, self.cleanup(s.title)))
        return '%s\n</dl>\n' % '\n'.join(ss)

    def writeXref(self, participant):
        if participant.sessions:
            self.f.write('<a name="%s"></a>' % re.sub(r'\W', '', participant.__str__()))
            Output.writeXref(self, participant)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self.__readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<xrefs>')

    def __readconfig(self):
        XmlOutput.__readconfig = lambda x: None
        XmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('xref template xml'):
                XmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

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
    (sessions, participants) = session.read(config.get('input files', 'schedule'))

    for mode in ('text', 'html', 'xml'):
        if eval('args.' + mode):
            output = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(output(args.outfile), participants)
            else:
                try:
                    write(output(config.get('output files ' + mode, 'xref')),
                          participants)
                except config.NoOptionError:
                    pass
