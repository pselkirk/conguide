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
import times

prune = False

class Output(pocketprogram.Output):

    def writeDayTime(self, session):
        self.f.write(self.strDayTime(session))

    def writeTime(self, session):
        self.f.write(self.strTime(session))

    def writeSession(self, session):
        # all defined in sub-classes
        self.f.write(self.strIndex(session))
        self.f.write(self.strTitle(session))
        self.f.write(self.strTrackType(session))
        self.f.write(self.strDuration(session))
        self.f.write(self.strRoom(session))
        self.f.write(self.strIcons(session))
        self.f.write(self.strDescription(session))
        self.f.write(self.strParticipants(session))

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', text)

    def strDayTime(self, session):
        return '%s %s ----------------\n\n' % (session.day, session.time)

    def strTime(self, session):
        return self.strDayTime(session)

    def strIndex(self, session):
        return '[%s] ' % session.sessionid

    def strTitle(self, session):
        return '%s\n' % self.cleanup(session.title)

    def strTrackType(self, session):
        return '\t%s, %s ' % (session.track, session.type)

    def strDuration(self, session):
        return '- %s ' % session.duration

    def strRoom(self, session):
        return '- %s\n' % session.room

    def strIcons(self, session):
        return ''

    def strDescription(self, session):
        return self.wrapper.fill(self.cleanup(session.description)) + '\n'

    def strParticipants(self, session):
        if session.participants:
            pp = []
            for p in session.participants:
                #name = str(p)
                name = p.__str__()
                if p == session.moderator:
                    name += ' (m)'
                pp.append(name)
            return self.wrapper.fill('{%s}' % ', '.join(pp)) + '\n\n'
        else:
            return '\n'

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        title = config.convention + ' Schedule'
        self.f.write(config.html_header % (title, '', title, config.source_date))
        dd = []
        for d in range(times.Day.index):
            day = config.day[d]
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % ' - '.join(dd))

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strDayTime(self, session):
        return '<p><a name="%s"></a></p>\n' % session.day + \
            self.strTime(session)

    def strTime(self, session):
        return '<hr />\n<h3>%s %s</h3>\n' % (session.day, session.time)

    def strIndex(self, session):
        return '<p><a name="%s"></a></p>\n' % session.sessionid

    def strTitle(self, session):
        return '<dl><dt><b>%s</b> ' % self.cleanup(session.title)

    def strTrackType(self, session):
        return '<i>&mdash; %s, %s</i> ' % (self.cleanup(session.track), session.type)

    def strDuration(self, session):
        return '<i>&mdash; %s</i> ' % session.duration

    def strRoom(self, session):
        return '<i>&mdash; %s</i></dt>\n' % session.room

    def strIcons(self, session):
        return ''

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
                name = '<a href="%s#%s">%s</a>' % (config.filenames['bios', 'html'], re.sub(r'\W', '', name), name)
                if p == session.moderator:
                    name += '&nbsp;(m)'
                pp.append(name)
            return '<dd><i>%s</i></dd></dl>\n' % ', '.join(pp)
        else:
            return '</dl>\n'

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<schedule>')

    def __del__(self):
        self.f.write('</schedule>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def strDayTime(self, session):
        # don't print the day header for the first day
        if session.day.index == 0:
            return self.strTime(session)
        else:
            # write '12:00am SATURDAY' instead of 'Saturday 12:00am'
            return '<ss-day>%s %s</ss-day>\n' % \
                (session.time, str(session.day).upper())

    def strTime(self, session):
        return '<ss-time>%s</ss-time>\n' % session.time

    def strIndex(self, session):
        return '<ss-session><ss-index>%d</ss-index>\t' % session.index

    def strTitle(self, session):
        # need a special tag for italics in titles, because weights
        title = re.sub(r'<(/?)i>', r'<\1i-title>', session.title)
        return '<ss-title>%s</ss-title>' % self.cleanup(title)

    def strTrackType(self, session):
        return ''

    def strDuration(self, session):
        if session.duration != config.default_duration:
            return '<ss-duration> (%s)</ss-duration>\t' % session.duration
        else:
            return '\t'

    def strRoom(self, session):
        return '<ss-room>%s</ss-room>\n' % session.room

    def strIcons(self, session):
        icon = None
        for k,v in config.icons:
            # compile() these in config
            #v = v.replace('track', 'session.track')
            #v = v.replace('type', 'session.type')
            #v = v.replace('sessionid', 'session.sessionid')
            #v = v.replace(' in ', ' in config.')
            #v = re.sub(r'room == (\'\w+\')',
            #           r'session.room == config.room[\1]', v)
            if eval(v):
                icon = k
                break
        if config.debug:
            if icon:
                print('%s %s' % (icon, session.title))
            else:
                print('  %s' % session.title)
        if icon:
            return '<ss-icon>%s</ss-icon>' % icon
        else:
            return ''

    def strDescription(self, session):
        if session.description:
            return '\t<ss-description>%s</ss-description>' % self.cleanup(session.description)
        else:
            return '\t'

    def strParticipants(self, session):
        pp = []
        if session.sessionid in config.nopartic:
            return ''
        for p in session.participants:
            #name = str(p)
            name = p.__str__()
            if p == session.moderator and len(session.participants) > 1:
                name += u'\u00A0(m)'
            pp.append(name)
        # Prune participants to save space.
        if prune and pp:
            # Remove "participants" from movies, and open gaming.
            if session.type == 'Movie' or \
               session.type == 'Projected Media' or \
               session.type == 'TV Show' or \
               session.type == 'Open Gaming' or \
               session.title.startswith('Reading: '):
                if config.debug:
                    print('%s: prune participants %s' % (session.title, ', '.join(pp)))
                return ''
        return ' <ss-participants>%s</ss-participants></ss-session>\n' % ', '.join(pp)

def write(output, sessions):
    curday = curtime = None
    for s in sessions:
        if s.day != curday:
            output.writeDayTime(s)
            curday = s.day
            curtime = s.time
        elif s.time != curtime:
            output.writeTime(s)
            curtime = s.time
        output.writeSession(s)

if __name__ == '__main__':
    import argparse
    import cmdline

#    (args, sessions, participants) = cmdline.cmdline(io=True)
    parent = cmdline.cmdlineParser(io=True)
    parser = argparse.ArgumentParser(add_help=False, parents=[parent])
    parser.add_argument('-p', '--prune', action='store_true',
                        help='prune participants to save space (xml only)')
    (args, sessions, participants) = cmdline.cmdline(parser)
    prune = args.prune

    if args.text:
        if args.outfile:
            write(TextOutput(args.outfile), sessions)
        else:
            write(TextOutput(config.filenames['schedule', 'text']), sessions)

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile), sessions)
        else:
            write(HtmlOutput(config.filenames['schedule', 'html']), sessions)

    if args.xml:
        if args.outfile:
            write(XmlOutput(args.outfile), sessions)
        else:
            write(XmlOutput(config.filenames['schedule', 'xml']), sessions)
