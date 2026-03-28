"""Tests for src/get_date.py"""

import re
import pytz
from datetime import datetime as real_datetime
from unittest.mock import patch

from get_date import get_current_date_in_timezone


class _FixedDatetime(real_datetime):
    @classmethod
    def now(cls, tz=None):
        return real_datetime(2026, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)


def test_result_matches_expected_format():
    # Output should look like "Saturday, March 28, 2026"
    result = get_current_date_in_timezone(pytz.UTC)
    assert re.match(r"\w+, \w+ \d+, \d{4}", result), f"Unexpected format: {result}"


def test_correct_day_and_month_for_known_date():
    # January 15, 2026 is a Thursday
    with patch("get_date.datetime", _FixedDatetime):
        result = get_current_date_in_timezone(pytz.UTC)
    assert "Thursday" in result
    assert "January" in result
    assert "15" in result
    assert "2026" in result


def test_timezone_affects_date():
    # UTC midnight vs a timezone that is behind UTC — date may differ
    # This just confirms the function runs without error for non-UTC zones
    tz = pytz.timezone("America/New_York")
    result = get_current_date_in_timezone(tz)
    assert re.match(r"\w+, \w+ \d+, \d{4}", result)
