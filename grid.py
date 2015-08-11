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

import config
import pocketprogram
from room import Room
from times import Duration

# ----------------------------------------------------------------
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

# ----------------------------------------------------------------
class Output(pocketprogram.Output):

    def strTitle(self, session):
        title = session.title
        if self.name == 'xml' or self.name == 'indesign':
            # remove things like "Reading" from the title if it's in the
            # room usage
            for m in config.grid_title_prune:
                try:
                    if session.room.usage == m or \
                       session.room.usage == m + 's' or \
                       m in str(session.room):
                        title = title.replace(m + ' - ', '')
                        title = title.replace(m + ': ', '')
                        break
                except AttributeError:
                    None
        # do the cleanup last, because we're replacing on ' - ',
        # which cleanup() will translate to m-dash
        return self.cleanup(title)

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

# ----------------------------------------------------------------
class HtmlOutput(Output):

    name = 'html'

    def __init__(self, fn):
        Output.__init__(self, fn)
        title = config.convention + ' Schedule Grid'
        self.f.write(config.html_header % \
                     (title,
                      'th { background-color: #E0E0E0 }\n' +
                      'td.gray { background-color: #C0C0C0 }\n' +
                      'td.white { background-color: #FFFFFF }\n',
                      title, config.source_date))
        dd = []
        for day in config.day:
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % \
                     ' - '.join(dd))
        self.f.write('<br /><br />\n')

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
            (config.filenames['schedule', 'html'], session.sessionid, title)

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

    def strRowHeaderCell(self, text):
        if text:
            text = text.replace('\n', '<br />')
        return self.strHeaderCell(text)

    def strTableHeaderCell(self, text):
        return self.strHeaderCell(text)

    def strHeaderCell(self, text):
        if not text:
            text = '&nbsp;'
        return '<th>%s</th>' % text

    def strTextCell(self, nrow, ncol, text):
        return '<td rowspan="%d" colspan="%d" class="white">%s</td>\n' % \
            (nrow, ncol, text)

    def strGrayCell(self, ncol):
        return '<td colspan="%d" class="gray">&nbsp;</td>\n' % ncol

# ----------------------------------------------------------------
class IndesignOutput(Output):

    name = 'indesign'

    # InDesign tags can be verbose (e.g. ParaStyle) or abbreviated (e.g.
    # pstyle). Some of the abbreviated tags can be rather obscure, so I've
    # defaulted to using verbose tags for clarity.

    # NOTE InDesign tagged text uses DOS line breaks (\r\n).

    def __init__(self, fn):
        Output.__init__(self, fn, codec='cp1252')
        self.f.write('<ASCII-WIN>\r\n<Version:8><FeatureSet:InDesign-Roman>')

        if config.fixed[self.name]:
            nrow = 0
            for i in range(Room.index):
                room = config.room[i]
                if room.major:
                    nrow += 1
            self.cheight = (config.theight - config.hheight) / nrow

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert italics
        text = text.replace('<i>', '<CharStyle:Body italic>')
        text = text.replace('</i>', '<CharStyle:>')
        return text

    def strTableTitle(self, gridslice):
        # This feels the wrong place to do this, but it's the first time
        # the IndesignOutput class gets to see the gridslice.
        if not config.fixed[self.name]:
            self.cheight = (config.theight - config.hheight) \
                           / len(gridslice.rooms)
            if self.cheight > config.cheight_max:
                self.cheight = config.cheight_max
            elif self.cheight < config.cheight_min:
                self.cheight = config.cheight_min
        return '<ParaStyle:Headline>%s\r\n' % gridslice.name

    def strTableStart(self, gridslice):
        trows = len(gridslice.rooms) + 1
        tcols = gridslice.endIndex - gridslice.startIndex + 1
        cwidth = (config.twidth - config.hwidth) / (tcols - 1)
        str = '<ParaStyle:Grid time>' + \
              '<TableStart:%d,%d:1:0' % (trows, tcols) + \
              '<tCellDefaultCellType:Text>>'
        # column widths
        str += '<ColStart:<tColAttrWidth:%.4f>>' % config.hwidth
        for i in range(tcols - 1):
            str += '<ColStart:<tColAttrWidth:%.4f>>' % cwidth
        return str

    def strTableEnd(self):
        return '<TableEnd:>\r\n'

    def strHeaderRowStart(self):
        return self.strRowStart(config.hheight)

    def strRowStart(self, height=None):
        # can't default height=self.cheight in the def
        if not height:
            height = self.cheight
        return '<RowStart:<tRowAttrHeight:%.4f><tRowAutoGrow:0>>' % height

    def strRowEnd(self):
        return '<RowEnd:>'

    def strCellStart(self, tag, nrow, ncol):
        return '<CellStyle:Grid %s><CellStart:%d,%d>' % (tag, nrow, ncol)

    def strCellEnd(self):
        return '<CellEnd:>'

    def strCell(self, tag, nrow, ncol, text):
        str = self.strCellStart(tag, nrow, ncol)
        if text:
            str += '<ParaStyle:Grid %s>%s' % (tag, text)
        str += self.strCellEnd()
        if ncol > 1:
            for i in range(ncol - 1):
                str += self.strCellBehind()
        return str

    def strTableHeaderCell(self, text):
        return self.strCell('time', 1, 1, text)

    def strRowHeaderCell(self, text):
        if text:
            # convert room usage styling
            text = text.replace('\n', '\r\n')
            text = text.replace('<i>', '<CharStyle:Room italic>')
            text = text.replace('</i>', '<CharStyle:>')
        return self.strCell('room', 1, 1, text)

    def strTextCell(self, nrow, ncol, text):
        if text:
            text = text.replace('\n', '\r\n')
            text = text.replace('<i>', '<CharStyle:Body italic>')
            text = text.replace('</i>', '<CharStyle:>')
        return self.strCell('text', nrow, ncol, text)

    def strGrayCell(self, ncol):
        return self.strCell('gray', 1, ncol, None)

    def strCellBehind(self):
        return '<CellStart:1,1><CellEnd:>'

# ----------------------------------------------------------------
# InDesign XML suffers from the severe deficiency that you can't control the
# height of a cell, which makes it really annoying to try to produce fixed-
# size tables, as we do for Arisia. It might be useful for variable-size
# tables, as for Worldcon.
class XmlOutput(Output):

    name = 'xml'

    def __init__(self, fn):
        Output.__init__(self, fn)
        self.f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')
        self.f.write('<Root><Story>')

    def __del__(self):
        self.f.write('</Story></Root>\n')
        Output.__del__(self)

    def cleanup(self, text):
        text = Output.cleanup(self, text)
        # convert ampersand
        return text.replace('&', '&amp;')

    def strTableTitle(self, gridslice):
        return '<title xmlns:aid="http://ns.adobe.com/AdobeInDesign/4.0/" aid:pstyle="Headline">%s</title>' % gridslice.name

    def strTableStart(self, gridslice):
        trows = len(gridslice.rooms) + 1
        tcols = gridslice.endIndex - gridslice.startIndex + 1
        self.cwidth = (config.twidth - config.hwidth) / (tcols - 1)
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

    def strRowHeaderCell(self, text):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="1" aid:ccolwidth="74.0448" aid5:cellstyle="Grid room"><room aid:pstyle="Grid room">Alcott</room></Cell>
        text = text.replace('<i>', '<i aid:cstyle="Room italic">')
        return self.strCell('room', 1, 1, config.hwidth, text)

    def strTextCell(self, nrow, ncol, text):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="3" aid5:cellstyle="Grid text"><text aid:pstyle="Grid text">How to Survive the Nerd Convention Apocalypse</text></Cell>
        text = text.replace('<i>', '<i aid:cstyle="Body italic">')
        return self.strCell('text', nrow, ncol, None, text)

    def strGrayCell(self, ncol):
        #<Cell aid:table="cell" aid:crows="1" aid:ccols="15" aid5:cellstyle="Grid gray"></Cell>
        return self.strCellStart('gray', 1, ncol) + self.strCellEnd()

# ----------------------------------------------------------------
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

    def matrix():
        for i in range(Room.index):
            room = config.room[i]
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
                None
        for i in range(Room.index):
            room = config.room[i]
            room.major = (len(room.gridsessions) > 5)	# XXX make this threshold configurable
            # declare an array of half-hour blocks
            room.gridrow = [None for j in range((len(config.day) + 1) * 24 * 2)]
            for session in room.gridsessions:
                if output.name == 'xml' or output.name == 'indesign':
                    if config.grid_noprint and eval(config.grid_noprint):
                        continue
                off = offset(session.time)
                end = offset(session.time + session.duration)
                while off < min(end, len(room.gridrow)):
                    try:
                        # two sessions share the same block
                        # iff they start at the same time
                        if room.gridrow[off][0].time == session.time:
                            room.gridrow[off].append(session)
                        else:
                            room.gridrow[off] = [session]
                        #room.gridrow[off].append(session)
                    except (TypeError, AttributeError):
                        room.gridrow[off] = [session]
                    off += 1

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
            rname = output.fillTemplate(config.schema['grid room', output.name], room.sessions[0])
        except KeyError:
            rname = str(room)
        if room.usage:
            rname += '\n<i>%s</i>' % room.usage
        output.f.write(output.strRowHeaderCell(rname))
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
                tt = []
                if s.time < gridslice.start or s.time.minute % 30 != 0:
                    tt.append(str(s.time).replace(':00', ''))
                if s.duration < Duration('15min'):
                    tt.append(str(s.duration))
                if tt:
                    title += '<i> (%s)</i>' % ', '.join(tt)
                titles.append(title)
            output.f.write(output.strTextCell(nrow, ncol, ', '.join(titles)))

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

    for day in config.day:
        output.f.write(output.strTableAnchor(day.name))
        for slice in config.slice[output.name]:
            gridslice = Slice('%s %s' % (day.name, slice.name),
                              slice.start, slice.end, day)
            gridslice.startIndex = offset(gridslice.start)
            gridslice.endIndex = offset(gridslice.end)
            gridslice.rooms = []
            for i in range(Room.index):
                room = config.room[i]
                try:
                    unused = room.gridrow
                except AttributeError:
                    matrix()
                if activeRoom(room, gridslice.startIndex, gridslice.endIndex) or \
                   (config.fixed[output.name] and room.major):
                    gridslice.rooms.append(room)
            if activeGrid(gridslice):
                writeTable(gridslice)

# ----------------------------------------------------------------
if __name__ == '__main__':
    import cmdline

    args = cmdline.cmdline(io=True)
    config.filereader.read(config.filenames['schedule', 'input'])

#    if args.text:
#        if args.outfile:
#            write(TextOutput(args.outfile))
#        else:
#            write(TextOutput(config.filenames['grid', 'text']))

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile))
        else:
            write(HtmlOutput(config.filenames['grid', 'html']))

    if args.xml:
        if args.outfile:
            write(XmlOutput(args.outfile))
        elif ('grid', 'xml') in config.filenames:
            write(XmlOutput(config.filenames['grid', 'xml']))

    if args.indesign:
        if args.outfile:
            write(IndesignOutput(args.outfile))
        else:
            write(IndesignOutput(config.filenames['grid', 'indesign']))
