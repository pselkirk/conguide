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

"""Base class for output classes."""

import codecs
import copy
import re
import time

import config

class Output(object):
    """ Parent class for TextOutput etc. in schedule.py etc. """

    def __init__(self, fn, fd=None, codec='utf-8'):
        Output._readconfig(self)
        if fd:
            self.f = fd
            self.leaveopen = True
        else:
            #self.f = open(fn, 'w')
            self.f = codecs.open(fn, 'w', codec)
            self.leaveopen = False

    def _readconfig(self):
        Output._readconfig = lambda x: None
        # get some basic configuration from the config file
        Output.convention = config.get('convention', 'convention')
        Output.goh = {}
        for name in re.split(r',\s*', config.get('convention', 'goh')):
            Output.goh[name] = True
        try:
            Output.start = time.strptime(config.get('convention', 'start'), '%Y-%m-%d')
            # time.struct_time(tm_year=2014, tm_mon=1, tm_mday=17, tm_hour=0,
            # tm_min=0, tm_sec=0, tm_wday=4, tm_yday=17, tm_isdst=-1)
        except config.NoOptionError:
            pass

    def __del__(self):
        if not self.leaveopen:
            self.f.close()

    def cleanup(self, text):
        if text:
            # convert dashes
            # the much-misunderstood n-dash
            text = re.sub(r'(\d) *- *(\d)', r'\1'+u'\u2013'+r'\2', text)
            # m--dash, m -- dash, etc.
            text = re.sub(r' *-{2,} *', u'\u2014', text)
            # m - dash
            text = re.sub(r' +- +', u'\u2014', text)

            # convert quotes
            # right quote before abbreviated years and decades ('70s)
            text = re.sub(r'\'([0-9])', u'\u2019'+r'\1', text)
            # beginning single quote -> left
            text = re.sub(r'^\'', u'\u2018', text)
            # ending single quote -> right
            text = re.sub(r'\'$', u'\u2019', text)
            # left single quote
            text = re.sub(r'([^\w,.!?])\'(\w)', r'\1'+u'\u2018'+r'\2', text)
            # all remaining single quotes -> right
            text = re.sub(r'\'', u'\u2019', text)
            # beginning double quote -> left
            text = re.sub(r'^"', u'\u201c', text)
            # ending double quote -> right
            text = re.sub(r'"$', u'\u201d', text)
            # left double quote
            text = re.sub(r'([^\w,.!?])"(\w)', r'\1'+u'\u201c'+r'\2', text)
            # all remaining double quotes -> right
            text = re.sub(r'"', u'\u201d', text)

        return text

    # Fill a template (list of fields, with optional elements as sub-lists).
    # At each level, count the number of lexemes that expand into non-empty
    # strings. If nothing expands, return the empty string; else return a join
    # of the strings.
    #
    # XXX This treats the top-level list as an optional list, so if nothing
    # expands, it blows away any static text as well.
    def fillTemplate(self, template, session):
        fields = copy.deepcopy(template)
        ok = False
        for i, tag in enumerate(fields):
            if type(tag) is list:
                fields[i] = self.fillTemplate(tag, session)
                if fields[i]:
                    ok = True
            else:
                m = re.match(r'\((.*)\)', tag)
                if m:
                    parentheses = True
                    tag = m.group(1)
                else:
                    parentheses = False                    
                if re.match(r'\w+', tag):
                    try:
                        str = eval('self.str%s(session)' % tag.capitalize())
                    except AttributeError:
                        pass
                    else:
                        if str:
                            ok = True
                            if tag.isupper():
                                str = str.upper()
                            if parentheses:
                                str = '(' + str + ')'
                            try:
                                str = eval('self.markup%s(session, str)' % tag.capitalize())
                            except AttributeError:
                                pass
                            fields[i] = str
        if ok:
            return ''.join(fields)
        else:
            return ''

    def strIndex(self, session):
        return str(session.index)

    def strDay(self, session):
        return str(session.time.day)

    def strTime(self, session):
        return str(session.time)

    def strDuration(self, session):
        return str(session.duration)

    def strTitle(self, session):
        return self.cleanup(session.title)

    def strTrack(self, session):
        return self.cleanup(str(session.track))

    def strType(self, session):
        return self.cleanup(str(session.type))

    def strLevel(self, session):
        if session.room.level:
            return self.cleanup(str(session.room.level))
        else:
            return ''

    def strRoom(self, session):
        return self.cleanup(str(session.room))

    def strUsage(self, session):
        if session.room.usage:
            return self.cleanup(session.room.usage)
        else:
            return ''

    def strIcons(self, session):
        return ''

    def strDescription(self, session):
        return self.cleanup(session.description)

    def strParticipants(self, session):
        if session.participants:
            pp = []
            for p in session.participants:
                name = self.strParticipant(p)
                try:
                    name = self.markupParticipant(p, name)
                except AttributeError:
                    pass
                if p in session.moderators:
                    name += u'\u00A0(m)'
                pp.append(name)
            return ', '.join(pp)
        else:
            return ''

    def strParticipant(self, participant):
        return self.cleanup(participant.__str__())

    def strTags(self, session):
        try:
            if session.tags:
                return '#%s' % ', #'.join(session.tags)
            else:
                return ''
        except AttributeError:
            return ''

