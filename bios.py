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
import participant
import pocketprogram

# XXX pylint really doesn't like this; is there a way of indicating that this is a base class?
class Output(pocketprogram.Output):

    def writeBio(self, participant):
        boldname = self.bold(participant)
        try:
            bio = participant.bio
        except AttributeError:
            if config.debug:
                print('not found: ' + participant.pubsname)
            bio = boldname
        else:
            firstname = participant.firstname
            lastname = participant.lastname
            pubsname = participant.pubsname
            fullname = '%s %s' % (firstname, lastname)
            first = re.sub(r' .*$', '', firstname)
            shortname = '%s %s' % (first, lastname)

            # Try to bold the name in the bio text.
            name = config.boldname.get(participant.pubsname)
            if name:
                if config.debug:
                    print('config override: ' + participant.pubsname)
                if name in bio:
                    bio = bio.replace(name, self.bold(name), 1)
                else:
                    bio = boldname + u'\u2014' + bio
            elif not participant.bio or participant.bio == 'NULL':
                if config.debug:
                    print('empty bio: ' + participant.pubsname)
                bio = boldname
            elif re.match(r'^(?=[a-z])', bio):
                if config.debug:
                    print('beginning lowercase: ' + participant.pubsname)
                bio = '%s %s' % (boldname, bio)
            elif pubsname in bio:
                if config.debug:
                    print('pubsname match: ' + participant.pubsname)
                bio = bio.replace(pubsname, boldname, 1)
            elif fullname in bio:
                if config.debug:
                    print('fullname match: ' + participant.pubsname)
                bio = bio.replace(fullname, boldname, 1)
            elif shortname in bio:
                if config.debug:
                    print('shortname match: ' + participant.pubsname)
                bio = bio.replace(shortname, boldname, 1)
            elif 'Dr. ' + lastname in bio:
                if config.debug:
                    print('Dr. match: ' + participant.pubsname)
                bio = bio.replace('Dr. ' + lastname, 'Dr. ' + boldname, 1)
            elif firstname in bio:
                if config.debug:
                    print('firstname match: ' + participant.pubsname)
                bio = bio.replace(firstname, boldname, 1)
            elif lastname in bio:
                if config.debug:
                    print('lastname match: ' + participant.pubsname)
                bio = bio.replace(lastname, boldname, 1)
            else:
                if config.debug:
                    print('no match: ' + participant.pubsname)
                bio = u'%s\u2014%s' % (boldname, bio)

        self.f.write(self.strBio(participant, bio))
        self.f.write(self.strSessions(participant))

class TextOutput(Output):

    def __init__(self, fn):
        Output.__init__(self, fn)
        import textwrap
        self.wrapper = textwrap.TextWrapper(76)

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
        title = config.convention + ' Program Participant Bios'
        self.f.write(config.html_header % (title, '', title, config.source_date))

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

        bio = re.sub(r'([a-zA-Z0-9\-_:\/\.~@]*)(www\.[a-zA-Z0-9\-_:\/\.~%]+|\.(com|org|net|biz)[a-zA-Z0-9\-_:\/\.~%]*)', repl, bio, flags=re.I)

        return '<a name="%s"></a>\n<p>%s ' % \
            (re.sub(r'\W', '', participant.__str__()), bio)

    def strSessions(self, participant):
        ss = []
        for s in participant.sessions:
            ss.append('<dd><a href="%s#%s">%s</a>\n</dd>' % \
                      (config.filenames['schedule', 'html'], s.sessionid, self.cleanup(s.title)))
        return '<i>\n<dl>\n%s\n</dl>\n</i></p>\n' % '\n'.join(ss)

class XmlOutput(Output):

    def __init__(self, fn, fd=None):
        Output.__init__(self, fn, fd)
        if not self.leaveopen:
            self.f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        self.f.write('<bios>')

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

if __name__ == '__main__':
    import argparse
    import cmdline

    # --infile in cmdline.py is pocketprogram.csv, but here we want the bios file
    parent = cmdline.cmdlineParser()
    parser = argparse.ArgumentParser(add_help=False, parents=[parent])
    parser.add_argument('--infile', action='store', help='input file name')
    parser.add_argument('--outfile', action='store', help='output file name')
    args = cmdline.cmdline(parser)
    (sessions, participants) = config.filereader.read(config.filenames['schedule', 'input'])
    if not args.infile:
        args.infile = config.filenames['bios', 'input']
    participants = config.filereader.read_bios(args.infile, participants)

    if args.text:
        if args.outfile:
            write(TextOutput(args.outfile), participants)
        else:
            write(TextOutput(config.filenames['bios', 'text']), participants)

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile), participants)
        else:
            write(HtmlOutput(config.filenames['bios', 'html']), participants)

    if args.xml:
        if args.outfile:
            write(XmlOutput(args.outfile), participants)
        else:
            write(XmlOutput(config.filenames['bios', 'xml']), participants)
