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

""" Global variables and config file parsing. """

import re
import sys
PY3 = sys.version > '3'

if not PY3:
    import codecs
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf8')(sys.stderr)

# default config file
CFG = 'conguide.cfg'
# TODO: If there is exactly one .cfg file in the working directory, use
# that by default.

# global variables
debug = False
quiet = False
cfgfile = CFG

# bios.py variables
boldnames = {}

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

if PY3:
    import configparser
else:
    import ConfigParser as configparser
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

cfg = None

def readConfig(fn):
    global cfg
    if not cfg:
        if PY3:
            cfg = configparser.ConfigParser(allow_no_value=True, strict=False,
                                            inline_comment_prefixes=('#',))
            cfg.optionxform = lambda s: s
            with open(fn, 'r') as f:
                cfg.readfp(f)
        else:
            cfg = MyConfigParser()
            with codecs.open(fn, 'r', 'utf-8') as f:
                cfg.readfp(f)

def get(section, option):
    readConfig(cfgfile)
    try:
        return cfg.get(section, option)
    except configparser.NoSectionError as e:
        raise NoSectionError(e)
    except configparser.NoOptionError as e:
        raise NoOptionError(e)

def getfloat(section, option):
    readConfig(cfgfile)
    try:
        return cfg.getfloat(section, option)
    except configparser.NoSectionError as e:
        raise NoSectionError(e)
    except configparser.NoOptionError as e:
        raise NoOptionError(e)

def items(section):
    readConfig(cfgfile)
    try:
        return cfg.items(section)
    except configparser.NoSectionError as e:
        raise NoSectionError(e)

def itemdict(section):
    readConfig(cfgfile)
    try:
        dd = {}
        for key, value in cfg.items(section):
            dd[key] = value
        return dd
    except configparser.NoSectionError as e:
        raise NoSectionError(e)

def sections():
    readConfig(cfgfile)
    return cfg.sections()

def set(section, option, value):
    readConfig(cfgfile)
    try:
        cfg.set(section, option, value)
    except configparser.NoSectionError as e:
        raise NoSectionError(e)

# exception classes, so callers don't have to know about configparser
# (or ConfigParser)
class NoSectionError(configparser.NoSectionError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NoOptionError(configparser.NoOptionError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

