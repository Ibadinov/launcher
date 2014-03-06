# -*- coding: utf-8 -*-

from unittest import TestCase
from launcher import schedule

from datetime import datetime
from pytz import UTC


class TestSchedule(TestCase):
    def test_parse(self):
        format, value = schedule.ptime_format('*:00')
        self.assertEquals(format, '%i')
        self.assertEquals(value, '00')
        format, value = schedule.ptime_format('12:00')
        self.assertEquals(format, '%H %i')
        self.assertEquals(value, '12 00')
        format, value = schedule.ptime_format('12:00:30')
        self.assertEquals(format, '%H %i %s')
        self.assertEquals(value, '12 00 30')

        format, value = schedule.ptime_format('01 12:00')
        self.assertEquals(format, '%d %H %i')
        self.assertEquals(value, '01 12 00')
        format, value = schedule.ptime_format('12-01 12:00')
        self.assertEquals(format, '%d %m %H %i')
        self.assertEquals(value, '01 12 12 00')
        format, value = schedule.ptime_format('2014-*-01 12:00')
        self.assertEquals(format, '%d %Y %H %i')
        self.assertEquals(value, '01 2014 12 00')

    def test_previous(self):
        result = datetime.fromtimestamp(schedule.previous('*-*-01 12:00'), tz=UTC)

        now = datetime.now(UTC)
        expectation = datetime(
            year=now.year, month=now.month, day=01, hour=12, minute=0, tzinfo=UTC
        )
        if expectation > now:
            expectation = expectation.replace(month=expectation.month-1)

        self.assertEquals(result, expectation)

    def test_next(self):
        result = datetime.fromtimestamp(schedule.next('*-*-01 12:00'), tz=UTC)

        now = datetime.now(UTC)
        expectation = datetime(
            year=now.year, month=now.month, day=01, hour=12, minute=0, tzinfo=UTC
        )
        if expectation < now:
            expectation = expectation.replace(month=expectation.month+1)

        self.assertEquals(result, expectation)
