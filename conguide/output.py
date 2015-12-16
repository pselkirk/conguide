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
import types

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

    def parenthesize(self, text):
        return '(%s)' % text if text else ''

    def parseTemplate(self, template):
        # parse a template string into a list of tokens,
        # with optional sections as sub-lists
        def xyzzy(list):
            tokens = []
            while list:
                a = list.pop(0)
                if not a:
                    # split() can insert empty tokens into the list
                    continue
                elif a == '[':
                    # begin optional section: process into sub-list
                    (toks, residue) = xyzzy(list)
                    tokens.append(toks)	# sub-list
                    list = residue
                elif a == ']':
                    # end optional section: return sub-list and remaining unprocessed list
                    break
                else:
                    # split token into words and non-words
                    tokens += re.split(r'([\w()-]+)', a)
            return (tokens, list)
        # split template into brackets and non-brackets
        list = re.split(r'([\[\]])', template)
        (tokens, unused) = xyzzy(list)
        return self.compileTemplate(tokens)

    def compileTemplate(self, template):
        newTemplate = []
        for token in template:
            if isinstance(token, list):
                token = self.compileTemplate(token)
            else:
                tokname = token
                m = re.match(r'\((.*)\)', token)
                if m:
                    parens = True
                    token = m.group(1)
                else:
                    parens = False
                if re.match(r'\w+', token):
                    codestring = 'self.str%s(session)' % token.capitalize()
                    if parens:
                        codestring = 'self.parenthesize(%s)' % codestring
                    codestring = 'self.markup%s(session, %s)' % (token.capitalize(), codestring)
                    token = (compile(codestring, '<string>', 'eval'), tokname)
            newTemplate.append(token)
        return newTemplate                    

    # Fill a template (list of fields, with optional elements as sub-lists).
    # At each level, count the number of lexemes that expand into non-empty
    # strings. If nothing expands, return the empty string; else return a join
    # of the strings.
    #
    # XXX This treats the top-level list as an optional list, so if nothing
    # expands, it blows away any static text as well.
    def fillTemplate(self, template, session):
        fields = []
        ok = False
        for token in template:
            if isinstance(token, list):
                # sub-list of optional elements
                value = self.fillTemplate(token, session)
                if value:
                    fields.append(value)
                    ok = True
            elif isinstance(token, tuple):
                # e.g. markupIndex(session, strIndex(session))
                # text is the literal token in the config template.
                # html markup causes us to try e.g. strDd()
                # XXX change '<text>' to process as literal above
                (code, text) = token
                try:
                    value = eval(code)
                    if value:
                        fields.append(value)
                        ok = True
                except AttributeError:
                    fields.append(text)
            else:
                fields.append(token)
        return ''.join(fields) if ok else ''

    def strIndex(self, session):
        return str(session.index)

    def markupIndex(self, session, text):
        return text

    def strDay(self, session):
        return str(session.time.day)

    def markupDay(self, session, text):
        return text

    def strTime(self, session):
        return str(session.time)

    def markupTime(self, session, text):
        return text

    def strDuration(self, session):
        return str(session.duration)

    def markupDuration(self, session, text):
        return text

    def strTitle(self, session):
        return self.cleanup(session.title)

    def markupTitle(self, session, text):
        return text

    def strTrack(self, session):
        return self.cleanup(str(session.track))

    def markupTrack(self, session, text):
        return text

    def strType(self, session):
        return self.cleanup(str(session.type))

    def markupType(self, session, text):
        return text

    def strLevel(self, session):
        return self.cleanup(str(session.room.level)) if session.room.level else ''

    def markupLevel(self, session, text):
        return text

    def strRoom(self, session):
        return self.cleanup(str(session.room))

    def markupRoom(self, session, text):
        return text

    def strUsage(self, session):
        return self.cleanup(session.room.usage) if session.room.usage else ''

    def markupUsage(self, session, text):
        return text

    def strIcons(self, session):
        return ''

    def markupIcons(self, session, text):
        return text

    def strDescription(self, session):
        return self.cleanup(session.description)

    def markupDescription(self, session, text):
        return text

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

    def markupParticipants(self, session, text):
        return text

    def strParticipant(self, participant):
        return self.cleanup(participant.__str__())

    def markupParticipant(self, participant, text):
        return text

    def strTags(self, session):
        try:
            return '#%s' % ', #'.join(session.tags) if session.tags else ''
        except AttributeError:
            return ''

    def markupTags(self, session, text):
        return text

