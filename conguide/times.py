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

# had to rename time.py to times.py, because import was pulling in the
# builtin 'time' module

""" Time and day related classes. """

import copy
import re
from functools import total_ordering

@total_ordering
class Day(object):
    """ Day class.

    Parameters:

    name: str
        Can be a long name ('Friday') or a short name ('Fri')
    """

    # class variables
    _DAY_ = {'Mon': 'Monday', 'Tue': 'Tuesday', 'Wed': 'Wednesday',
             'Thu': 'Thursday', 'Fri': 'Friday', 'Sat': 'Saturday',
             'Sun': 'Sunday',
             'Monday': 'Mon', 'Tuesday': 'Tue', 'Wednesday': 'Wed',
             'Thursday': 'Thu', 'Friday': 'Fri', 'Saturday': 'Sat',
             'Sunday': 'Sun'}
    index = 0
    days = []

    # TODO: add day/month/year for guidebook?

    def __init__(self, name):
        for day in Day.days:
            if name == day.name or name == day.shortname:
                self.__dict__ = day.__dict__
                return

        if len(name) == 3:
            self.shortname = name
            self.name = Day._DAY_[name]
        else:
            self.name = name
            self.shortname = Day._DAY_[name]
        # KeyError on bad name
        self.index = Day.index
        Day.index += 1
        Day.days.append(self)
        self.time = []

    def __lt__(self, other):
        return other and (self.index < other.index)

    def __eq__(self, other):
        return other and (self.name == other.name)

    def __ne__(self, other):
        return not self == other

    def __str__(self):
        return self.name

@total_ordering
class Time(object):
    """ Time class.

    Parameters:

    string: str
        Can be American time (e.g. 2:30pm) or 24-hour time (e.g. 14:30).
        Note that am/pm is case-insensitive, and there can be a space between
        the time and the am/pm string.
    day: Day
        Optional reference to a Day object.
    """

    def __init__(self, string, day=None):
        m = re.match(r'(\d{,2}):(\d{,2}) ?([AP]M)', string,
                     flags=re.IGNORECASE)
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
                raise ValueError(
                    'invalid initialization string for Time: \'%s\'' % string)
        self.session = []
        self.day = day

    def __lt__(self, other):
        if not other:
            return False
        elif self.day and other.day:
            # Friday 24:00 and Saturday 0:00 should be equal
            h1 = self.day.index * 24 + self.hour
            h2 = other.day.index * 24 + other.hour
            return h1 < h2 or \
                h1 == h2 and self.minute < other.minute
        else:
            return self.hour < other.hour or \
                self.hour == other.hour and self.minute < other.minute

    def __eq__(self, other):
        if not other:
            return False
        elif self.day and other.day:
            h1 = self.day.index * 24 + self.hour
            h2 = other.day.index * 24 + other.hour
            return h1 == h2 and self.minute == other.minute
        else:
            return self.hour == other.hour and self.minute == other.minute

    def __ne__(self, other):
        return not self == other

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
        # if time overflows to the next day, normalize it
        #if t.day:
        #    if t.hour > 23:
        #        t.hour -= 24
        #        t.day = Day.days[t.day.index + 1]
        return t

    def __sub__(self, other):
        if not isinstance(other, Time):
            raise TypeError('can only subtract Time or Duration from Time')
        t = copy.copy(self)
        t.hour -= other.hour
        t.minute -= other.minute
        if t.minute >= 60:
            t.hour -= 1
            t.minute += 60
        return t

class Duration(Time):
    """ Duration class. Internally, a Duration is identical to a Time,
    but the initialization and presentation strings are different.

    Parameters:

    string: str
        Can be of the form '2hr 30min', or an absolute number of minutes (150).
    """
    def __init__(self, string):
        self.day = None
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
                # bare number of minutes
                m = re.match(r'^(\d+)$', string)
                if m:
                    (self.hour, self.minute) = divmod(int(m.group(1)), 60)
                else:
                    raise ValueError(
                        'invalid initialization string for Duration: ' +
                        '\'%s\'' % string)

    def __str__(self):
        if not self.minute:
            return '%dhr' % self.hour
        elif not self.hour:
            return '%dmin' % self.minute
        else:
            return '%dhr %dmin' % (self.hour, self.minute)

if __name__ == '__main__':

    test = ["Time('4:15 PM')", \
            "Time('16:15')", \
            "Time('6:00am')", \
            "Duration('3hr 55min')", \
            "Duration('03:55')", \
            "Duration('235')", \
            "Time('4:45 PM') + Duration('1hr 15min')", \
            "Time('11:30 PM') + Duration('6hr')", \
            "Time('6:00am') > Time('6:00pm')", \
            "Time('6:00am') < Time('6:00pm')", \
            "Time('6:00am') == Time('6:00pm')"]

    for a in test:
        print('%s = %s' % (a, eval(a)))
