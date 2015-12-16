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
import participant
import session

class Output(output.Output):

    def __init__(self, fn, fd=None):
        output.Output.__init__(self, fn, fd)
        Output._readconfig(self)

    def _readconfig(self):
        Output._readconfig = lambda x: None
        Output.template = {}
        try:
            for key, value in config.items('bios template'):
                Output.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass
        Output.boldnames = {}
        try:
            for (name, rename) in config.items('bios bold name'):
                Output.boldnames[name] = rename
        except config.NoSectionError:
            pass

    def writeBio(self, participant):
        boldname = self.bold(participant)
        try:
            bio = participant.bio
        except AttributeError:
            if config.debug:
                print('not found: ' + participant.name)
            bio = boldname
        else:
            firstname = participant.firstname
            lastname = participant.lastname
            pubsname = participant.name
            fullname = '%s %s' % (firstname, lastname)
            first = re.sub(r' .*$', '', firstname)
            shortname = '%s %s' % (first, lastname)

            # Try to bold the name in the bio text.
            name = self.boldnames.get(participant.name)
            if name:
                if config.debug:
                    print('config override: ' + participant.name)
                if name in bio:
                    bio = bio.replace(name, self.bold(name), 1)
                else:
                    bio = boldname + u'\u2014' + bio
            elif not participant.bio or participant.bio == 'NULL':
                if config.debug:
                    print('empty bio: ' + participant.name)
                bio = boldname
            elif re.match(r'^(?=[a-z])', bio):
                if config.debug:
                    print('beginning lowercase: ' + participant.name)
                bio = '%s %s' % (boldname, bio)
            elif pubsname in bio:
                if config.debug:
                    print('pubsname match: ' + participant.name)
                bio = bio.replace(pubsname, boldname, 1)
            elif fullname in bio:
                if config.debug:
                    print('fullname match: ' + participant.name)
                bio = bio.replace(fullname, boldname, 1)
            elif shortname in bio:
                if config.debug:
                    print('shortname match: ' + participant.name)
                bio = bio.replace(shortname, boldname, 1)
            elif 'Dr. ' + lastname in bio:
                if config.debug:
                    print('Dr. match: ' + participant.name)
                bio = bio.replace('Dr. ' + lastname, 'Dr. ' + boldname, 1)
            elif firstname in bio:
                if config.debug:
                    print('firstname match: ' + participant.name)
                bio = bio.replace(firstname, boldname, 1)
            elif lastname in bio:
                if config.debug:
                    print('lastname match: ' + participant.name)
                bio = bio.replace(lastname, boldname, 1)
            else:
                if config.debug:
                    print('no match: ' + participant.name)
                bio = u'%s\u2014%s' % (boldname, bio)

        self.f.write(self.strBio(participant, bio))
        self.f.write(self.strSessions(participant))

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

    def _readconfig(self):
        TextOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('bios template text'):
                TextOutput.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def cleanup(self, text):
        # convert italics
        return re.sub(r'</?i>', '*', text)

    def bold(self, text):
        return '**%s**' % text

    def strBio(self, participant, bio):
        return self.wrapper.fill(self.cleanup(bio)) + '\n'

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append(s.sessionid)
        return '{%s}\n\n' % ', '.join(ss)

class HtmlOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        title = self.convention + ' Program Participant Bios'
        self.f.write(config.html_header % (title, '', title,
                                           config.source_date))

    def _readconfig(self):
        HtmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('bios template html'):
                HtmlOutput.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def bold(self, text):
        return '<b>%s</b>' % text

    def strBio(self, participant, bio):
        bio = self.cleanup(bio)

        # add a link to the participant's website or email address
        def repl(matchobj):
            url = matchobj.group(0)
            (url, period) = re.subn(r'\.$', '', url)
            if '@' in  url:
                fullurl = 'mailto://' + url
            elif not re.match(r'^http', url, flags=re.I):
                fullurl = 'http://' + url
            else:
                fullurl = url
            string = '<a href="%s">%s</a>' % (fullurl, url)
            if period:
                string += '.'
            return string

        bio = re.sub(r'([a-zA-Z0-9\-_:\/\.~@]*)' + \
                     r'(www\.[a-zA-Z0-9\-_:\/\.~%]+|\.(com|org|net|biz)' + \
                     r'[a-zA-Z0-9\-_:\/\.~%]*)',
                     repl, bio, flags=re.I)

        return '<a name="%s"></a>\n<p>%s ' % \
            (re.sub(r'\W', '', participant.__str__()), bio)

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append('<dd><a href="%s#%s">%s</a>\n</dd>' % \
                      (config.get('output files html', 'schedule'),
                       s.sessionid, self.cleanup(s.title)))
        return '<i>\n<dl>\n%s\n</dl>\n</i></p>\n' % '\n'.join(ss)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        self._readconfig()
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<bios>')

    def _readconfig(self):
        XmlOutput.template = copy.copy(Output.template)
        try:
            for key, value in config.items('bios template xml'):
                XmlOutput.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

    def __del__(self):
        self.f.write('</bios>\n')
        if not self.leaveopen:
            Output.__del__(self)

    def cleanup(self, text):
        # convert ampersand
        return text.replace('&', '&amp;')

    def bold(self, text):
        return '<bold>%s</bold>' % text

    def strBio(self, participant, bio):
        # suppress empty bios
        if bio == self.bold(participant.__str__()):
            return ''
        else:
            return '<bio>%s</bio>\n' % self.cleanup(bio)

    def strSessions(self, participant):
        return ''

def write(output, participants):
    for p in sorted(participants.values()):
        output.writeBio(p)

def main(args):
    (sessions, participants) = session.read(config.get('input files', 'schedule'))
    fn = args.infile or config.get('input files', 'bios')
    participant.read(fn, participants)
    if args.all:
        args.text = True
        args.html = True
        args.xml = True
    for mode in ('text', 'html', 'xml'):
        if eval('args.' + mode):
            outfunc = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(outfunc(args.outfile), participants)
            else:
                try:
                    write(outfunc(config.get('output files ' + mode, 'bios')),
                          participants)
                except config.NoOptionError:
                    pass
