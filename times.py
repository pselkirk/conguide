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

# had to rename time.py to times.py, because import was pulling in the
# builtin 'time' module

""" Time and day related classes. """

import copy
import re
from functools import total_ordering

@total_ordering
class Day:
    """ Day class. """
    # XXX add day/month/year for guidebook?
    __DAY__ = {'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday',
               'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday',
               'Sun': 'Sunday'}
    index = 0

    def __init__(self, shortname):
        """ Days are instantitated from config.py, such that Friday is day 0. """
        self.shortname = shortname
        self.name = Day.__DAY__[shortname]
        # KeyError on bad shortname

    def __lt__(self, other):
        return (other and (self.index < other.index))

    def __eq__(self, other):
        return (other and (self.index == other.index))

    def __ne__(self, other):
        return not (self == other)

    def __str__(self):
        return self.name

@total_ordering
class Time:
    """ Time class. """

    def __init__(self, string):
        """ Times are instantiated from session.py, from a 12-hour time string. """
        m = re.match(r'(\d{,2}):(\d{,2}) ?([AP]M)', string, flags=re.IGNORECASE)
        if m:
            self.hour = int(m.group(1))
            self.minute = int(m.group(2))
            ampm = m.group(3).upper()
            if self.hour == 12:
                if ampm == 'AM':
                    self.hour = 0
            elif ampm == 'PM':
                self.hour += 12
        else:
            # 24-hour time
            m = re.match(r'(\d{,2}):(\d{,2})', string)
            if m:
                self.hour = int(m.group(1))
                self.minute = int(m.group(2))
            else:
                raise ValueError('invalid initialization string for Time: \'%s\'' % string)

    def __lt__(self, other):
        return (other and ((self.hour < other.hour) or \
                           ((self.hour == other.hour) and \
                            (self.minute < other.minute))))

    def __eq__(self, other):
        return (other and (self.hour == other.hour) and (self.minute == other.minute))

    def __ne__(self, other):
        return not (self == other)

    def __str__(self, mode=None):
        if mode == '24hr':
            return '%d:%02d' % (self.hour, self.minute)
        else:
            hour = self.hour
            if hour >= 24:
                hour -= 24
            if mode == 'grid':
                if hour == 0 and self.minute == 0:
                    return 'midnight'
                elif hour == 12 and self.minute == 0:
                    return 'noon'
                else:
                    if hour < 12:
                        ampm = 'a'
                    else:
                        hour -= 12
                        ampm = 'p'
            else:
                if hour < 12:
                    ampm = 'am'
                else:
                    hour -= 12
                    ampm = 'pm'
            if hour == 0:
                hour = 12
            return '%d:%02d%s' % (hour, self.minute, ampm)

    def __add__(self, other):
        if not isinstance(other, Time):
            raise TypeError('can only add Time or Duration to Time')
        t = copy.copy(self)
        t.hour += other.hour
        t.minute += other.minute
        if t.minute >= 60:
            t.hour += 1
            t.minute -= 60
        return t

import config

@total_ordering
class DayTime(Time):
    """ DayTime class - a concatenation of Day and Time,
    currently only used in grid.py.
    """
    def __init__(self, day, time):
        self.day = config.day[day]
        self.time = Time(time)
        if self.time.hour >= 24:
            self.day = config.day[self.day.index + 1]
            self.time.hour -= 24

    def __lt__(self, other):
        return (other and ((self.day < other.day) or \
                           ((self.day == other.day) and \
                            (self.time < other.time))))

    def __eq__(self, other):
        return (other and \
                self.day == other.day and \
                self.time == other.time)

    def __str__(self, mode=None):
        if mode == 'grid':
            return self.time.__str__(mode)
        else:
            return self.day.__str__() + ' ' + self.time.__str__()

    def __add__(self, other):
        if not isinstance(other, Time):
            raise TypeError('can only add Time or Duration to DayTime')
        dt = copy.copy(self)
        dt.time += other
        if dt.time.hour >= 24:
            dt.day = config.day[dt.day.index + 1]
            dt.time.hour -= 24
        return dt

class Duration(Time):
    """" Duration class. Internally, a Duration is identical to a Time,
    but the initialization and presentation strings are different.
    """
    def __init__(self, string):
        m = re.match(r'(\d{,2}) ?hr', string, flags=re.IGNORECASE)
        if m:
            self.hour = int(m.group(1))
        else:
            self.hour = 0
        m = re.search(r'(\d{,2}) ?min', string, flags=re.IGNORECASE)
        if m:
            self.minute = int(m.group(1))
        else:
            self.minute = 0
        if self.hour == 0 and self.minute == 0:
            # maybe this is in time format
            m = re.match(r'(\d{,2}):(\d{,2})', string)
            if m:
                self.hour = int(m.group(1))
                self.minute = int(m.group(2))
            else:
                raise ValueError('invalid initialization string for Duration: \'%s\'' % string)

    def __str__(self):
        if not self.minute:
            return '%dhr' % self.hour
        elif not self.hour:
            return '%dmin' % self.minute
        else:
            return '%dhr %dmin' % (self.hour, self.minute)

if __name__ == '__main__':
    for i in range(7):
        print('{0}: {1}'.format(config.day[i].index, config.day[i].name))

    print(Time('4:15 PM'))
    print(Time('16:15'))
    print(Duration('3hr 55min'))
    print(Duration('03:55'))
    print(DayTime('Fri', '4:15 PM'))
    print(Time('4:45 PM') + Duration('1hr 15min'))
    print(Time('11:30 PM') + Duration('6hr'))
    print(DayTime('Sat', '11:30 PM') + Duration('6hr'))
    print(DayTime('Sat', '11:30 PM') + Time('06:00'))
