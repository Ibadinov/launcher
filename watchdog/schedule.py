# -*- coding: utf-8 -*-
"""
    watchdog
    ~~~~~~~~

    :copyright: (c) 2014 by Marat Ibadinov.
    :license: MIT, see LICENSE for more details.
"""

import calendar
import ptime


def ptime_format(schedule):
    date, time = ([''] + schedule.split(' '))[-2:]

    placeholders = ['%H', '%i', '%s']
    time = time.split(':')
    time_format = [placeholders[index] for index, value in enumerate(time) if value != '*']
    time = [value for value in time if value != '*']

    placeholders = ['%d', '%m', '%Y']
    date = date.split('-')[::-1] if date else []
    date_format = [placeholders[index] for index, value in enumerate(date) if value != '*']
    date = [value for value in date if value != '*']

    return (' '.join(date_format + time_format), ' '.join(date + time))


def next(schedule, base=None):
    return _parse(True, schedule, base)


def previous(schedule, base=None):
    return _parse(False, schedule, base)


def _parse(prefer_future, schedule, base=None):
    if (base):
        base = datetime.fromtimestamp(base)
    format, value = ptime_format(schedule)
    parser = ptime.Parser(ptime.Format(format), None, prefer_future)
    datetime = parser.parse(value, base)
    return calendar.timegm(datetime.utctimetuple())
