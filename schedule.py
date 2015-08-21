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
from times import Day, Duration
import session

prune = True

class Output(pocketprogram.Output):

    def __init__(self, fn, fd=None):
        pocketprogram.Output.__init__(self, fn, fd)
        self.__readconfig()

    def __readconfig(self):
        Output.__readconfig = lambda x: None
        try:
            Output.default_duration = Duration(config.get('schedule default duration', 'duration'))
        except (config.NoSectionError, config.NoOptionError):
            pass
        Output.template = {}
        try:
            for key, value in config.items('schedule template'):
                Output.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

        Output.icons = []
        try:
            for char, expr in config.items('schedule icons'):
                #config.icons.append((char, expr))
                expr = expr.replace('track', 'session.track')
                expr = expr.replace('type', 'session.type')
                expr = expr.replace('sessionid', 'session.sessionid')
                expr = expr.replace(' in ', ' in config.')
                expr = re.sub(r'room == (\'\w+\')',
                              r'session.room == config.rooms[\1]', expr)
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

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

    def __readconfig(self):
        TextOutput.__readconfig = lambda x: None
        TextOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('schedule template text'):
                TextOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', Output.cleanup(self, text))

    def strSession(self, session, str):
        return '%s\n' % str

    def strIndex(self, session):
        return '[%s]' % session.index

    #def strDuration(self, session):
    #    if session.duration != self.default_duration:
    #        return str(session.duration)
    #    else:
    #        return ''

    def strTitle(self, session):
        return self.wrapper.fill(self.cleanup(session.title))

    def strDescription(self, session):
        if session.description:
            return self.wrapper.fill(self.cleanup(session.description))
        else:
            return ''

    def strParticipants(self, session):
        return self.wrapper.fill(Output.strParticipants(self, session))

    def strTags(self, session):
        return self.wrapper.fill(Output.strTags(self, session))

class HtmlOutput(Output):

    name = 'html'

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__readconfig()
        title = self.convention + ' Schedule'
        self.f.write(config.html_header % (title, '', title, config.source_date))
        dd = []
        for day in Day.days:
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % ' - '.join(dd))
        self.curday = None

    def __readconfig(self):
        HtmlOutput.__readconfig = lambda x: None
        HtmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('schedule template html'):
                HtmlOutput.template[key] = config.parseTemplate(value)
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

    def strSession(self, session, str):
        return '<p><a name="%s"></a>\n<dl>%s</dl></p>\n' % \
            (session.sessionid, str)

    def strTrack(self, session):
        return self.cleanup(session.track)

    def strParticipants(self, session):
        if session.participants:
            pp = []
            for p in session.participants:
                name = p.__str__()
                try:
                    href = config.get('output files html', 'bios')
                except config.NoOptionError:
                    try:
                        href = config.get('output files html', 'xref')
                    except config.NoOptionError:
                        href = None
                if href:
                    name = '<a href="%s#%s">%s</a>' % \
                           (href, re.sub(r'\W', '', name), name)
                if p in session.moderators:
                    name += '&nbsp;(m)'
                pp.append(name)
            return ', '.join(pp)
        else:
            return ''

class XmlOutput(Output):

    name = 'xml'

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self.__readconfig()
        self.zeroDuration = Duration('0')
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<schedule>')

    def __readconfig(self):
        XmlOutput.__readconfig = lambda x: None
        XmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('schedule template xml'):
                XmlOutput.template[key] = config.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</schedule>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def strSession(self, session, str):
        return '<ss-session>%s</ss-session>' % str

    def strDay(self, session):
        return '<ss-day>%s</ss-day>' % session.time.day

    def strTime(self, session):
        return '<ss-time>%s</ss-time>' % session.time

    def strIndex(self, session):
        if (session.index):
            return '<ss-index>%d</ss-index>' % session.index
        else:
            return ''

    def strTitle(self, session):
        # need a special tag for italics in titles, because weights
        title = re.sub(r'<(/?)i>', r'<\1i-title>', session.title)
        return '<ss-title>%s</ss-title>' % self.cleanup(title)

    def strDuration(self, session):
        if session.duration != self.zeroDuration and \
           session.duration != self.default_duration:
            return '<ss-duration>%s</ss-duration>' % session.duration
        else:
            return ''

    def strRoom(self, session):
        return '<ss-room>%s</ss-room>' % self.cleanup(str(session.room))

    def strLevel(self, session):
        if session.room.level:
            return '<ss-room>%s</ss-room>' % self.cleanup(str(session.room.level))
        else:
            return ''

    def strIcon(self, session):
        if self.icons:
            icon = None
            for k, v in self.icons:
                if eval(v):
                    icon = k
                    break
            if icon:
                return '<ss-icon>%s</ss-icon>' % icon
        return ''

    def strDescription(self, session):
        if session.description:
            return '<ss-description>%s</ss-description>' % \
                self.cleanup(session.description)
        else:
            return ''

    def strParticipants(self, session):
        if session.sessionid in self.nopartic:
            return ''
        str = Output.strParticipants(self, session)
        # Prune participants to save space.
        if str and prune and self.prune and eval(self.prune):
            if config.debug:
                pp = []
                for p in session.participants:
                    pp.append(p.__str__())
                print('%s: prune participants %s' % \
                      (session.title, ', '.join(pp)))
            return ''
        return '<ss-participants>%s</ss-participants>' % str

    def strTags(self, session):
        if session.tags:
            return '<ss-tags>%s</ss-tags>' % ('#' + ', #'.join(session.tags))
        else:
            return ''

def write(output, sessions):

    def writeDay(session):
        try:
            str = output.fillTemplate(output.template['day'], session)
            output.f.write(str + '\n')
        except KeyError:
            pass

    def writeTime(session):
        try:
            str = output.fillTemplate(output.template['time'], session)
            output.f.write(str + '\n')
        except KeyError:
            pass

    def writeSession(session):
        str = output.fillTemplate(output.template['session'], session)
        # remove blank lines	# XXX make this a config option
        #str = re.sub('\n+', '\n', str)
        #str = re.sub('\n$', '', str)
        str = output.strSession(session, str)
        output.f.write(str + '\n')

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

if __name__ == '__main__':
    import argparse

    import cmdline

    parent = cmdline.cmdlineParser(io=True)
    parser = argparse.ArgumentParser(add_help=False, parents=[parent])
    parser.add_argument('--no-prune', dest='prune', action='store_false',
                        help='don\'t prune participants to save space (xml only)')
    args = cmdline.cmdline(parser, io=True)
    prune = args.prune
    (sessions, participants) = session.read(config.get('input files', 'schedule'))

    for mode in ('text', 'html', 'xml'):
        if eval('args.' + mode):
            output = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(output(args.outfile), sessions)
            else:
                try:
                    write(output(config.get('output files ' + mode, 'schedule')),
                          sessions)
                except config.NoOptionError:
                    pass
