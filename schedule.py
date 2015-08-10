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

prune = True

class Output(pocketprogram.Output):

    def strSession(self, session, str):
        return str

    def strDay(self, session):
        return str(session.time.day)

    def strTime(self, session):
        return str(session.time)

    def strIndex(self, session):
        return str(session.index)

    def strTitle(self, session):
        return self.cleanup(session.title)

    def strTrack(self, session):
        return str(self.track)
    
    def strType(self, session):
        return str(self.type)

    def strDuration(self, session):
        return str(session.duration)

    def strLevel(self, session):
        return str(session.room.level)

    def strRoom(self, session):
        return str(session.room)

    def strIcons(self, session):
        return ''

    def strDescription(self, session):
        return str(session.description)

    def strParticipants(self, session):
        if session.participants:
            pp = []
            for p in session.participants:
                name = str(p)
                try:
                    if p in session.moderator:
                        name += ' (m)'
                except AttributeError:
                    None
                pp.append(name)
            return ', '.join(pp)
        else:
            return ''

    def strTags(self, session):
        try:
            if session.tags:
                return '#%s' % ', #'.join(session.tags)
            else:
                return ''
        except AttributeError:
            return ''

    def cleanup(self, field):
        if field:
            # convert dashes
            field = re.sub(r'(\d) *- *(\d)', r'\1'+u'\u2013'+r'\2', field) # the much-misunderstood n-dash
            field = re.sub(r' *-{2,} *', u'\u2014', field)   # m--dash, m -- dash, etc.
            field = re.sub(r' +- +', u'\u2014', field)       # m - dash
            field = re.sub(r' +\u2014 +', u'\u2014', field, flags=re.U)

            # right quote before abbreviated years and decades ('70s)
            field = re.sub(r'\'([0-9])', u'\u2019'+r'\1', field)

            # convert quotes
            field = re.sub(r'^\'', u'\u2018', field) # beginning single quote -> left
            field = re.sub(r'\'$', u'\u2019', field) # ending single quote -> right
            field = re.sub(r'([^\w,.!?])\'(\w)', r'\1'+u'\u2018'+r'\2', field) # left single quote
            field = re.sub(r'\'', u'\u2019', field)  # all remaining single quotes -> right

            field = re.sub(r'^"', u'\u201c', field)  # beginning double quote -> left
            field = re.sub(r'"$', u'\u201d', field)  # ending double quote -> right
            field = re.sub(r'([^\w,.!?])"(\w)', r'\1'+u'\u201c'+r'\2', field) # left double quote
            field = re.sub(r'"', u'\u201d', field)   # all remaining double quotes -> right

        return field

    def writeDay(self, session):
        try:
            str = config.schema['time', self.__type__]
        except KeyError:
            try:
                str = config.schema['time', 'all']
            except KeyError:
                return
        str = re.sub('{day}', self.strDay(session), str)
        str = re.sub('{DAY}', self.strDay(session).upper(), str)
        str = re.sub('{time}', self.strTime(session), str)
        self.f.write(str)

    def writeTime(self, session):
        try:
            str = config.schema['time', self.__type__]
        except KeyError:
            try:
                str = config.schema['time', 'all']
            except KeyError:
                return
        str = re.sub('{time}', self.strTime(session), str)
        self.f.write(str)

    def writeSession(self, session):
        try:
            str = config.schema['schedule', self.__type__]
        except KeyError:
            str = config.schema['schedule', 'all']

        val = {}
        val['index'] = self.strIndex(session)
        val['day'] = self.strDay(session)
        val['time'] = self.strTime(session)
        val['duration'] = self.strDuration(session)
        val['room'] = self.strRoom(session)
        val['level'] = self.strLevel(session)
        val['icons'] = self.strIcons(session)
        val['title'] = self.strTitle(session)
        val['description'] = self.strDescription(session)
        val['participants'] = self.strParticipants(session)
        try:
            val['tags'] = self.strTags(session)
        except AttributeError:
            # used in sasquan, not in arisia
            None

        # deal with optional elements
        m = re.search(r'\[(.*?)\]', str)
        while m:
            n = re.search(r'\{(.*?)\}', m.group(1))
            if val[n.group(1)]:
                repl = m.group(1)[:n.start()] + val[n.group(1)] + m.group(1)[n.end():]
            else:
                repl = ''
            str = str[:m.start()] + repl + str[m.end():]
            m = re.search(r'\[(.*?)\]', str)
        # deal with regular elements
        for k,v in val.items():
            str = str.replace('{%s}' % k, v)

        str = re.sub('\n+', '\n', str)
        str = self.strSession(session, str)
        self.f.write(str)

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__type__ = 'text'
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', text)

    def strSession(self, session, str):
        return '%s\n' % str

    def strIndex(self, session):
        return '[%s]' % session.index

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

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.__type__ = 'html'
        title = config.convention + ' Schedule'
        self.f.write(config.html_header % (title, '', title, config.source_date))
        dd = []
        for day in config.day:
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % ' - '.join(dd))
        self.curday = None

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert ampersand
        return text.replace('&', '&amp;')

    def strSession(self, session, str):
        return '<p><a name="%s"></a></p>\n<p><dl>%s</dl></p>\n' % (session.sessionid, str)

    def strDay(self, session):
        day = str(session.time.day)
        if day != self.curday:
            self.curday = day
            return '<a name="%s">%s</a>' % (day, day)
        else:
            return day

    def strTitle(self, session):
        return '<dt><b>%s</b> ' % self.cleanup(session.title)

    def strTrackType(self, session):
        return '<i>&mdash; %s, %s</i> ' % (self.cleanup(session.track), session.type)

    def strDuration(self, session):
        return '<i>&mdash; %s</i> ' % session.duration

    def strRoom(self, session):
        return '<i>&mdash; %s</i></dt>\n' % session.room

    def strLevel(self, session):
        return '<i>&mdash; %s</i></dt>\n' % session.room.level

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
                if p in session.moderator:
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

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self.__type__ = 'xml'
        self.zeroDuration = times.Duration('0')
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<schedule>')

    def __del__(self):
        self.f.write('</schedule>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert ampersand
        return text.replace('&', '&amp;')

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
            if icon:
                return '<ss-icon>%s</ss-icon>' % icon
        return ''

    def strDescription(self, session):
        if session.description:
            return '<ss-description>%s</ss-description>' % self.cleanup(session.description)
        else:
            return ''

    def strParticipants(self, session):
        if session.participants and session.sessionid not in config.nopartic:
            pp = []
            for p in session.participants:
                #name = str(p)
                name = p.__str__()
                if p in session.moderator:
                    name += u'\u00A0(m)'
                pp.append(name)
            # Prune participants to save space.
            if prune and pp:
                if config.prune and eval(config.prune):
                    if config.debug:
                        print('%s: prune participants %s' % (session.title, ', '.join(pp)))
                    return ''
            return '<ss-participants>%s</ss-participants>' % ', '.join(pp)
        else:
            return ''

    def strTags(self, session):
        if session.tags:
            return '<ss-tags>%s</ss-tags>' % ('#' + ', #'.join(session.tags))
        else:
            return ''

def write(output, sessions):
    curday = curtime = None
    for s in sessions:
        if s.time.day != curday:
            output.writeDay(s)
            curday = s.time.day
            curtime = s.time
        elif s.time != curtime:
            output.writeTime(s)
            curtime = s.time
        output.writeSession(s)

if __name__ == '__main__':
    import argparse

    import cmdline

    parent = cmdline.cmdlineParser(io=True)
    parser = argparse.ArgumentParser(add_help=False, parents=[parent])
    parser.add_argument('--no-prune', dest='prune', action='store_false',
                        help='don\'t prune participants to save space (xml only)')
    args = cmdline.cmdline(parser, io=True)
    prune = args.prune
    (sessions, participants) = config.filereader.read(config.filenames['schedule', 'input'])

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
