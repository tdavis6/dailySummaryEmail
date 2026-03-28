"""Tests for src/get_todo_tasks.py — format_time and parse_task_sections."""

from datetime import datetime

from get_todo_tasks import format_time, parse_task_sections


# ── format_time ────────────────────────────────────────────────────────────────

class TestFormatTime:
    def test_12hr_morning(self):
        dt = datetime(2026, 1, 15, 9, 30)
        assert format_time(dt, "12HR") == "09:30 AM"

    def test_12hr_afternoon(self):
        dt = datetime(2026, 1, 15, 14, 0)
        assert format_time(dt, "12HR") == "02:00 PM"

    def test_12hr_midnight(self):
        dt = datetime(2026, 1, 15, 0, 0)
        assert format_time(dt, "12HR") == "12:00 AM"

    def test_12hr_noon(self):
        dt = datetime(2026, 1, 15, 12, 0)
        assert format_time(dt, "12HR") == "12:00 PM"

    def test_24hr(self):
        dt = datetime(2026, 1, 15, 14, 30)
        assert format_time(dt, "24HR") == "14:30"

    def test_24hr_midnight(self):
        dt = datetime(2026, 1, 15, 0, 0)
        assert format_time(dt, "24HR") == "00:00"


# ── parse_task_sections ────────────────────────────────────────────────────────

class TestParseTaskSections:
    def test_empty_input_returns_empty(self):
        assert parse_task_sections("") == ""

    def test_only_header_returns_empty(self):
        # "# Tasks" with no real tasks → no output
        assert parse_task_sections("# Tasks") == ""

    def test_regular_task_goes_to_general(self):
        result = parse_task_sections("# Tasks\n - Buy milk")
        assert "## General Tasks" in result
        assert "Buy milk" in result

    def test_overdue_task_goes_to_overdue_section(self):
        result = parse_task_sections("# Tasks\n - Fix bug ⚠️ Overdue · Jan 10")
        assert "## Overdue Tasks" in result
        assert "Fix bug" in result

    def test_deadline_passed_goes_to_overdue_section(self):
        result = parse_task_sections("# Tasks\n - Old task 🚨 Deadline passed · Jan 5")
        assert "## Overdue Tasks" in result

    def test_multiple_tasks_split_correctly(self):
        text = "# Tasks\n - Normal task\n - Late task ⚠️ Overdue · Jan 1"
        result = parse_task_sections(text)
        assert "## General Tasks" in result
        assert "## Overdue Tasks" in result

    def test_output_starts_with_tasks_header(self):
        result = parse_task_sections("# Tasks\n - Do something")
        assert result.startswith("# Tasks")
