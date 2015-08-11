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

""" Global variables """

import sys
PY3 = sys.version > '3'

# default config file
CFG = 'arisia.cfg'

# global variables
debug = False
quiet = False
convention = ''
start = None
default_duration = None
goh = {}
filenames = {}
filereader = None
level = {}
room = {}
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
day = {}
schema = {}
prune = None
sessions = []
participants = {}
grid_noprint = None
grid_title_prune = []

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

