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
from pocketprogram import Output
import times

prune = True

class TextOutput(Output):

    name = 'text'

    def __init__(self, fn):
        Output.__init__(self, fn)
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', Output.cleanup(self, text))

    def strSession(self, session, str):
        return '%s\n' % str

    def strIndex(self, session):
        return '[%s]' % session.index

    def strDuration(self, session):
        if session.duration != config.default_duration:
            return str(session.duration)
        else:
            return ''

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
        title = config.convention + ' Schedule'
        self.f.write(config.html_header % (title, '', title, config.source_date))
        dd = []
        for day in config.days:
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % ' - '.join(dd))
        self.curday = None

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return Output.cleanup(self, text).replace('&', '&amp;')

    def strSession(self, session, str):
        return '<p><a name="%s"></a>\n<dl>%s</dl></p>\n' % \
            (session.sessionid, str)

    def strDay(self, session):
        return '<p><a name="%s"></a></p>' % str(session.time.day)

    def strTime(self, session):
        return '<hr />\n<h3>%s %s</h3>\n' % \
            (str(session.time.day), str(session.time))

    def strTitle(self, session):
        return '<dt><b>%s</b> ' % self.cleanup(session.title)

    def strTracktype(self, session):
        return '<i>%s, %s</i> ' % (self.cleanup(session.track), session.type)

    def strType(self, session):
        return '<i>%s</i> ' % session.type

    def strDuration(self, session):
        return '<i>%s</i> ' % session.duration

    def strRoom(self, session):
        return '<i>%s</i></dt>\n' % session.room

    def strLevel(self, session):
        return '<i>%s</i>\n' % session.room.level

    def strRoomlevel(self, session):
        if session.room.level:
            return '<i>%s (%s)</i></dt>\n' % (session.room, session.room.level)
        else:
            return '<i>%s</i></dt>\n' % session.room

    def strDescription(self, session):
        if session.description:
            return '<dd>%s</dd>\n' % self.cleanup(session.description)
        else:
            return ''

    def strParticipants(self, session):
        if session.participants:
            pp = []
            for p in session.participants:
                #name = str(p)
                name = p.__str__()
                try:
                    name = '<a href="%s#%s">%s</a>' % \
                           (config.filenames['bios', 'html'],
                            re.sub(r'\W', '', name), name)
                except KeyError:
                    try:
                        name = '<a href="%s#%s">%s</a>' % \
                               (config.filenames['xref', 'html'],
                                re.sub(r'\W', '', name), name)
                    except KeyError:
                        None
                if p in session.moderators:
                    name += '&nbsp;(m)'
                pp.append(name)
            return '<dd><i>%s</i></dd>' % ', '.join(pp)
        else:
            return ''

    def strTags(self, session):
        if session.tags:
            return '<dd>%s</dd>\n' % ('#' + ', #'.join(session.tags))
        else:
            return ''

class XmlOutput(Output):

    name = 'xml'

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self.zeroDuration = times.Duration('0')
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<schedule>')

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
           session.duration != config.default_duration:
            return '<ss-duration>%s</ss-duration>' % session.duration
        else:
            return ''

    def strRoom(self, session):
        return '<ss-room>%s</ss-room>' % self.cleanup(str(session.room))

    def strLevel(self, session):
        return '<ss-room>%s</ss-room>' % self.cleanup(str(session.room.level))

    def strIcons(self, session):
        if (config.icons):
            icon = None
            for k, v in config.icons:
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
        if session.sessionid in config.nopartic:
            return ''
        str = Output.strParticipants(self, session)
        # Prune participants to save space.
        if str and prune and config.prune and eval(config.prune):
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
            str = output.fillTemplate(config.schema['day', output.name], session)
            output.f.write(str + '\n')
        except KeyError:
            None

    def writeTime(session):
        try:
            str = output.fillTemplate(config.schema['time', output.name], session)
            output.f.write(str + '\n')
        except KeyError:
            None

    def writeSession(session):
        str = output.fillTemplate(config.schema['schedule', output.name], session)
        # remove blank lines
        str = re.sub('\n+', '\n', str)
        str = re.sub('\n$', '', str)
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
    config.filereader.read(config.filenames['schedule', 'input'])

    if args.text:
        if args.outfile:
            write(TextOutput(args.outfile), config.sessions)
        elif ('schedule', 'text') in config.filenames:
            write(TextOutput(config.filenames['schedule', 'text']), config.sessions)

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile), config.sessions)
        elif ('schedule', 'html') in config.filenames:
            write(HtmlOutput(config.filenames['schedule', 'html']), config.sessions)

    if args.xml:
        if args.outfile:
            write(XmlOutput(args.outfile), config.sessions)
        elif ('schedule', 'xml') in config.filenames:
            write(XmlOutput(config.filenames['schedule', 'xml']), config.sessions)
