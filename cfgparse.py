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

""" Config file parsing. """

import codecs
import importlib
import re
import time
import sys

import config

if config.PY3:
    import configparser
else:
    import ConfigParser as configparser
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf8')(sys.stderr)

from grid import Slice
from times import Time, Duration
from room import Level, Room

if not config.PY3:
    class MyConfigParser(configparser.SafeConfigParser):
        """ Py2 ConfigParser does not support inline comments starting with '#'. """

        def __init__(self):
            """ Allow options without values, and don't lower-case option names. """
            configparser.SafeConfigParser.__init__(self, allow_no_value=True)
            self.optionxform = lambda s: s

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

    if config.PY3:
        cfg = configparser.ConfigParser(allow_no_value=True, strict=False,
                                        inline_comment_prefixes=('#',))
        cfg.optionxform = lambda s: s
    else:
        cfg = MyConfigParser()
    with codecs.open(fn, 'r', 'utf-8') as f:
        cfg.readfp(f)

    config.convention = cfg.get('top', 'convention')

    try:
        config.start = time.strptime(cfg.get('top', 'start'), '%Y-%m-%d')
        # time.struct_time(tm_year=2014, tm_mon=1, tm_mday=17, tm_hour=0,
        # tm_min=0, tm_sec=0, tm_wday=4, tm_yday=17, tm_isdst=-1)
    except configparser.NoOptionError:
        None

    try:
        config.default_duration = Duration(cfg.get('top', 'default duration'))
    except configparser.NoOptionError:
        None

    for name in re.split(r',\s*', cfg.get('top', 'goh')):
        config.goh[name] = True

    for (key, value) in cfg.items('input files'):
        config.filenames[key, 'input'] = value

    value = cfg.get('input file importer', 'reader')
    config.filereader = importlib.import_module(value)

    for mode in ('text', 'html', 'xml', 'indesign'):
        try:
            for (key, value) in cfg.items('output files ' + mode):
                config.filenames[key, mode] = value
        except configparser.NoSectionError:
            None

    for (key, value) in cfg.items('output format'):
        for mode in ('text', 'html', 'xml', 'indesign'):
            config.schema[key, mode] = value
    for mode in ('text', 'html', 'xml', 'indesign'):
        try:
            for (key, value) in cfg.items('output format ' + mode):
                config.schema[key, mode] = value
        except configparser.NoSectionError:
            None

    try:
        for (name, sortkey) in cfg.items('sort name'):
            config.sortname[name] = sortkey.lower()
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('change name'):
            config.chname[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('change room'):
            config.chroom[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('change title'):
            config.chtitle[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('change participants'):
            config.chpartic[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('no participants'):
            config.nopartic[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('no description'):
            config.nodescr[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('presentation'):
            config.presentation[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('combat'):
            config.combat[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('featured'):
            config.featured[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (session, unused) in cfg.items('do not print'):
            config.noprint[session] = True
    except configparser.NoSectionError:
        None

    try:
        for (name, rename) in cfg.items('bold name'):
            config.boldname[name] = rename
    except configparser.NoSectionError:
        None

    try:
        for char, expr in cfg.items('icons'):
            #config.icons.append((char, expr))
            expr = expr.replace('track', 'session.track')
            expr = expr.replace('type', 'session.type')
            expr = expr.replace('sessionid', 'session.sessionid')
            expr = expr.replace(' in ', ' in config.')
            expr = re.sub(r'room == (\'\w+\')',
                          r'session.room == config.room[\1]', expr)
            config.icons.append((char, compile(expr, '<string>', 'eval')))
    except configparser.NoSectionError:
        None

    try:
        for area, expr in cfg.items('tracks'):
            expr = expr.replace('track', 'session.track')
            expr = expr.replace('type', 'session.type')
            expr = re.sub(r'room == (\'\w+\')',
                          r'session.room == config.room[\1]', expr)
            area = area.replace(' - ', u'\u2014')
            config.tracks.append((area, compile(expr, '<string>', 'eval')))
    except configparser.NoSectionError:
        None

    try:
        nn = []
        for k, expr in cfg.items('output prune'):
            if k == 'type':
                for n in re.split(r',\s*', expr):
                    nn.append('session.type == \'%s\'' % n)
            elif k == 'title':
                for n in re.split(r',\s*', expr):
                    nn.append('session.title.startswith(\'%s\')' % n)
        config.prune = compile(' or '.join(nn), '<string>', 'eval')
    except configparser.NoSectionError:
        None

    try:
        for unused, expr in cfg.items('featured research'):
            expr = expr.replace('track', 'session.track')
            expr = expr.replace('type', 'session.type')
            # Unlike icons and tracks above, we don't compile these
            # expressions, because we want to print them out at the
            # end. This makes the whole thing slower, but it's not
            # something we're going to do very often.
            config.research.append(expr)
    except configparser.NoSectionError:
        None

    try:
        expr = cfg.get('grid no print', 'title ends with')
        config.grid_noprint = compile('session.title.endswith((%s))' % expr, '<string>', 'eval')
    except (configparser.NoSectionError, configparser.NoOptionError):
        None

    try:
        val = cfg.get('grid title prune', 'usage')
        config.grid_title_prune = re.split(r',\s*', val)
    except (configparser.NoSectionError, configparser.NoOptionError):
        None

    # hotel layout - levels and rooms
    for section in cfg.sections():
        m = re.match(r'(level|venue) (.*)', section)
        if m:
            name = m.group(2)
            config.level[name] = Level(name)
            try:
                config.level[name].pubsname = cfg.get(section, 'pubsname')
            except configparser.NoOptionError:
                None
            rooms = cfg.get(section, 'rooms')
            for r in re.split(r',\s*', rooms):
                config.room[r] = Room(r, config.level[name])
                config.room[config.room[r].index] = config.room[r]

        m = re.match(r'room (.*)', section)
        if m:
            name = m.group(1)
            try:
                config.room[name].pubsname = cfg.get(section, 'pubsname')
            except configparser.NoOptionError:
                None
            try:
                config.room[name].usage = cfg.get(section, 'usage')
            except configparser.NoOptionError:
                None
            try:
                rooms = re.split(r',\s*', cfg.get(section, 'grid room'))
                for i, r in enumerate(rooms):
                    # change room name to Room instance
                    rooms[i] = config.room[r]
                config.room[name].gridrooms = rooms
            except configparser.NoOptionError:
                None

    # grid layout
    try:
        config.twidth = float(cfg.get('grid indesign', 'table width')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        config.theight = float(cfg.get('grid indesign', 'table height')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        config.hheight = float(cfg.get('grid indesign', 'header height')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        config.hwidth = float(cfg.get('grid indesign', 'header width')) * 72.0
    except configparser.NoOptionError:
        None
    try:
        config.cheight_min = float(cfg.get('grid indesign', 'minimum cell height')) \
                      * 72.0
    except configparser.NoOptionError:
        None
    try:
        config.cheight_max = float(cfg.get('grid indesign', 'maximum cell height')) \
                      * 72.0
    except configparser.NoOptionError:
        None
    for mode in ['html', 'indesign', 'xml']:
        try:
            value = cfg.get('grid ' + mode, 'print empty rooms')
            config.fixed[mode] = (value == 'major')
        except (configparser.NoSectionError, configparser.NoOptionError):
            config.fixed[mode] = False

    # grid slices
    for section in cfg.sections():
        (name, n) = re.subn(r'^grid slice ', '', section)
        if n:
            m = re.match(r'(\w+) (\d)', name)
            type = m.group(1)
            name = cfg.get(section, 'name')
            start = cfg.get(section, 'start')
            end = cfg.get(section, 'end')
            s = Slice(name, Time(start), Time(end))
            try:
                if s.start < config.slice[type][0].start:
                    s.start.hour += 24
                if s.end < s.start:
                    s.end.hour += 24
                config.slice[type].append(s)
            except KeyError:
                config.slice[type] = [s]
            # XXX validate that slices are contiguous and complete

if __name__ == '__main__':
    if sys.argv[1]:
        parseConfig(sys.argv[1])
    else:
        parseConfig(config.CFG)

    print('convention = ' + config.convention)
    print('start = %d/%d/%d' % (config.start.tm_mon, config.start.tm_mday, config.start.tm_year))
    print('default_duration = %s' % config.default_duration)
    print('goh = %s' % config.goh)
    print('chname = %s' % config.chname)
    print('chroom = %s' % config.chroom)
    print('chtitle = %s' % config.chtitle)
    print('noprint = %s' % config.noprint)
    print('level = %s' % config.level)
    print('room = %s' % config.room)

    for k, v in config.slice.items():
        print('grid slice %s' % k)
        for s in v:
            print(s)

    print('twidth = %f' % config.twidth)
    print('theight = %f' % config.theight)
    print('hwidth = %f' % config.hwidth)
    print('hheight = %f' % config.hheight)
    print('cheight_min = %f' % config.cheight_min)
    print('cheight_max = %f' % config.cheight_max)

    print('filenames = %s' % config.filenames)
    print('featured = %s' % config.featured)
    print('sortname = %s' % config.sortname)

    for k, v in config.schema.items():
        print('schema[%s] =' % str(k))
        print(v)

    print('grid_title_prune = %s' % ', '.join(config.grid_title_prune))
