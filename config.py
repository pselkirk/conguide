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
# TODO: If there is exactly one .cfg file in the working directory, use
# that by default.

# global variables
debug = False
quiet = False
convention = ''			# used in html output
start = None			# used in guidebook.py
goh = {}			# used in featured.py
filenames = {}
filereader = None
levels = {}			# used in session.py
rooms = {}			# used in session.py and grid.py
days = {}
schema = {}			# used in schedule.py and grid.py (split, expand to others)
sessions = []
participants = {}

# session.py or data importer variables
chname = {}			# used in arisia-csv.py (should also sasquan-xml.py)
chroom = {}			# used in session.py
chtitle = {}			# used in session.py
chdescr = {}			# used in session.py (but not configured)
chpartic = {}			# unused (but configured)
nodescr = {}			# unused (but configured)
noprint = {}			# unused (but configured)

# participant.py variables
sortname = {}

# schedule.py variables
default_duration = None
nopartic = {}
icons = []
prune = None
combat = {}
presentation = {}

# grid.py variables
twidth = float(0)
theight = float(0)
hwidth = float(0)
hheight = float(0)
cheight_min = float(0)
cheight_max = float(0)
fixed = {}
slice = {}
grid_noprint = None
grid_title_prune = []

# bios.py variables
boldnames = {}

# tracks.py variables
track_classifiers = []

# featured.py variables
featured = []
research = []

# html output variables

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
