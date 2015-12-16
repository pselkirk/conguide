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

import argparse

import config
import session

if not config.PY3:
    str = unicode

def main(args):
    if not args.files or len(args.files) > 2:
        print('specify one or two data files')
        exit(1)

    if args.bios:
        changes_bios(args)
        return
    
    if len(args.files) == 1:
        args.files.append(config.get('input files', 'schedule'))
    
    sessions = [{}, {}]
    participants = [{}, {}]
    
    def read(fn):
        if not config.quiet:
            print('---- %s ----' % fn)
        (sessions, participants) = session.read(fn, reset=True)
        session_hash = {}
        for s in sessions:
            if args.by_title:
                s.sessionid = s.title
            session_hash[s.sessionid] = s
        return (session_hash, participants)
    
    (sessions[0], participants[0]) = read(args.files[0])
    (sessions[1], participants[1]) = read(args.files[1])
    
    def session_header(s):
        string = ''
        if args.sessionid:
            string = '%s: ' % s.sessionid
        string += '%s %s %s' % (s.time.day, s.time, s.title)
        return string
    
    new = []
    cancelled = []
    ch_time = []
    ch_duration = []
    ch_room = []
    ch_track = []
    ch_type = []
    ch_title = []
    ch_description = []
    ch_participants = []
    
    for s in sorted(sessions[1].values()):
        if not s.sessionid in sessions[0]:
            new.append(session_header(s))
    
    for s in sorted(sessions[0].values()):
        sh = session_header(s)
        if config.debug:
            print(sh)
        s1 = sessions[1].get(s.sessionid)
        if not s1:
            cancelled.append(sh)
            continue
        #if s1.time.day != s.time.day or s1.time != s.time:
        if s1.time != s.time:
            ch_time.append('%s -> %s %s' % (sh, s1.time.day, s1.time))
        if s1.duration != s.duration:
            ch_duration.append('%s: %s -> %s' % (sh, s.duration, s1.duration))
        if s1.room != s.room:
            ch_room.append('%s: %s -> %s' % (sh, s.room, s1.room))
        if s1.track != s.track:
            ch_track.append('%s: %s -> %s' % (sh, s.track, s1.track))
        if s1.type != s.type:
            ch_type.append('%s: %s -> %s' % (sh, s.type, s1.type))
        if s1.title != s.title:
            ch_title.append('%s -> %s' % (sh, s1.title))
        if s1.description != s.description:
            if args.verbose:
                ch_description.append('%s:\n\t%s\n->\n\t%s' % \
                                      (sh, s.description, s1.description))
            else:
                ch_description.append(sh)
        cp = []
        if s1.participants != s.participants:
            add = []
            for p in s1.participants:
                if not p in s.participants:
                    add.append(str(p))
            if add:
                cp.append('add %s' % ', '.join(add))
            remove = []
            for p in s.participants:
                if not p in s1.participants:
                    remove.append(str(p))
            if remove:
                cp.append('remove %s' % ', '.join(remove))
            addmod = []
            for p in s1.moderators:
                if not p in s.moderators:
                    addmod.append(str(p))
            if addmod:
                cp.append('add moderator %s' % ', '.join(addmod))
            removemod = []
            for p in s.moderators:
                if not p in s1.moderators:
                    removemod.append(str(p))
            if removemod:
                cp.append('remove moderator %s' % ', '.join(removemod))
        if cp:
            ch_participants.append('%s: %s' % (sh, '; '.join(cp)))
    
    if new:
        print('\nnew sessions (%d):\n%s' % (len(new), '\n'.join(new)))
    if cancelled:
        print('\ncancelled sessions (%d):\n%s' % \
              (len(cancelled), '\n'.join(cancelled)))
    if ch_time:
        print('\ntime changes (%d):\n%s' % \
              (len(ch_time), '\n'.join(ch_time)))
    if ch_room:
        print('\nroom changes (%d):\n%s' % \
              (len(ch_room), '\n'.join(ch_room)))
    if ch_track:
        print('\ntrack changes (%d):\n%s' % \
              (len(ch_track), '\n'.join(ch_track)))
    if ch_type:
        print('\ntype changes (%d):\n%s' % \
              (len(ch_type), '\n'.join(ch_type)))
    if ch_title:
        print('\ntitle changes (%d):\n%s' % \
              (len(ch_title), '\n'.join(ch_title)))
    if ch_description:
        print('\ndescription changes (%d):\n%s' % \
              (len(ch_description), '\n'.join(ch_description)))
    if ch_participants:
        print('\nparticipant changes (%d):\n%s' % \
              (len(ch_participants), '\n'.join(ch_participants)))

def changes_bios(args):
    import participant

    if len(args.files) == 1:
        args.files.append(config.get('input files', 'bios'))

    def read(fn):
        participants = {}
        for p in participant.read(fn, {}).values():
            participants[p.badgeid] = p
        return participants

    config.quiet = True
    participants = [read(args.files[0]), read(args.files[1])]

    added = []
    removed = []
    ch_name = []
    ch_pubsname = []
    ch_bio = []

    def pheader(p):
        name = '%s %s' % (p.firstname, p.lastname)
        string = '%s: %s' % (p.badgeid, name)
        if p.name != name:
            string += ' (%s)' % p.name
        return string

    for p in sorted(participants[1].values()):
        if not p.badgeid in participants[0]:
            added.append(pheader(p))

    for p in sorted(participants[0].values()):
        ph = pheader(p)
        if args.debug:
            print(ph)
        p1 = participants[1].get(p.badgeid)
        if not p1:
            removed.append(ph)
            continue
        if p1.firstname != p.firstname or p1.lastname != p.lastname:
            ch_name.append('%s -> %s %s' % (ph, p1.firstname, p1.lastname))
        if p1.name != p.name:
            ch_pubsname.append('%s: %s -> %s' % (ph, p.name, p1.name))
        if p1.bio != p.bio:
            if args.verbose:
                ch_bio.append('%s: %s -> %s' % (ph, p.bio, p1.bio))
            else:
                ch_bio.append(ph)

    if added:
        print('\nadded participants:\n%s' % '\n'.join(added))
    if removed:
        print('\nremoved participants:\n%s' % '\n'.join(removed))
    if ch_name:
        print('\nname changes:\n%s' % '\n'.join(ch_name))
    if ch_pubsname:
        print('\npubsname changes:\n%s' % '\n'.join(ch_pubsname))
    if ch_bio:
        print('\nbio changes:\n%s' % '\n'.join(ch_bio))
