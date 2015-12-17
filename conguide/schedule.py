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

import conguide
import config
import output
from room import Room
from times import Day, Duration
import session

prune = False

class Output(output.Output):

    def __init__(self, fn, fd=None):
        output.Output.__init__(self, fn, fd)
        Output._readconfig(self)

    def _readconfig(self):
        Output._readconfig = lambda x: None
        try:
            Output.default_duration = Duration(config.get('schedule default duration', 'duration'))
        except (config.NoSectionError, config.NoOptionError):
            Output.default_duration = None
        Output.template = {}
        try:
            for key, value in config.items('schedule template'):
                Output.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

        Output.icons = []
        try:
            for char, expr in config.items('schedule icons'):
                #config.icons.append((char, expr))
                expr = expr.replace('track', 'session.track')
                expr = expr.replace('type', 'session.type')
                expr = expr.replace('sessionid', 'session.sessionid')
                expr = expr.replace(' in ', ' in Output.')
                expr = re.sub(r'room == (\'\w+\')',
                              r'session.room == Room.rooms[\1]', expr)
                Output.icons.append((char, expr))
        except config.NoSectionError:
            pass

        Output.presentation = []
        try:
            for (sessionid, unused) in config.items('schedule presentation'):
                Output.presentation.append(sessionid)
        except config.NoSectionError:
            pass

        Output.combat = []
        try:
            for (sessionid, unused) in config.items('schedule combat'):
                Output.combat.append(sessionid)
        except config.NoSectionError:
            pass

        Output.prune = None
        try:
            nn = []
            for k, expr in config.items('schedule prune participants'):
                if k == 'type':
                    for n in re.split(r',\s*', expr):
                        nn.append('session.type == \'%s\'' % n)
                elif k == 'title':
                    for n in re.split(r',\s*', expr):
                        nn.append('session.title.startswith(\'%s\')' % n)
            Output.prune = ' or '.join(nn)
        except config.NoSectionError:
            pass

        Output.nopartic = []
        try:
            for (sessionid, unused) in config.items('schedule no participants'):
                Output.nopartic.append(sessionid)
        except config.NoSectionError:
            pass

        Output.nodescr = []
        try:
            for (sessionid, unused) in config.items('schedule no description'):
                Output.nodescr.append(sessionid)
        except config.NoSectionError:
            pass

class TextOutput(Output):

    name = 'text'

    def __init__(self, fn=None):
        Output.__init__(self, fn)
        self._readconfig()
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('schedule template text'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', Output.cleanup(self, text))

    def markupSession(self, session, text):
        return '%s\n' % text

    def markupIndex(self, session, text):
        return '[%s]' % text

    #def strDuration(self, session):
    #    return str(session.duration) if session.duration != self.default_duration else ''

    def strTitle(self, session):
        return self.wrapper.fill(self.cleanup(session.title))

    def strDescription(self, session):
        return self.wrapper.fill(self.cleanup(session.description)) if session.description else ''

    def strParticipants(self, session):
        return self.wrapper.fill(Output.strParticipants(self, session))

    def strTags(self, session):
        return self.wrapper.fill(Output.strTags(self, session))

class HtmlOutput(Output):

    name = 'html'

    def __init__(self, fn=None):
        Output.__init__(self, fn)
        self._readconfig()
        title = self.convention + ' Schedule'
        self.f.write(config.html_header % (title, '', title, config.source_date))
        dd = []
        for day in Day.days:
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % ' - '.join(dd))
        self.curday = None

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('schedule template html'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert ampersand
        text = text.replace('&', '&amp;')
        # convert line breaks
        text = text.replace('\n', '<br/>\n')
        return text

    def markupSession(self, session, text):
        return '<p><a name="%s"></a>\n<dl>%s</dl></p>' % (session.sessionid, text)

    def markupParticipant(self, participant, name):
        try:
            href = config.get('output files html', 'bios')
        except config.NoOptionError:
            try:
                href = config.get('output files html', 'xref')
            except config.NoOptionError:
                href = None
        return '<a href="%s#%s">%s</a>' % (href, re.sub(r'\W', '', name), name) if href else name

class XmlOutput(Output):

    name = 'xml'

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self._readconfig()
        self.zeroDuration = Duration('0')
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<schedule>')

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('schedule template xml'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</schedule>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def markupSession(self, session, text):
        return '<ss-session>%s</ss-session>' % text if text else ''

    def markupDay(self, session, text):
        return '<ss-day>%s</ss-day>' % text if text else ''

    def markupTime(self, session, text):
        return '<ss-time>%s</ss-time>' % text if text else ''

    def strIndex(self, session):
        return str(session.index) if session.index else ''

    def markupIndex(self, session, text):
        return '<ss-index>%s</ss-index>' % text if text else ''

    def strTitle(self, session):
        # need a special tag for italics in titles, because weights
        return re.sub(r'<(/?)i>', r'<\1i-title>', Output.strTitle(self, session))

    def markupTitle(self, session, text):
        return '<ss-title>%s</ss-title>' % text if text else ''

    def strDuration(self, session):
        if session.duration != self.zeroDuration and \
           session.duration != self.default_duration:
            return str(session.duration)
        else:
            return ''

    def markupDuration(self, session, text):
        return '<ss-duration>%s</ss-duration>' % text if text else ''

    def markupRoom(self, session, text):
        return '<ss-room>%s</ss-room>' % text if text else ''

    def markupLevel(self, session, text):
        return '<ss-room>%s</ss-room>' % text if text else ''

    def strIcon(self, session):
        if self.icons:
            icon = None
            for k, v in self.icons:
                if eval(v):
                    icon = k
                    break
            if icon:
                return icon
        return ''

    def markupIcon(self, session, text):
        return '<ss-icon>%s</ss-icon>' % text if text else ''

    def markupDescription(self, session, text):
        return '<ss-description>%s</ss-description>' % text if text else ''

    def strParticipants(self, session):
        if session.sessionid in self.nopartic:
            return ''
        # Prune participants to save space.
        if prune and self.prune and eval(self.prune):
            if config.debug:
                pp = []
                for p in session.participants:
                    pp.append(p.__str__())
                print('%s: prune participants %s' % \
                      (session.title, ', '.join(pp)))
            return ''
        return Output.strParticipants(self, session)

    def markupParticipants(self, session, text): 
        return '<ss-participants>%s</ss-participants>' % text if text else ''

    def strTags(self, session):
        return '<ss-tags>%s</ss-tags>' % ('#' + ', #'.join(session.tags)) if session.tags else ''

def write(output, sessions):

    def writeDay(session):
        try:
            text = output.fillTemplate(output.template['day'], session)
            output.f.write(text + '\n')
        except KeyError:
            pass

    def writeTime(session):
        try:
            text = output.fillTemplate(output.template['time'], session)
            output.f.write(text + '\n')
        except KeyError:
            pass

    def writeSession(session):
        text = output.fillTemplate(output.template['session'], session)
        # remove blank lines	# XXX make this a config option
        #text = re.sub('\n+', '\n', text)
        #text = re.sub('\n$', '', text)
        text = output.markupSession(session, text)
        output.f.write(text + '\n')

    curday = curtime = None
    for s in sessions:
        if s.time.day != curday:
            writeDay(s)
            curday = s.time.day
            curtime = s.time
        elif s.time != curtime:
            writeTime(s)
            curtime = s.time
        writeSession(s)

def add_args(subparsers):
    parser = subparsers.add_parser('schedule', add_help=False,
                                   help='generate the "TV Guide" style listing')
    conguide.add_modes(parser, ['t', 'h', 'x', 'a'])
    conguide.add_io(parser)
    parser.add_argument('--no-prune', dest='prune', action='store_false',
                                 help='don\'t prune participants to save space (xml only)')
    parser.set_defaults(func=main)

def main(args):
    global prune
    if hasattr(args, 'prune'):
        prune = args.prune
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
                    write(outfunc(config.get('output files ' + mode, 'schedule')),
                          sessions)
                except config.NoOptionError:
                    pass
