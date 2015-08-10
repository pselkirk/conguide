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

import re

import config
import pocketprogram
import session

class Output(pocketprogram.Output):

    def writeDay(self, session):
        self.f.write(self.strDay(session))

    def writeSession(self, session):
        self.f.write(self.strIndex(session))
        self.f.write(self.strTime(session))
        self.f.write(self.strTitle(session))
        self.f.write(self.strRoom(session))

class TextOutput(Output):

    def cleanup(self, text):
        # convert italics
        return re.sub('</?i>', '*', text)

    def strDay(self, session):
        return '\n\n%s\n' % str(session.day).upper()

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
        title = config.convention + ' Featured Panels &amp; Events'
        self.f.write(config.html_header % (title, '', title, config.source_date))

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strDay(self, session):
        return '<hr /><h3>%s</h3>\n' % str(session.day).upper()

    def strIndex(self, session):
        return '<dl><dt>'

    def strTime(self, session):
        return '%s ' % session.time

    def strTitle(self, session):
        return '<a href="%s#%s">%s</a> ' % \
            (config.filenames['schedule', 'html'], session.sessionid, self.cleanup(session.title))

    def strRoom(self, session):
        return '<i>&mdash; %s</i></dt></dl>\n' % session.room

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<featured>')

    def __del__(self):
        self.f.write('</featured>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strDay(self, session):
        return '<fe-day>%s</fe-day>\n' % str(session.day).upper()

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
    # XXX It would be more efficient to write a 'featured' array as we
    # build the 'sessions' list.
    for s in sessions:
        if s.sessionid in config.featured:
            if s.day != curday:
                nextday = s
                curday = s.day
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
    (args, sessions, participants) = cmdline.cmdline(parser)

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
                if p.pubsname in config.goh:
                    return True
            return False

        def out(label, a):
            print(label)
            for s in a:
                print('%s\t# %s' % (s.sessionid, s.title))

        #gohtrack = []
        gohpartic = []
        #trackless = []
        #drama = []
        #concert = []
        #for s in sessions:
        #    if s.track == 'GOH':
        #        gohtrack.append(s)
        #    elif is_goh(s):
        #        gohpartic.append(s)
        #    elif s.track == 'Trackless events':
        #        trackless.append(s)
        #    elif s.type == 'Drama':
        #        drama.append(s)
        #    elif s.type == 'Concert':
        #        concert.append(s)
        #out("### GOH track", gohtrack)
        #out("### GOH participant(s)", gohpartic)
        #out("### Trackless events", trackless)
        #out("### Drama", drama)
        #out("### Concert", concert)

        ss = {}
        for session in sessions:
            for i, expr in enumerate(config.research):
                if eval(expr):
                    try:
                        ss[i].append(session)
                    except KeyError:
                        ss[i] = [session]
                    break
            if is_goh(session):
                gohpartic.append(session)
        for i in sorted(ss):
            out('### %s' % config.research[i], ss[i])
        out("### GOH participant(s)", gohpartic)

        exit(0)

    if args.text:
        if args.outfile:
            write(TextOutput(args.outfile), sessions)
        else:
            write(TextOutput(config.filenames['featured', 'text']), sessions)

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile), sessions)
        else:
            write(HtmlOutput(config.filenames['featured', 'html']), sessions)

    if args.xml:
        if args.outfile:
            write(XmlOutput(args.outfile), sessions)
        else:
            write(XmlOutput(config.filenames['featured', 'xml']), sessions)
