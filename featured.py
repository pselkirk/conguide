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
import pocketprogram
import session

class Output(pocketprogram.Output):

    def __init__(self, fn, fd=None):
        pocketprogram.Output.__init__(self, fn, fd)
        self.__readconfig()

    def __readconfig(self):
        Output.template = {}
        try:
            for key, value in config.items('featured template'):
                Output.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass
        Output.featured = []
        try:
            for (sessionid, unused) in config.items('featured sessions'):
                Output.featured.append(sessionid)
        except config.NoSectionError:
            pass
        Output.research = []
        try:
            for unused, expr in config.items('featured research'):
                expr = expr.replace('track', 'session.track')
                expr = expr.replace('type', 'session.type')
                Output.research.append(expr)
        except config.NoSectionError:
            pass
        Output.__readconfig = lambda x: None

    def writeDay(self, session):
        self.f.write(self.strDay(session))

    def writeSession(self, session):
        self.f.write(self.strIndex(session))
        self.f.write(self.strTime(session))
        self.f.write(self.strTitle(session))
        self.f.write(self.strRoom(session))

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()

    def __readconfig(self):
        TextOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('featured template text'):
                TextOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass
        TextOutput.__readconfig = lambda x: None

    def cleanup(self, text):
        # convert italics
        return re.sub('</?i>', '*', text)

    def strDay(self, session):
        return '\n\n%s\n' % str(session.time.day).upper()

    def strIndex(self, session):
        return '\n[%s]\t' % session.sessionid

    def strTime(self, session):
        return '%s\t' % session.time

    def strTitle(self, session):
        return '%s\t' % self.cleanup(session.title)

    def strRoom(self, session):
        return '%s\n' % session.room

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()
        title = Output.convention + ' Featured Panels &amp; Events'
        self.f.write(config.html_header % (title, '', title,
                                           config.source_date))

    def __readconfig(self):
        HtmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('featured template html'):
                HtmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass
        HtmlOutput.__readconfig = lambda x: None

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strDay(self, session):
        return '<hr /><h3>%s</h3>\n' % str(session.time.day).upper()

    def strIndex(self, session):
        return '<dl><dt>'

    def strTime(self, session):
        return '%s ' % session.time

    def strTitle(self, session):
        return '<a href="%s#%s">%s</a> ' % \
            (config.get('output files html', 'schedule'),
             session.sessionid, self.cleanup(session.title))

    def strRoom(self, session):
        return '<i>&mdash; %s</i></dt></dl>\n' % session.room

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self.__readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<featured>')

    def __readconfig(self):
        XmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('featured template xml'):
                XmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass
        XmlOutput.__readconfig = lambda x: None

    def __del__(self):
        self.f.write('</featured>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strDay(self, session):
        return '<fe-day>%s</fe-day>\n' % str(session.time.day).upper()

    def strIndex(self, session):
        return '<fe-session><fe-index>%d</fe-index>\t' % session.index

    def strTime(self, session):
        return '<fe-time>%s</fe-time>\t' % session.time

    def strTitle(self, session):
        return '<fe-title>%s</fe-title>\t' % self.cleanup(session.title)

    def strRoom(self, session):
        return '<fe-room>%s</fe-room></fe-session>\n' % session.room

def write(output, sessions):
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
                output.writeDay(s)
                nextday = None
            output.writeSession(s)

if __name__ == '__main__':
    import argparse
    import cmdline

    parent = cmdline.cmdlineParser(io=True)
    parser = argparse.ArgumentParser(add_help=False, parents=[parent])
    parser.add_argument('--research', action='store_true',
                        help='identify likely candidates for "featured" list')
    args = cmdline.cmdline(parser, io=True)
    session.read(config.get('input files', 'schedule'))

    # research - list all sessions in major-draw tracks, plus all sessions
    # with at least one GOH participant, formatted for cut-and-paste into
    # arisia.cfg. Note this is just a starting point, and often misses
    # things like the Masquerade.
    #
    # XXX one current glitch is that cmdline.py will barf if --research
    # is given without an output mode, even though we don't use it
    if args.research:
        def is_goh(s):
            for p in s.participants:
                if p.name in Output.goh:
                    return True
            return False

        def out(label, a):
            print(label)
            for s in a:
                print('%s\t# %s' % (s.sessionid, s.title))

        gohpartic = []
        ss = {}
        for session in Output.sessions:
            for i, expr in enumerate(Output.research):
                if eval(expr):
                    try:
                        ss[i].append(session)
                    except KeyError:
                        ss[i] = [session]
                    break
            if is_goh(session):
                gohpartic.append(session)
        for i in sorted(ss):
            out('### %s' % Output.research[i], ss[i])
        out("### GOH participant(s)", gohpartic)

        exit(0)

    for mode in ('text', 'html', 'xml'):
        if eval('args.' + mode):
            output = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(output(args.outfile), session.Session.sessions)
            else:
                try:
                    write(output(config.get('output files ' + mode, 'featured')),
                          session.Session.sessions)
                except config.NoOptionError:
                    pass
