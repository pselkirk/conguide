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

import codecs
import re

import config
import times
from room import Room

class Slice:
    # start and end can be Time (from config) or DayTime

    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

    def __str__(self):
        return '%s: %s - %s' % (self.name, self.start.__str__(), self.end.__str__())

class Output:

    def __init__(self, fn, codec='utf-8'):
        self.f = codecs.open(fn, 'w', codec)

    def __del__(self):
        self.f.close()

class HtmlOutput(Output):

    name = 'html'

    def __init__(self, fn):
        Output.__init__(self, fn)
        title = config.convention + ' Schedule Grid'
        self.f.write(config.html_header % (title,
                                           'th { background-color: #E0E0E0 }\n' +
                                           'td.gray { background-color: #C0C0C0 }\n' +
                                           'td.white { background-color: #FFFFFF }\n',
                                           title, config.source_date))
        dd = []
        for d in range(times.Day.index):
            day = config.day[d]
            dd.append('<a href="#%s">%s</a>' % (day.name, day.name))
        self.f.write('<div class="center">\n<p><b>%s</b></p>\n</div>\n' % ' - '.join(dd))
        self.f.write('<br /><br />\n')

    def __del__(self):
        self.f.write('</body></html>\n')
        Output.__del__(self)

    def writeAnchor(self, label):
        if label:
            self.f.write('<a name="%s"></a>\n' % label)

    def writeTableHeader(self, title, times):
        self.f.write('<h2>%s</h2>\n' % title)
        self.f.write('<table border="1" width="100%">\n')
        self.f.write('<tr><th>&nbsp;</th>')
        for stime in times:
            self.f.write('<th>%s</th>' % stime)
        self.f.write('</tr>\n')

    def writeTableEnd(self):
        self.f.write('</table>\n<br /><br />\n')

    def writeRoom(self, room):
        rname = room.pubsname
        if room.usage:
            rname += '<br /><i>%s</i>' % room.usage
        self.f.write('<tr><th>%s</th>' % rname)

    def writeRowEnd(self):
        self.f.write('</tr>\n')

    def writeSessions(self, rows, cols, sessions, room):
        if not sessions:
            self.f.write('<td colspan="%d" class="gray">&nbsp;</td>' % cols)
        else:
            self.f.write('<td rowspan="%d" colspan="%d" class="white">' % (rows, cols))
            ss = []
            for (sessionid, title) in sessions:
                ss.append('<a href="%s#%s">%s</a>' % \
                          (config.filenames['schedule', 'html'],
                           sessionid, title.replace('&', '&amp;')))
            self.f.write('; <br />'.join(ss) + '</td>\n')

    def writeCellsBehind(self, cols):
        return

class IndesignOutput(Output):

    name = 'indesign'

    # InDesign tags can be verbose (e.g. ParaStyle) or abbreviated (e.g.
    # pstyle). Some of the abbreviated tags can be rather obscure, so I've
    # defaulted to using verbose tags for clarity.

    # NOTE InDesign tagged text uses DOS line breaks (\r\n).

    def __init__(self, fn):
        Output.__init__(self, fn, 'cp1252')

        # count "major" rooms (+1 for time header)
        self.nrows = 0
        for i in range(Room.index):
            r = config.room[i]
            if len(r.sessions) > 5:     # XXX make this threshold configurable
                self.nrows += 1
                r.minor = False
            else:
                r.minor = True

        self.f.write('<ASCII-WIN>\r\n<Version:8><FeatureSet:InDesign-Roman>')
        # If you export tagged text, this is followed by definitions of
        # styles. We want to keep the definitions in the InDesign file, and
        # NOT redefine them here.

    def writeAnchor(self, label):
        return

    def writeTableHeader(self, title, times):
        # XXX key off config.fixed
        trows = self.nrows + 1
        tcols = len(times) + 1
        self.cheight = (config.theight - config.hheight) / self.nrows
        self.cwidth = (config.twidth - config.hwidth) / len(times)

        self.f.write('<ParaStyle:Headline>%s\r\n' % title)
        self.f.write('<ParaStyle:Grid time>')
        self.f.write('<TableStart:%d,%d:1:0<tCellDefaultCellType:Text>>' % (trows, tcols))
        # column widths
        self.f.write('<ColStart:<tColAttrWidth:%.4f>>' % config.hwidth)
        for i in times:
            self.f.write('<ColStart:<tColAttrWidth:%.4f>>' % self.cwidth)
        # header row: times
        self.f.write('<RowStart:<tRowAttrHeight:%.4f><tRowAutoGrow:0>>' % config.hheight)
        self.f.write('<CellStyle:Grid room><CellStart:1,1><ParaStyle:Grid room> <CellEnd:>')
        for stime in times:
            self.f.write('<CellStyle:Grid time><CellStart:1,1><ParaStyle:Grid time>%s<CellEnd:>' % stime)

    def writeTableEnd(self):
        self.f.write('<TableEnd:>\r\n')

    def writeRoom(self, room):
        self.f.write('<RowStart:<tRowAttrHeight:%.4f><tRowAutoGrow:0>>' % self.cheight)
        rname = room.pubsname

        # flag fixed-function rooms
        if room.usage:
            rname += '\r\n<CharStyle:Room italic>%s' % room.usage

        # figure out whether the cell needs a bottom stroke
        rnum = room.index + 1
        while rnum < Room.index and config.room[rnum].minor:
            rnum += 1
        if rnum == Room.index or config.room[rnum].level != room.level:
            cellstyle = 'Grid room'
        else:
            cellstyle = 'Grid room no bottom'
        self.f.write('<CellStyle:%s><CellStart:1,1><ParaStyle:Grid room>' % cellstyle)

        # flag it if it's a minor room with scheduled sessions
        if room.minor:
            self.f.write('<CharStyle:Red>')

        self.f.write('%s<CellEnd:>' % rname)

    def writeRowEnd(self):
        self.f.write('<RowEnd:>')

    def writeSessions(self, rows, cols, sessions, room):
        if not sessions:
            self.f.write('<CellStyle:Grid gray><CellStart:1,%d><CellEnd:>' % cols)
        else:
            ss = []
            for (sessionid, title) in sessions:
                # add roomname to minor rooms, to make it easier to move
                # cell contents around in indesign
                if room.minor and not room.name in config.room_combo:
                    title += '<CharStyle:Body italic> (%s)<CharStyle:>' % room.pubsname
                ss.append(title)
            titles = ';\r\n'.join(ss)
            titles = re.sub('<i>(.*?)</i>', r'<CharStyle:Body italic>\1<CharStyle:>', titles)
            self.f.write('<CellStyle:Grid text><CellStart:%d,%d><ParaStyle:Grid text>%s<CellEnd:>' % (rows, cols, titles))
        # InDesign requires one cell per time block, even if it's
        # "covered" by a another cell
        if cols > 1:
            self.writeCellsBehind(cols - 1)

    def writeCellsBehind(self, cols):
        for i in range(cols):
            self.f.write('<CellStart:1,1><CellEnd:>')

#def offset(daytime):
#    return daytime.day.index * 24 * 2 + \
#        daytime.time.hour * 2 + \
#        int((daytime.time.minute + 15) / 30)
def offset(day, time):
    return day.index * 24 * 2 + \
        time.hour * 2 + \
        int((time.minute + 15) / 30)

# fill in the giant matrix with all sessions (do this once)
def matrix(sessions):

    # declare an array of half-hour blocks * number of rooms
    matrix = [[None for j in range(times.Day.index * 24 * 2)]
              for i in range(Room.index)]

    def fill(i, off, end, s):
        while off < min(end, len(matrix[i])):
            try:
                # two sessions share the same block iff they start at the same time
                if matrix[i][off][0].time == s.time:
                    matrix[i][off].append(s)
                else:
                    matrix[i][off] = [s]
            except (TypeError, AttributeError):
                matrix[i][off] = [s]
            off += 1

    for s in sessions:
#        off = offset(s.daytime)
#        end = offset(s.daytime + s.duration)
        off = offset(s.day, s.time)
        end = offset(s.day, s.time + s.duration)
        try:
            for r in config.room_combo[s.room.name]:
                fill(r.index, off, end, s)
        except KeyError:
            fill(s.room.index, off, end, s)

    return matrix

# slice the matrix and write it out (once for each output mode)
def write(output, matrix):

    def active_grid(grid):
        for row in grid:
            for cell in row:
                if cell:
                    return True
        return False

    def active_row(row):
        for cell in row:
            if cell:
                return True
        return False

    def colspan(i, row):
        j = i + 1
        while j < len(row) and row[j] == row[i]:
            j += 1
        return j - i

    def rowspan(i, j, grid):
        k = i
        while k < len(grid) and grid[k][j] == grid[i][j]:
            k += 1
        return k - i

    def writeSessions(gridslice, i, j, rows, cols):
        sessions = gridslice.grid[i][j]
        if not sessions:
            output.writeSessions(rows, cols, None, None)
        else:
            ss = []
            for s in sessions:
                # XXX hardcoded local policies
                title = s.title
                if 'Autograph' in title:
                    pp = []
                    for p in s.participants:
                        pp.append(str(p))
                    title = ', '.join(pp)

                tt = []
                if s.day < gridslice.start.day or \
                   (s.day == gridslice.start.day and \
                    s.time < gridslice.start.time) or \
                   s.time.minute % 30 != 0:
                    tt.append(str(s.time).replace(':00', ''))
                if s.duration < times.Duration('15min'):
                    tt.append(str(s.duration))
                if tt:
                    title += ' <i>(%s)</i>' % ', '.join(tt)

                ss.append((s.sessionid, title))
            output.writeSessions(rows, cols, ss, sessions[0].room)

    def writeTableRow(gridslice, i):
        output.writeRoom(config.room[i])
        row = gridslice.grid[i]
        j = 0
        while j < len(row):
            cols = colspan(j, row)
            # if this session was previously listed in an adjacent room, skip
            if gridslice.grid[i][j] and i > 0 and \
               gridslice.grid[i-1][j] == gridslice.grid[i][j]:
                output.writeCellsBehind(cols)
            else:
                rows = rowspan(i, j, gridslice.grid)
                writeSessions(gridslice, i, j, rows, cols)
            j += cols
        output.writeRowEnd()

    def writeTable(gridslice):
        daytime = gridslice.start
        half = times.Duration('30min')
        tt = []
        while daytime < gridslice.end:
            stime = daytime.__str__(mode='grid')
            tt.append(stime)
            daytime += half
        output.writeTableHeader(gridslice.name, tt)

        for i, g in enumerate(gridslice.grid):
            # if the table is fixed size (indesign), print all major rooms,
            # even if empty
            if active_row(g) or \
               (config.fixed[output.name] and not config.room[i].minor):
                writeTableRow(gridslice, i)
        output.writeTableEnd()

    for d in range(times.Day.index):
        day = config.day[d]
        output.writeAnchor(day.name)
        for slice in config.slice[output.name]:
            gridslice = Slice('%s %s' % (day.name, slice.name),
                              times.DayTime(day.shortname,
                                            slice.start.__str__(mode='24hr')),
                              times.DayTime(day.shortname,
                                            slice.end.__str__(mode='24hr')))
            grid = []
            start = offset(gridslice.start.day, gridslice.start.time)
            end = offset(gridslice.end.day, gridslice.end.time)
            for m in matrix:
                grid.append(m[start:end])
            if active_grid(grid):
                gridslice.grid = grid
                writeTable(gridslice)


if __name__ == '__main__':
    import cmdline

    (args, sessions, participants) = cmdline.cmdline(io=True)

    matrix = matrix(sessions)

#    if args.text:
#        if args.outfile:
#            write(TextOutput(args.outfile), matrix)
#        else:
#            write(TextOutput(config.filenames['grid', 'text']), matrix)

    if args.html:
        if args.outfile:
            write(HtmlOutput(args.outfile), matrix)
        else:
            write(HtmlOutput(config.filenames['grid', 'html']), matrix)

#    if args.xml:
#        if args.outfile:
#            write(XmlOutput(args.outfile), matrix)
#        else:
#            write(XmlOutput(config.filenames['grid', 'xml']), matrix)

    if args.indesign:
        if args.outfile:
            write(IndesignOutput(args.outfile), matrix)
        else:
            write(IndesignOutput(config.filenames['grid', 'indesign']), matrix)
