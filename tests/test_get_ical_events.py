"""Tests for src/get_ical_events.py — make_aware, is_event_today, parse_icalendar."""

import pytz
from datetime import datetime, date

from get_ical_events import make_aware, is_event_today, parse_icalendar


# ── make_aware ─────────────────────────────────────────────────────────────────

class TestMakeAware:
    def test_naive_datetime_gets_timezone(self):
        tz = pytz.UTC
        naive = datetime(2026, 1, 15, 10, 0)
        result = make_aware(naive, tz)
        assert result.tzinfo is not None

    def test_already_aware_datetime_returned_as_is(self):
        tz = pytz.UTC
        aware = datetime(2026, 1, 15, 10, 0, tzinfo=pytz.UTC)
        result = make_aware(aware, tz)
        assert result is aware

    def test_date_object_becomes_aware_datetime(self):
        tz = pytz.UTC
        d = date(2026, 1, 15)
        result = make_aware(d, tz)
        assert isinstance(result, datetime)
        assert result.tzinfo is not None
        assert result.date() == d


# ── is_event_today ─────────────────────────────────────────────────────────────

class TestIsEventToday:
    def test_event_starting_and_ending_today_is_today(self):
        tz = pytz.UTC
        today = datetime.now(tz).date()
        start = datetime(today.year, today.month, today.day, 10, 0)
        end = datetime(today.year, today.month, today.day, 11, 0)
        assert is_event_today(start, end, tz) is True

    def test_event_in_the_past_is_not_today(self):
        tz = pytz.UTC
        assert is_event_today(
            datetime(2020, 1, 1, 10, 0),
            datetime(2020, 1, 1, 11, 0),
            tz,
        ) is False

    def test_event_in_the_future_is_not_today(self):
        tz = pytz.UTC
        assert is_event_today(
            datetime(2099, 6, 1, 10, 0),
            datetime(2099, 6, 1, 11, 0),
            tz,
        ) is False

    def test_all_day_event_today_is_today(self):
        # All-day: start = today 00:00, end = tomorrow 00:00 (ICS exclusive)
        tz = pytz.UTC
        today = datetime.now(tz).date()
        start = date(today.year, today.month, today.day)
        end = date(today.year, today.month, today.day + 1)
        assert is_event_today(start, end, tz) is True


# ── parse_icalendar ────────────────────────────────────────────────────────────

class TestParseIcalendar:
    def test_empty_string_returns_empty_list(self):
        assert parse_icalendar("") == []

    def test_none_returns_empty_list(self):
        assert parse_icalendar(None) == []

    def test_single_event_is_parsed(self):
        ical = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "DTSTART:20260115T100000Z\r\n"
            "DTEND:20260115T110000Z\r\n"
            "SUMMARY:Team Meeting\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        events = parse_icalendar(ical)
        assert len(events) == 1
        assert events[0]["summary"] == "Team Meeting"

    def test_event_start_and_end_are_present(self):
        ical = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "DTSTART:20260115T140000Z\r\n"
            "DTEND:20260115T150000Z\r\n"
            "SUMMARY:Test\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        events = parse_icalendar(ical)
        assert "start" in events[0]
        assert "end" in events[0]

    def test_event_with_no_title_defaults_to_no_title(self):
        ical = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "DTSTART:20260115T100000Z\r\n"
            "DTEND:20260115T110000Z\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        events = parse_icalendar(ical)
        assert events[0]["summary"] == "No Title"

    def test_multiple_events_all_parsed(self):
        ical = (
            "BEGIN:VCALENDAR\r\n"
            "VERSION:2.0\r\n"
            "BEGIN:VEVENT\r\n"
            "DTSTART:20260115T090000Z\r\n"
            "DTEND:20260115T100000Z\r\n"
            "SUMMARY:Event One\r\n"
            "END:VEVENT\r\n"
            "BEGIN:VEVENT\r\n"
            "DTSTART:20260115T110000Z\r\n"
            "DTEND:20260115T120000Z\r\n"
            "SUMMARY:Event Two\r\n"
            "END:VEVENT\r\n"
            "END:VCALENDAR\r\n"
        )
        events = parse_icalendar(ical)
        assert len(events) == 2
        summaries = {e["summary"] for e in events}
        assert summaries == {"Event One", "Event Two"}
