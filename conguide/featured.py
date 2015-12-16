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
            for key, value in config.items('featured template'):
                Output.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass
        Output.featured = []
        try:
            for (sessionid, unused) in config.items('featured sessions'):
                Output.featured.append(sessionid)
        except config.NoSectionError:
            pass

    def markupSession(self, session, text):
        return text

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('featured template text'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def cleanup(self, text):
        # convert italics
        return re.sub('</?i>', '*', Output.cleanup(self, text))

    def markupDay(self, session, text):
        return '\n%s' % text

    def markupIndex(self, session, text):
        return '[%s]' % text

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        title = self.convention + ' Featured Panels &amp; Events'
        self.f.write(config.html_header % (title, '', title,
                                           config.source_date))

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('featured template html'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def markupTitle(self, session, text):
        return '<a href="%s#%s">%s</a>' % \
            (config.get('output files html', 'schedule'), session.sessionid, text)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self._readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<featured>')

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('featured template xml'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</featured>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def markupSession(self, session, text):
        return '<fe-session>%s</fe-session>' % text if text else ''

    def markupDay(self, session, text):
        return '<fe-day>%s</fe-day>' % text if text else ''

    def markupIndex(self, session, text):
        return '<fe-index>%s</fe-index>' % text if text else ''

    def markupTime(self, session, text):
        return '<fe-time>%s</fe-time>' % text if text else ''

    def markupTitle(self, session, text):
        return '<fe-title>%s</fe-title>' % text if text else ''

    def markupRoom(self, session, text):
        return '<fe-room>%s</fe-room>' % text if text else ''

    def markupLevel(self, session, text):
        return '<fe-room>%s</fe-room>' % text if text else ''

def write(output, sessions):
    def writeDay(session):
        text = output.fillTemplate(output.template['day'], session)
        output.f.write(text + '\n')

    def writeSession(session):
        text = output.fillTemplate(output.template['session'], session)
        text = output.markupSession(session, text)
        output.f.write(text + '\n')

    curday = None
    # TODO: It would be more efficient to write a 'featured' array as we
    # build the 'sessions' list. Or even add a 'featured' attribute to the
    # session.
    for s in sessions:
        if s.sessionid in Output.featured:
            if s.time.day != curday:
                nextday = s
                curday = s.time.day
            if s.time.hour > 2 and nextday:
                writeDay(s)
                nextday = None
            writeSession(s)

def main(args):
    def research(sessions):
        # research - list all sessions in major-draw tracks, plus all sessions
        # with at least one GOH participant, formatted for cut-and-paste into
        # arisia.cfg. Note this is just a starting point, and often misses
        # things like the Masquerade.
        #
        # XXX one current glitch is that cmdline.py will barf if --research
        # is given without an output mode, even though we don't use it
        research = []
        try:
            for unused, expr in config.items('featured research'):
                expr = expr.replace('track', 'session.track')
                expr = expr.replace('type', 'session.type')
                research.append(expr)
        except config.NoSectionError:
            return
        goh = {}
        for name in re.split(r',\s*', config.get('convention', 'goh')):
            goh[name] = True

        def is_goh(s):
            return any(filter(lambda p: p.name in goh, s.participants))

        def out(label, a):
            print(label)
            for s in a:
                print('%s\t# %s' % (s.sessionid, s.title))

        gohpartic = []
        ss = {}
        for session in sessions:
            for i, expr in enumerate(research):
                if eval(expr):
                    try:
                        ss[i].append(session)
                    except KeyError:
                        ss[i] = [session]
                    break
            if is_goh(session):
                gohpartic.append(session)
        for i in sorted(ss):
            out('### %s' % research[i], ss[i])
        out("### GOH participant(s)", gohpartic)

    fn = args.infile or config.get('input files', 'schedule')
    (sessions, participants) = session.read(fn)

    if args.all:
        args.text = True
        args.html = True
        args.xml = True
    if hasattr(args, 'research'):
        research(sessions)
    else:
        for mode in ('text', 'html', 'xml'):
            if eval('args.' + mode):
                outfunc = eval('%sOutput' % mode.capitalize())
                if args.outfile:
                    write(outfunc(args.outfile), sessions)
                else:
                    try:
                        write(outfunc(config.get('output files ' + mode, 'featured')),
                              sessions)
                    except config.NoOptionError:
                        pass
