"""Tests for src/get_caldav_events.py — JSON parsing and error handling."""

import json
import sys
from unittest.mock import MagicMock, patch

import pytz
import pytest

from get_caldav_events import get_caldav_events, _resolve_url


# ── _resolve_url ───────────────────────────────────────────────────────────────

class TestResolveUrl:
    def test_icloud_no_override(self):
        assert _resolve_url("icloud", "user@icloud.com", "") == "https://caldav.icloud.com"

    def test_google_interpolates_username(self):
        url = _resolve_url("google", "user@gmail.com", "")
        assert "user@gmail.com" in url
        assert "google.com" in url

    def test_microsoft_interpolates_username(self):
        url = _resolve_url("microsoft", "user@outlook.com", "")
        assert "user@outlook.com" in url
        assert "office365" in url

    def test_webdav_requires_override(self):
        assert _resolve_url("webdav", "user", "") is None

    def test_explicit_url_takes_precedence(self):
        override = "https://my.server.com/dav/"
        assert _resolve_url("icloud", "user@icloud.com", override) == override


# ── get_caldav_events — input validation ───────────────────────────────────────

class TestGetCaldavEventsInputValidation:
    TZ = pytz.timezone("America/Los_Angeles")

    def test_none_returns_empty(self):
        assert get_caldav_events(None, self.TZ) == []

    def test_empty_string_returns_empty(self):
        assert get_caldav_events("", self.TZ) == []

    def test_invalid_json_returns_empty(self):
        assert get_caldav_events("not json", self.TZ) == []

    def test_json_object_not_array_returns_empty(self):
        assert get_caldav_events('{"type":"icloud"}', self.TZ) == []

    def test_empty_array_returns_empty(self):
        assert get_caldav_events("[]", self.TZ) == []


# ── get_caldav_events — connection failures ────────────────────────────────────

class TestGetCaldavEventsConnectionFailure:
    TZ = pytz.timezone("America/Los_Angeles")

    def test_failed_connection_returns_empty_not_raises(self):
        accounts = json.dumps([{"type": "icloud", "username": "u", "password": "p"}])
        mock_caldav = MagicMock()
        mock_caldav.DAVClient.return_value.principal.side_effect = Exception("auth failed")
        with patch.dict(sys.modules, {"caldav": mock_caldav}):
            result = get_caldav_events(accounts, self.TZ)
        assert result == []

    def test_missing_url_for_webdav_returns_empty(self):
        accounts = json.dumps([{"type": "webdav", "username": "u", "password": "p"}])
        with patch.dict(sys.modules, {"caldav": MagicMock()}):
            result = get_caldav_events(accounts, self.TZ)
        assert result == []

    def test_non_dict_entry_is_skipped(self):
        accounts = json.dumps(["not-a-dict", {"type": "icloud", "username": "u", "password": "p"}])
        mock_caldav = MagicMock()
        mock_caldav.DAVClient.return_value.principal.side_effect = Exception("auth failed")
        with patch.dict(sys.modules, {"caldav": mock_caldav}):
            result = get_caldav_events(accounts, self.TZ)
        assert result == []
