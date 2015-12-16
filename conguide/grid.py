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
from room import Level, Room
from times import Day, Time, Duration
import session

class Slice(object):
    # start and end are Time (with day)

    def __init__(self, name, start, end, day=None):
        self.name = name
        self.start = start
        self.start.day = day
        self.end = end
        self.end.day = day

    def __str__(self):
        return '%s: %s - %s' % \
            (self.name, self.start.__str__(mode='24hr'),
             self.end.__str__(mode='24hr'))

class Output(output.Output):

    def __init__(self, fn, fd=None, codec='utf-8'):
        output.Output.__init__(self, fn, fd, codec)
        Output._readconfig(self)

    def _readconfig(self):
        Output._readconfig = lambda x: None
        Output.template = {}
        try:
            for key, value in config.items('grid template'):
                Output.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass

        exprs = []
        try:
            expr = config.get('grid no print', 'title starts with')
            exprs.append('session.title.startswith((%s))' % expr)
        except (config.NoSectionError, config.NoOptionError):
            pass
        try:
            expr = config.get('grid no print', 'title ends with')
            exprs.append('session.title.endswith((%s))' % expr)
        except (config.NoSectionError, config.NoOptionError):
            pass
        Output.noprint = ' or '.join(exprs)

        try:
            val = config.get('grid title prune', 'usage')
            Output.title_prune = re.split(r',\s*', val)
        except (config.NoSectionError, config.NoOptionError):
            pass


    def configSlice(self):
        for section in config.sections():
            if re.match('grid slice ' + self.name, section):
                name = config.get(section, 'name')
                start = config.get(section, 'start')
                end = config.get(section, 'end')
                s = Slice(name, Time(start), Time(end))
                try:
                    if s.start < self.slice[0].start:
                        s.start.hour += 24
                    if s.end < s.start:
                        s.end.hour += 24
                    self.slice.append(s)
                except AttributeError:
                    self.slice = [s]
                # XXX validate that slices are contiguous and complete

    def strTableAnchor(self, text):
        return ''

    def strHeaderRowStart(self):
        return ''

    def strRowStart(self):
        return ''

    def strRowEnd(self):
        return ''

    def strCellBehind(self):
        return ''

class HtmlOutput(Output):

    name = 'html'

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        title = self.convention + ' Schedule Grid'
        self.f.write(config.html_header % \
                     (title,
                      'th { background-color: #E0E0E0 }\n' +
                      'td.gray { background-color: #C0C0C0 }\n' +
                      'td.white { background-color: #FFFFFF }\n',
                      title, config.source_date))
        dd = []
        for day in Day.days:
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % \
                     ' - '.join(dd))
        self.f.write('<br /><br />\n')

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('grid template html'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass
        try:
            value = config.get('grid html', 'print empty rooms')
            self.fixed = (value == 'major')
        except (config.NoSectionError, config.NoOptionError):
            self.fixed = False
        self.configSlice()

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert ampersand
        return text.replace('&', '&amp;')

    def strTableAnchor(self, text):
        return '<a name="%s"></a>\n' % text

    def strTitle(self, session):
        title = Output.strTitle(self, session)
        return '<a href="%s#%s">%s</a>' % \
            (config.get('output files html', 'schedule'), session.sessionid, title)

    def strTableTitle(self, gridslice):
        return '<h2>%s</h2>\n' % gridslice.name

    def strTableStart(self, gridslice):
        return '<table border="1" width="100%">\n'

    def strTableEnd(self):
        return '</table>\n<br /><br />\n'

    def strHeaderRowStart(self):
        return self.strRowStart()

    def strRowStart(self):
        return '<tr>'

    def strRowEnd(self):
        return '</tr>\n'

    def strRowHeaderCell(self, text, room=None):
        if text:
            text = text.replace('\n', '<br />')
        return self.strHeaderCell(text)

    def strTableHeaderCell(self, text):
        return self.strHeaderCell(text)

    def strHeaderCell(self, text):
        if not text:
            text = '&nbsp;'
        return '<th>%s</th>' % text

    def strTextCell(self, nrow, ncol, text, room=None):
        return '<td rowspan="%d" colspan="%d" class="white">%s</td>\n' % \
            (nrow, ncol, text)

    def strGrayCell(self, ncol):
        return '<td colspan="%d" class="gray">&nbsp;</td>\n' % ncol

class IndesignOutput(Output):

    name = 'indesign'

    # InDesign tags can be verbose (e.g. ParaStyle) or abbreviated (e.g.
    # pstyle). Some of the abbreviated tags can be rather obscure, so I've
    # defaulted to using verbose tags for clarity.

    # NOTE InDesign tagged text uses DOS line breaks (\r\n).

    def __init__(self, fn):
        Output.__init__(self, fn, codec='cp1252')
        self._readconfig()
        self.f.write('<ASCII-WIN>\r\n<Version:8><FeatureSet:InDesign-Roman>')

        for level in set(Level.levels.values()):
            rooms = filter(lambda room: room.major, level.rooms)
            try:
                rooms[-1].last = True
            except IndexError:
                pass

        if self.fixed:
            nrow = len(filter(lambda room: room.major, set(Room.rooms.values())))
            self.cheight = (self.theight - self.hheight) / nrow
        else:
            self.cheight = (self.theight - self.hheight) / len(gridslice.rooms)
            if self.cheight > self.cheight_max:
                self.cheight = self.cheight_max
            elif self.cheight < self.cheight_min:
                self.cheight = self.cheight_min

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('grid template indesign'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass
        try:
            value = config.get('grid indesign', 'print empty rooms')
            self.fixed = (value == 'major')
        except (config.NoSectionError, config.NoOptionError):
            self.fixed = False
        try:
            self.twidth = config.getfloat('grid indesign', 'table width') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.theight = config.getfloat('grid indesign', 'table height') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.hheight = config.getfloat('grid indesign', 'header height') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.hwidth = config.getfloat('grid indesign', 'header width') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.cheight_min = config.getfloat('grid indesign', 'minimum cell height') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.cheight_max = config.getfloat('grid indesign', 'maximum cell height') * 72.0
        except config.NoOptionError:
            pass
        self.configSlice()

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert italics
        text = text.replace('<i>', '<CharStyle:Body italic>')
        text = text.replace('</i>', '<CharStyle:>')
        return text

    def strTitle(self, session):
        title = session.title
        # XXX local policy
        # remove things like "Reading" from the title if it's in the
        # room usage
        try:
            for m in self.title_prune:
                if session.room.usage == m or \
                   session.room.usage == m + 's' or \
                   m in str(session.room):
                    title = title.replace(m + ' - ', '')
                    title = title.replace(m + ': ', '')
                    break
        except AttributeError:
            pass
        # do the cleanup last, because we're replacing on ' - ',
        # which cleanup() will translate to m-dash
        return self.cleanup(title)

    def strTableTitle(self, gridslice):
        return '<ParaStyle:Headline>%s\r\n' % gridslice.name

    def strTableStart(self, gridslice):
        trows = len(gridslice.rooms) + 1
        tcols = gridslice.endIndex - gridslice.startIndex + 1
        cwidth = (self.twidth - self.hwidth) / (tcols - 1)
        str = '<ParaStyle:Grid time>' + \
              '<TableStart:%d,%d:1:0' % (trows, tcols) + \
              '<tCellDefaultCellType:Text>>'
        # column widths
        str += '<ColStart:<tColAttrWidth:%.4f>>' % self.hwidth
        for i in range(tcols - 1):
            str += '<ColStart:<tColAttrWidth:%.4f>>' % cwidth
        return str

    def strTableEnd(self):
        return '<TableEnd:>\r\n'

    def strHeaderRowStart(self):
        return self.strRowStart(self.hheight)

    def strRowStart(self, height=None):
        # can't default height=self.cheight in the def
        if not height:
            height = self.cheight
        return '<RowStart:<tRowAttrHeight:%.4f><tRowAutoGrow:0>>' % height

    def strRowEnd(self):
        return '<RowEnd:>'

    def strCellStart(self, tag, nrow, ncol, cstyle_extra=None):
        if cstyle_extra:
            tag += cstyle_extra
        return '<CellStyle:Grid %s><CellStart:%d,%d>' % (tag, nrow, ncol)

    def strCellEnd(self):
        return '<CellEnd:>'

    def strCell(self, tag, nrow, ncol, text, cstyle_extra=None):
        str = self.strCellStart(tag, nrow, ncol, cstyle_extra)
        if text:
            str += '<ParaStyle:Grid %s>%s' % (tag, text)
        str += self.strCellEnd()
        if ncol > 1:
            for i in range(ncol - 1):
                str += self.strCellBehind()
        return str

    def strTableHeaderCell(self, text):
        return self.strCell('time', 1, 1, text)

    def strRowHeaderCell(self, text, room=None):
        if text:
            # flag it if it's a minor room with scheduled sessions
            if not room.major:
                text = '<CharStyle:Red>' + text + '<CharStyle:>'
            # convert room usage styling
            text = text.replace('\n', '\r\n')
            text = text.replace('<i>', '<CharStyle:Room italic>')
            text = text.replace('</i>', '<CharStyle:>')
        if room and not hasattr(room, 'last'):
            cstyle_extra = ' no bottom'
        else:
            cstyle_extra = None
        return self.strCell('room', 1, 1, text, cstyle_extra)

    def strTextCell(self, nrow, ncol, text, room=None):
        if text:
            text = text.replace('\n', '\r\n')
            text = text.replace('<i>', '<CharStyle:Body italic>')
            text = text.replace('</i>', '<CharStyle:>')
            # add roomname to minor rooms, to make it easier to move
            # cell contents around in indesign
            if room and not room.major:
                text += '<CharStyle:Body italic> (%s)<CharStyle:>' % room.pubsname
        return self.strCell('text', nrow, ncol, text)

    def strGrayCell(self, ncol):
        return self.strCell('gray', 1, ncol, None)

    def strCellBehind(self):
        return '<CellStart:1,1><CellEnd:>'

# InDesign XML suffers from the severe deficiency that you can't control the
# height of a cell, which makes it really annoying to try to produce fixed-
# size tables, as we do for Arisia. It might be useful for variable-size
# tables, as for Worldcon.
class XmlOutput(Output):

    name = 'xml'

    def __init__(self, fn):
        Output.__init__(self, fn)
        self._readconfig()
        self.f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        self.f.write('<Root><Story>')

    def _readconfig(self):
        self.template = copy.copy(Output.template)
        try:
            for key, value in config.items('grid template xml'):
                self.template[key] = self.parseTemplate(value)
        except config.NoSectionError:
            pass
        try:
            value = config.get('grid xml', 'print empty rooms')
            self.fixed = (value == 'major')
        except (config.NoSectionError, config.NoOptionError):
            self.fixed = False
        try:
            self.twidth = config.getfloat('grid xml', 'table width') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.theight = config.getfloat('grid xml', 'table height') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.hheight = config.getfloat('grid xml', 'header height') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.hwidth = config.getfloat('grid xml', 'header width') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.cheight_min = config.getfloat('grid xml', 'minimum cell height') * 72.0
        except config.NoOptionError:
            pass
        try:
            self.cheight_max = config.getfloat('grid xml', 'maximum cell height') * 72.0
        except config.NoOptionError:
            pass
        self.configSlice()

    def __del__(self):
        self.f.write('</Story></Root>\n')
        Output.__del__(self)

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert ampersand
        return text.replace('&', '&amp;')

    def strTitle(self, session):
        title = session.title
        # XXX local policy
        # remove things like "Reading" from the title if it's in the
        # room usage
        try:
            for m in self.title_prune:
                if session.room.usage == m or \
                   session.room.usage == m + 's' or \
                   m in str(session.room):
                    title = title.replace(m + ' - ', '')
                    title = title.replace(m + ': ', '')
                    break
        except AttributeError:
            pass
        # do the cleanup last, because we're replacing on ' - ',
        # which cleanup() will translate to m-dash
        return self.cleanup(title)

    def strTableTitle(self, gridslice):
        return '<title xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/" aid:pstyle="Headline">%s</title>' % gridslice.name

    def strTableStart(self, gridslice):
        trows = len(gridslice.rooms) + 1
        tcols = gridslice.endIndex - gridslice.startIndex + 1
        self.cwidth = (self.twidth - self.hwidth) / (tcols - 1)
        return'<Table xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/" xmlns:aid5="http://ns.adobe.com/AdobeInDesign/5.0/" aid:table="table" aid:trows="%d" aid:tcols="%d">' % (trows, tcols)

    def strTableEnd(self):
        return '</Table>\n'

    def strCellStart(self, tag, nrow, ncol, colwidth=None):
        if colwidth:
            colwidth = ' aid:ccolwidth="%.4f"' % colwidth
        else:
            colwidth = ''
        return '<Cell aid:table="cell" aid:crows="%d" aid:ccols="%d"%s aid5:cellstyle="Grid %s">' % (nrow, ncol, colwidth, tag)

    def strCellEnd(self):
        return '</Cell>'

    def strCell(self, tag, nrow, ncol, colwidth, text):
        return \
            self.strCellStart(tag, nrow, ncol, colwidth) + \
            '<%s aid:pstyle="Grid %s">%s</%s>' % (tag, tag, text, tag) + \
            self.strCellEnd()

    def strTableHeaderCell(self, text):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="1" aid:ccolwidth="37.8864" aid5:cellstyle="Grid time"><time aid:pstyle="Grid time">8:30a</time></Cell>
        return self.strCell('time', 1, 1, self.cwidth, text)

    def strRowHeaderCell(self, text, room=None):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="1" aid:ccolwidth="74.0448" aid5:cellstyle="Grid room"><room aid:pstyle="Grid room">Alcott</room></Cell>
        text = text.replace('<i>', '<i aid:cstyle="Room italic">')
        return self.strCell('room', 1, 1, self.hwidth, text)

    def strTextCell(self, nrow, ncol, text, room=None):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="3" aid5:cellstyle="Grid text"><text aid:pstyle="Grid text">How to Survive the Nerd Convention Apocalypse</text></Cell>
        text = text.replace('<i>', '<i aid:cstyle="Body italic">')
        return self.strCell('text', nrow, ncol, None, text)

    def strGrayCell(self, ncol):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="15" aid5:cellstyle="Grid gray"></Cell>
        return self.strCellStart('gray', 1, ncol) + self.strCellEnd()

def write(output, unused=None):

    def activeRoom(room, start, end):
        for i in range(start, end):
            if room.gridrow[i]:
                return True
        return False

    def activeGrid(gridslice):
        for room in gridslice.rooms:
            if activeRoom(room, gridslice.startIndex, gridslice.endIndex):
                return True
        return False

    def offset(time):
        return (time.day.index * 24 * 2) + (time.hour * 2) + int((time.minute + 15) / 30)

    def writeTable(gridslice):
        output.f.write(output.strTableTitle(gridslice))
        output.f.write(output.strTableStart(gridslice))
        writeTableHeaderRow(gridslice)
        for i in range(len(gridslice.rooms)):
            writeTableRow(gridslice, i)
        output.f.write(output.strTableEnd())

    def writeTableHeaderRow(gridslice):
        output.f.write(output.strHeaderRowStart())
        output.f.write(output.strRowHeaderCell(''))
        time = gridslice.start
        half = Duration('30min')
        while time < gridslice.end:
            output.f.write(output.strTableHeaderCell(time.__str__(mode='grid')))
            time += half
        output.f.write(output.strRowEnd())

    def writeTableRow(gridslice, i):
        room = gridslice.rooms[i]
        row = room.gridrow
        output.f.write(output.strRowStart())
        try:
            rname = output.fillTemplate(output.template['room'], room.gridsessions[0])
        except KeyError:
            rname = str(room)
        output.f.write(output.strRowHeaderCell(rname, room))
        j = gridslice.startIndex
        while j < gridslice.endIndex:
            ncol = colspan(gridslice, i, j)
            # if this session was previously listed in an adjacent room, skip
            if row[j] and (i > 0) and \
               (gridslice.rooms[i-1].gridrow[j] == row[j]):
                for i in range(ncol):
                    output.f.write(output.strCellBehind())
            else:
                nrow = rowspan(gridslice, i, j)
                writeSessions(gridslice, i, j, nrow, ncol)
            j += ncol
        output.f.write(output.strRowEnd())

    def writeSessions(gridslice, i, j, nrow, ncol):
        room = gridslice.rooms[i]
        sessions = room.gridrow[j]
        if not sessions:
            output.f.write(output.strGrayCell(ncol))
        else:
            titles = []
            for s in sessions:
                title = output.strTitle(s)
                #tt = []
                #if s.time < gridslice.start or s.time.minute % 30 != 0:
                #    tt.append(str(s.time).replace(':00', ''))
                #if s.duration < Duration('15min'):
                #    tt.append(str(s.duration))
                #if tt:
                #    title += '<i> (%s)</i>' % ', '.join(tt)
                if s.time < gridslice.start:
                    title += '<i> (%s)</i>' % str(s.time).replace(':00', '')
                titles.append(title)
            output.f.write(output.strTextCell(nrow, ncol, ', '.join(titles), room))

    def colspan(gridslice, i, j):
        row = gridslice.rooms[i].gridrow
        k = j + 1
        while k < gridslice.endIndex and row[k] == row[j]:
            k += 1
        return k - j

    def rowspan(gridslice, i, j):
        k = i + 1
        while k < len(gridslice.rooms) and \
              gridslice.rooms[k].gridrow[j] == gridslice.rooms[i].gridrow[j]:
            k += 1
        return k - i

    for day in Day.days:
        output.f.write(output.strTableAnchor(day.name))
        for slice in output.slice:
            gridslice = Slice('%s %s' % (day.name, slice.name),
                              slice.start, slice.end, day)
            gridslice.startIndex = offset(gridslice.start)
            gridslice.endIndex = offset(gridslice.end)
            gridslice.rooms = []
            for room in sorted(set(Room.rooms.values())):
                if activeRoom(room, gridslice.startIndex, gridslice.endIndex) or \
                   (output.fixed and room.major):
                    gridslice.rooms.append(room)
            if activeGrid(gridslice):
                writeTable(gridslice)

matrix_done = False
def matrix():
    global matrix_done
    if matrix_done:
        return
    matrix_done = True

    def offset(time):
        return (time.day.index * 24 * 2) + (time.hour * 2) + int((time.minute + 15) / 30)

    for room in sorted(set(Room.rooms.values())):
        room.gridsessions = room.sessions
        try:
            for r in room.gridrooms:
                sessions = []
                for s in room.sessions:
                    s.room = r
                    sessions.append(s)
                r.gridsessions += sessions
            room.gridsessions = []
        except AttributeError:
            pass

    for room in sorted(set(Room.rooms.values())):
        room.major = (len(room.gridsessions) > 5)	# XXX make this threshold configurable

        # declare an array of half-hour blocks
        room.gridrow = [None for j in range((len(Day.days) + 1) * 24 * 2)]
        for session in room.gridsessions:
            # config doesn't get read until we instantiate an output class.
            # [grid no print] items can screw with counts for "major" rooms.
            ##if output.noprint and eval(output.noprint):
            ##    if output.name == 'xml' or output.name == 'indesign':
            ##        continue
            ##    else:
            ##        # XXX more local policy
            ##        # XXX may also screw up anything else using session data after this
            ##        session.duration = Duration('30min')
            off = offset(session.time)
            end = offset(session.time + session.duration)
            if off == end:
                # This is a short session, where start and end round to
                # the same time. This can happen for a few reasons,
                # outlined below.
                startmin = session.time.minute
                endmin = startmin + session.duration.minute

                # a) If the session is less than 15 minutes, and falls
                # entirely in the first half of the slot (e.g. 4:00-4:10),
                # we need to push out the end time.
                if startmin < 15 or \
                   startmin >= 30 and startmin < 45:
                    end += 1

                # b) If the session is less than 15 minutes, and falls
                # entirely in the second half of the slot (e.g. 4:20-4:30),
                # we need to pull back the start time.
                elif endmin >= 15 and endmin <= 30 or \
                     endmin >= 45 and endmin <= 60:
                    off -= 1

                # c) If the session is less than 30 minutes, and crosses
                # an hour or half-hour boundary, we need to figure out
                # which slot it's more "in".
                else:
                    if startmin < 30:
                        # session crosses a half-hour boundary
                        before = 30 - startmin
                        after = endmin - 30
                    else:
                        # session crosses an hour boundary
                        before = 60 - startmin
                        after = endmin - 60
                    if before > after:
                        off -= 1
                    else:
                        end += 1
                # Note: This doesn't account for all short sessions.
                # If a session is less than 30 minutes, but crosses a
                # 15-minute mark (e.g. 4:05-4:25), start and end get
                # rounded in different directions, and it's handled the
                # same as a half-hour session.

            while off < min(end, len(room.gridrow)):
                try:
                    # two sessions share the same cell
                    # iff they start at the same time
                    if session.time - room.gridrow[off][0].time < Duration('30min'):
                        room.gridrow[off].append(session)
                    else:
                        room.gridrow[off] = [session]
                    #room.gridrow[off].append(session)
                except (TypeError, AttributeError):
                    room.gridrow[off] = [session]
                off += 1

def main(args):
    fn = args.infile or config.get('input files', 'schedule')
    (sessions, participants) = session.read(fn)
    if args.all:
        args.html = True
        args.indesign = True
        args.xml = True
    matrix()
    for mode in ('html', 'indesign', 'xml'):
        if eval('args.' + mode):
            outfunc = eval('%sOutput' % mode.capitalize())
            if args.outfile:
                write(outfunc(args.outfile), sessions)
            else:
                try:
                    write(outfunc(config.get('output files ' + mode, 'grid')),
                          sessions)
                except config.NoOptionError:
                    pass
