"""Tests for src/add_emojis.py"""

from datetime import datetime, timedelta

from add_emojis import add_emojis


def test_empty_string_returns_empty():
    assert add_emojis("") == ""


def test_known_keyword_gets_emoji():
    # "coffee" → ☕
    result = add_emojis("Tasks\n- Make coffee")
    assert "☕" in result


def test_header_line_preserved_unchanged():
    # Lines starting with "## " are skipped — no emoji added
    result = add_emojis("Tasks\n## Morning Tasks\n- Make coffee")
    assert result.startswith("Tasks")
    # The section header itself should not have an emoji appended to it
    assert "## Morning Tasks ☕" not in result


def test_url_in_task_is_preserved():
    result = add_emojis("Tasks\n- Check https://example.com/coffee for updates")
    assert "https://example.com/coffee" in result


def test_task_without_due_date_is_not_marked_overdue():
    # No due date → treated as today → days_late == 0 → no overdue emoji
    result = add_emojis("Tasks\n- Buy groceries")
    assert "⚠️" not in result
    assert "🔥" not in result


def test_recently_overdue_task_gets_warning_emoji():
    # 3 days ago → days_late == 3 → ⚠️
    three_days_ago = (datetime.now() - timedelta(days=3)).strftime("%A, %B %d, %Y")
    result = add_emojis(f"Tasks\n- Submit report due on {three_days_ago}")
    assert "⚠️" in result


def test_long_overdue_task_gets_fire_emoji():
    # A date well in the past (> 7 days) → 🔥
    result = add_emojis("Tasks\n- Old task due on Monday, January 01, 2024")
    assert "🔥" in result


def test_multiple_keywords_in_one_task():
    result = add_emojis("Tasks\n- Morning workout and coffee")
    assert "💪" in result
    assert "☕" in result
