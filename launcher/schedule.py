# -*- coding: utf-8 -*-
"""
    launcher
    ~~~~~~~~

    :copyright: (c) 2014 by Marat Ibadinov.
    :license: MIT, see LICENSE for more details.
"""

import calendar
import ptime

from datetime import datetime


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
    schedules = [schedule] if isinstance(schedule, basestring) else schedule
    return min([_parse(True, schedule, base) for schedule in schedules])


def previous(schedule, base=None):
    schedules = [schedule] if isinstance(schedule, basestring) else schedule
    return max([_parse(False, schedule, base) for schedule in schedules])


def _parse(prefer_future, schedule, base=None):
    if (base):
        base = datetime.fromtimestamp(base)
    format, value = ptime_format(schedule)
    parser = ptime.Parser(ptime.Format(format), None, prefer_future)
    result = parser.parse(value, base)
    return calendar.timegm(result.utctimetuple())
