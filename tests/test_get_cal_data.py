"""Tests for src/get_cal_data.py — ensure_datetime, localize_or_convert, handle_all_day_event."""

import pytz
from datetime import datetime, date, timedelta

from get_cal_data import ensure_datetime, localize_or_convert, handle_all_day_event


# ── ensure_datetime ────────────────────────────────────────────────────────────

class TestEnsureDatetime:
    def test_date_becomes_datetime_at_midnight(self):
        d = date(2026, 1, 15)
        result = ensure_datetime(d)
        assert isinstance(result, datetime)
        assert result.year == 2026
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0

    def test_datetime_returned_unchanged(self):
        dt = datetime(2026, 1, 15, 10, 30)
        assert ensure_datetime(dt) is dt


# ── localize_or_convert ────────────────────────────────────────────────────────

class TestLocalizeOrConvert:
    def test_naive_datetime_gets_timezone_attached(self):
        tz = pytz.timezone("America/New_York")
        naive = datetime(2026, 1, 15, 10, 0)
        result = localize_or_convert(naive, tz)
        assert result.tzinfo is not None

    def test_aware_datetime_is_converted(self):
        utc_dt = datetime(2026, 1, 15, 15, 0, tzinfo=pytz.UTC)
        est = pytz.timezone("America/New_York")
        result = localize_or_convert(utc_dt, est)
        # 15:00 UTC = 10:00 EST
        assert result.hour == 10
        assert result.tzinfo is not None


# ── handle_all_day_event ───────────────────────────────────────────────────────

class TestHandleAllDayEvent:
    def _make_event(self, start, end):
        return {"start": start, "end": end}

    def test_single_day_event_returns_all_day(self):
        # ICS end date is exclusive, so end = start + 1 day → single day
        start = datetime(2026, 1, 15, 0, 0, tzinfo=pytz.UTC)
        end = datetime(2026, 1, 16, 0, 0, tzinfo=pytz.UTC)
        result = handle_all_day_event(self._make_event(start, end))
        assert result == "\n\nAll day event"

    def test_multi_day_event_includes_end_date(self):
        # start Jan 15, end Jan 18 (exclusive) → corrected end = Jan 17
        start = datetime(2026, 1, 15, 0, 0, tzinfo=pytz.UTC)
        end = datetime(2026, 1, 18, 0, 0, tzinfo=pytz.UTC)
        result = handle_all_day_event(self._make_event(start, end))
        assert "ends" in result.lower()
        assert "January 17, 2026" in result

    def test_two_day_event_includes_end_date(self):
        # start Jan 15, end Jan 17 (exclusive) → corrected end = Jan 16
        start = datetime(2026, 1, 15, 0, 0, tzinfo=pytz.UTC)
        end = datetime(2026, 1, 17, 0, 0, tzinfo=pytz.UTC)
        result = handle_all_day_event(self._make_event(start, end))
        assert "January 16, 2026" in result
