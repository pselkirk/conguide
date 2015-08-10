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

""" Config file parsing, and global variables. """

import codecs
import re
import time
import sys

PY3 = sys.version > '3'
if PY3:
    import configparser
else:
    import ConfigParser as configparser

import grid
import times
from room import Level, Room

# default config file
CFG = 'arisia.cfg'

# global variables
debug = False
convention = ''
start = None
default_duration = None
goh = {}
filenames = {}
level = {}
room = {}
room_combo = {}
sortname = {}
chname = {}
chroom = {}
chtitle = {}
chdescr = {}
chpartic = {}
nopartic = {}
nodescr = {}
noprint = {}
combat = {}
presentation = {}
featured = {}
boldname = {}
twidth = float(0)
theight = float(0)
hwidth = float(0)
hheight = float(0)
cheight_min = float(0)
cheight_max = float(0)
fixed = {}
slice = {}
icons = []
tracks = []
research = []

# Assume the common case of a con starting on Friday.
# If it doesn't, session.read() will rotate the array.
days = [ 'Fri', 'Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu' ]
day = {}
i = 0
for d in days:
    Day = times.Day(d)
    Day.index = i
    day[i] = Day
    #day[Day.name] = Day
    day[Day.shortname] = Day
    i += 1

# Boilerplate xhtml file header, with 4 %s bits:
# - title, for <head>
# - extra styles (only used in grid.py)
# - title again, for <body>
# - timestamp of the input csv file
html_header = \
'<?xml version="1.0" encoding="UTF-8"?>\n\
<!DOCTYPE html\n\
     PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"\n\
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n\
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\n\
<head>\n\
<title>%s</title>\n\
<meta http-equiv="content-type" content="text/html;charset=utf-8" />\n\
<style type="text/css">\n\
div.center {text-align:center}\n\
%s\
</style>\n\
</head>\n\
<body>\n\
<div class="center">\n\
<h1>%s</h1>\n\
<p>Generated: %s</p>\n\
</div>\n'
source_date = ''

if not PY3:
    class MyConfigParser(configparser.SafeConfigParser):
        """ Py2 ConfigParser does not support inline comments starting with '#'. """

        def __init__(self):
            """ Allow options without values, and don't lower-case option names. """
            configparser.SafeConfigParser.__init__(self, allow_no_value=True)
            self.optionxform = lambda s:s

        def get(self, section, option):
            value = configparser.SafeConfigParser.get(self, section, option)
            return re.sub(r'\s*#.*', '', value)

        def items(self, section):
            list = configparser.ConfigParser.items(self, section)
            for i, (name, value) in enumerate(list):
                name = re.sub(r'\s*#.*', '', name)
                value = re.sub(r'\s*#.*', '', value)
                list[i] = (name, value)
            return list

def parseConfig(fn):

    # sigh, scalar variables have to be declared global
    global convention, start, default_duration, twidth, theight, hwidth, hheight, cheight_min, cheight_max

    if PY3:
        cfg = configparser.ConfigParser(allow_no_value=True, strict=False, inline_comment_prefixes=('#',))
        cfg.optionxform = lambda s:s
    else:
        cfg = MyConfigParser()
    with codecs.open(fn, 'r', 'utf-8') as f:
        cfg.readfp(f)

    convention = cfg.get('top', 'convention')

    try:
        start = time.strptime(cfg.get('top', 'start'), '%Y-%m-%d')
        # time.struct_time(tm_year=2014, tm_mon=1, tm_mday=17, tm_hour=0,
        # tm_min=0, tm_sec=0, tm_wday=4, tm_yday=17, tm_isdst=-1)
    except configparser.NoOptionError:
        None

    try:
        default_duration = times.Duration(cfg.get('top', 'default duration'))
    except configparser.NoOptionError:
        None

    for name in re.split(r',\s*', cfg.get('top', 'goh')):
        goh[name] = True

    for (key, value) in cfg.items('input files'):
        filenames[key, 'input'] = value

    for mode in ('text', 'html', 'xml', 'indesign'):
        try:
            for (key, value) in cfg.items('output files ' + mode):
                filenames[key, mode] = value
        except configparser.NoSectionError:
            None

    try:
        for (name, sortkey) in cfg.items('sort name'):
            sortname[name] = sortkey
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('change name'):
            chname[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('change room'):
            # XXX hack for dash in room name
            name = name.replace(' - ', u'\u2014')
            rename = rename.replace(' - ', u'\u2014')
            chroom[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('change title'):
            chtitle[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('change participants'):
            chpartic[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('no participants'):
            nopartic[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('no description'):
            nodescr[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('presentation'):
            presentation[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('combat'):
            combat[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('featured'):
            featured[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('do not print'):
            noprint[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('bold name'):
            # XXX hack for quotes in names
            rename = re.sub(r'^"', u'\u201c', rename)        # beginning double quote -> left
            rename = re.sub(r'"$', u'\u201d', rename)        # ending double quote -> right
            rename = re.sub(r'([^\w,.!?])"(\w)', r'\1'+u'\u201c'+r'\2', rename) # left double quote
            rename = re.sub(r'"', u'\u201d', rename) # all remaining double quotes -> right
            boldname[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for char, expr in cfg.items('icons'):
            #icons.append((char, expr))
            expr = expr.replace('track', 'session.track')
            expr = expr.replace('type', 'session.type')
            expr = expr.replace('sessionid', 'session.sessionid')
            expr = expr.replace(' in ', ' in config.')
            expr = re.sub(r'room == (\'\w+\')',
                          r'session.room == config.room[\1]', expr)
            icons.append((char, compile(expr, '<string>', 'eval')))
    except configparser.NoSectionError:
        None

    try:
        for area, expr in cfg.items('tracks'):
            expr = expr.replace('track', 'session.track')
            expr = expr.replace('type', 'session.type')
            expr = re.sub(r'room == (\'\w+\')',
                          r'session.room == config.room[\1]', expr)
            area = area.replace(' - ', u'\u2014')
            tracks.append((area, compile(expr, '<string>', 'eval')))
    except configparser.NoSectionError:
        None

    try:
        for unused, expr in cfg.items('featured research'):
            expr = expr.replace('track', 'session.track')
            expr = expr.replace('type', 'session.type')
            # Note we don't compile these expressions, because we want to
            # print them out at the end. This makes the whole thing slower,
            # but it's not something we're going to do very often.
            research.append(expr)
    except configparser.NoSectionError:
        None

    # hotel layout - levels and rooms
    for section in cfg.sections():
        m = re.match(r'level (.*)', section)
        if m:
            name = m.group(1)
            try:
                pubsname = cfg.get(section, 'pubsname')
            except configparser.NoOptionError:
                pubsname = None
            level[name] = Level(name, pubsname)
            rooms = cfg.get(section, 'rooms')
            for r in re.split(r',\s*', rooms):
                # XXX hack for 'Galleria - Autograph Space'
                r = r.replace(' - ', u'\u2014')
                room[r] = Room(r, level[name])
                room[room[r].index] = room[r]

        m = re.match(r'room (.*)', section)
        if m:
            name = m.group(1)
            # XXX hack for 'Galleria - Autograph Space'
            name = name.replace(' - ', u'\u2014')
            try:
                room[name].pubsname = cfg.get(section, 'pubsname')
            except configparser.NoOptionError:
                None
            try:
                room[name].usage = cfg.get(section, 'usage')
            except configparser.NoOptionError:
                None
            try:
                rooms = re.split(r',\s*', cfg.get(section, 'combination'))
                for i, r in enumerate(rooms):
                    # change room name to Room instance
                    rooms[i] = room[r]
                room_combo[name] = rooms
            except configparser.NoOptionError:
                None

    # grid layout
    try:
        twidth = float(cfg.get('grid indesign', 'table width')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        theight = float(cfg.get('grid indesign', 'table height')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        hheight = float(cfg.get('grid indesign', 'header height')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        hwidth = float(cfg.get('grid indesign', 'header width')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        cheight_min = float(cfg.get('grid indesign', 'minimum cell height')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        cheight_max = float(cfg.get('grid indesign', 'maximum cell height')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        value = cfg.get('grid indesign', 'print empty rooms')
        fixed['indesign'] = (value == 'major')
    except configparser.NoOptionError:
        None
    try:
        value = cfg.get('grid html', 'print empty rooms')
        fixed['html'] = (value == 'major')
    except configparser.NoOptionError:
        None

    # grid slices
    for section in cfg.sections():
        (name, n) = re.subn(r'^grid slice ', '', section)
        if n:
            m = re.match(r'(\w+) (\d)', name)
            type = m.group(1)
            name = cfg.get(section, 'name')
            # 'start' conflicts with global variable above
            # should refactor this into a bunch of smaller functions
            strt = cfg.get(section, 'start')
            end = cfg.get(section, 'end')
            s = grid.Slice(name, times.Time(strt), times.Time(end))
            try:
                if s.start < slice[type][0].start:
                    s.start.hour += 24
                if s.end < s.start:
                    s.end.hour += 24
                slice[type].append(s)
            except KeyError:
                slice[type] = [s]
            # XXX validate that slices are contiguous and complete

if __name__ == '__main__':
    parseConfig(CFG)
    print('convention = ' + convention)
    print('start = %d/%d/%d' % (start.tm_mon, start.tm_mday, start.tm_year))
    print('default_duration = %s' % default_duration)
    print('goh = %s' % goh)
    print('chname = %s' % chname)
    print('chroom = %s' % chroom)
    print('chtitle = %s' % chtitle)
    print('noprint = %s' % noprint)
    print('level = %s' % level)
    print('room = %s' % room)
    print('day = %s' % day)

    for k,v in slice.items():
        print('grid slice %s' % k)
        for s in v:
            print(s)

    print('twidth = %f' % twidth)
    print('theight = %f' % theight)
    print('hwidth = %f' % hwidth)
    print('hheight = %f' % hheight)
    print('cheight_min = %f' % cheight_min)
    print('cheight_max = %f' % cheight_max)

    print('filenames = %s' % filenames)
    print('featured = %s' % featured)
    print('sortname = %s' % sortname)
