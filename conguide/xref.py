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
import output
import session

class Output(output.Output):

    def __init__(self, fn, fd=None):
        output.Output.__init__(self, fn, fd)
        Output._readconfig(self)

    def _readconfig(self):
        Output._readconfig = lambda x: None
        Output.template = {}
        try:
            for key, value in config.items('xref template'):
                Output.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def strXref(self, participant):
        return self.markupXref(self.fillTemplate(self.template['xref'], participant)) + '\n'

    def markupXref(self, text):
        return text

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append(self.fillTemplate(self.template['session'], s))
        return ', '.join(ss)

    def markupSessions(self, participant, text):
        return text

    def strParticipant(self, participant):
        return output.Output.strParticipant(self, participant)

    def markupParticipant(self, participant, text):
        return output.Output.markupParticipant(self, participant, text)

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('xref template text'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        title = self.convention + ' Program Participant Cross-Reference'
        self.f.write(config.html_header % (title, '', title, config.source_date))

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('xref template html'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def markupParticipant(self, participant, name):
        return '<a name="%s"></a>%s' % (re.sub(r'\W', '', name), name)

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append(self.fillTemplate(self.template['session'], s))
        return '\n'.join(ss)

    def markupTitle(self, session, title):
        return '<a href="%s#%s">%s</a>' % \
            (config.get('output files html', 'schedule'), session.sessionid, title)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self._readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<xrefs>')

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('xref template xml'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</xrefs>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def markupXref(self, text):
        return '<xref>%s</xref>' % text if text else ''

    def markupParticipant(self, participant, name):
        return '<xr-name>%s</xr-name>' % name if name else ''

    def markupSessions(self, participant, sessions):
        return '<xr-sessions>%s</xr-sessions>' % sessions if sessions else ''

def write(output, participants):

    for p in sorted(participants.values()):
        if p.sessions:
            output.f.write(output.strXref(p))

def main(args):
    fn = args.infile or config.get('input files', 'schedule')
    (sessions, participants) = session.read(fn)
    if args.all:
        args.text = True
        args.html = True
        args.xml = True
    for mode in ('text', 'html', 'xml'):
        if eval('args.' + mode):
            outfunc = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(outfunc(args.outfile), participants)
            else:
                try:
                    write(outfunc(config.get('output files ' + mode, 'xref')),
                          participants)
                except config.NoOptionError:
                    pass
