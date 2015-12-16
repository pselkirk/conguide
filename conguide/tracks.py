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
from room import Room
import session

class Output(output.Output):

    def __init__(self, fn, fd=None):
        output.Output.__init__(self, fn, fd)
        Output._readconfig(self)

    def _readconfig(self):
        Output._readconfig = lambda x: None
        Output.template = {}
        try:
            for key, value in config.items('tracks template'):
                Output.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass
        Output.classifiers = []
        try:
            for area, expr in config.items('tracks classifier'):
                expr = expr.replace('track', 'session.track')
                expr = expr.replace('type', 'session.type')
                expr = re.sub(r'room == (\'\w+\')',
                              r'session.room == Room.rooms[\1]', expr)
                area = area.replace(' - ', u'\u2014')
                Output.classifiers.append((area, expr))
        except config.NoSectionError:
            pass
        try:
            val = config.get('tracks title prune', 'title starts with')
            val = re.sub(r'\'', '', val)
            val = re.sub(r',\s*', '|', val)
            Output.title_prune = val
        except (config.NoSectionError, config.NoOptionError):
            pass

    def strTrackList(self, tracks):
        return ''

    def strTrackSessions(self, trsessions):
        try:
            text = self.fillTemplate(self.template['track'], trsessions)
        except KeyError:
            return ''
        text = self.markupTrackSessions(text)
        return text + '\n'

    def markupTrackSessions(self, text):
        return text

    def strTrack(self, trsessions):
        name = trsessions[0]
        return self.cleanup(name)

    def strSessions(self, trsessions):
        ss = []
        for s in trsessions[1]:
            ss.append(self.fillTemplate(self.template['session'], s))
        return '\n'.join(ss)

    def markupSessions(self, trsessions, text):
        return text

    def strTitle(self, session):
        # XXX local policy - process [tracks title prune] config
        # remove redundant title info
        try:
            (title, n) = re.subn(Output.title_prune, '', session.title)
            if n:
                title = re.sub(r', ?&', ',', title)
                title = re.sub(r' &', ',', title)
                title = re.sub(r', and ', ', ', title)
        except AttributeError:
            pass
        return self.cleanup(title)

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('tracks template text'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', Output.cleanup(self, text))

    def markupTrackSessions(self, text):
        return '%s\n' % text

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        title = Output.convention + ' Schedule, by Area'
        self.f.write(config.html_header % (title, '', title,
                                           config.source_date))

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('tracks template html'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</dl></body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def strTrackList(self, tracks):
        str = '<ul>\n'
        for t in tracks:
            str += '<li><a href="#%s">%s</a></li>\n' % \
                   (re.sub(r'\W', '', t), self.cleanup(t))
        str += '</ul>\n<dl>'
        return str

    def markupTrack(self, trsessions, text):
        name = trsessions[0]
        return '<a name="%s">%s</a>' % (re.sub(r'\W', '', name), text)

    def markupTitle(self, session, text):
        return '<a href="%s#%s">%s</a>\n' % \
            (config.get('output files html', 'schedule'), session.sessionid, text)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self._readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<tracks>')

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('tracks template xml'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</tracks>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def markupTrackSessions(self, text):
        return '<track>%s</track>' % text if text else ''

    def markupTrack(self, trsessions, text):
        return '<tr-name>%s</tr-name>' % text if text else ''

    def markupIndex(self, session, text):
        return '<tr-index>%s</tr-index>' % text if text else ''

    def markupTitle(self, session, text):
        return '<tr-title>%s</tr-title>' % text if text else ''

def write(output, sessions):
    tracks = {}
    for session in sessions:
        t = session.track
        for k, v in Output.classifiers:
            if eval(v):
                t = k
                break
        if config.debug:
            print('%s: %s' % (t, session.title))
        try:
            tracks[t].append(session)
        except KeyError:
            tracks[t] = [session]

    output.f.write(output.strTrackList(sorted(tracks)))

    for k, v in sorted(tracks.items()):
        output.f.write(output.strTrackSessions((k, v)))

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
                write(outfunc(args.outfile), sessions)
            else:
                try:
                    write(outfunc(config.get('output files ' + mode, 'tracks')),
                          sessions)
                except config.NoOptionError:
                    pass
