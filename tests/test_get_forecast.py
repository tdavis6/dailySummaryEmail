"""
Tests for src/get_forecast.py.

Covers:
  - _strip_html        — pure HTML-stripping helper
  - _fmt_timestamp     — ISO 8601 / RFC 2822 timestamp formatting
  - _get_with_timeout_retry — HTTP retry logic (including recent fixes)
  - Outfit suggestions — temperature tiers, morning-low note, wind tiers,
                         precipitation codes (via mocked get_forecast())
"""

import pytest
import requests
import pytz
from datetime import datetime as real_datetime
from unittest.mock import patch, MagicMock

from get_forecast import (
    _strip_html,
    _fmt_timestamp,
    _get_with_timeout_retry,
    get_forecast,
)

# ── Shared test fixtures ───────────────────────────────────────────────────────

FIXED_DATE = "2026-01-15"
FIXED_TZ = pytz.UTC


class _FixedDatetime(real_datetime):
    """datetime subclass that freezes .now() to FIXED_DATE noon UTC.

    Inheriting from real_datetime preserves fromisoformat(), strptime(), etc.
    so the rest of get_forecast() keeps working normally.
    """

    @classmethod
    def now(cls, tz=None):
        return real_datetime(2026, 1, 15, 12, 0, 0, tzinfo=pytz.UTC)


def _make_weather_json(max_temp, min_temp, wind_speed=5, weathercode=0):
    """Minimal Open-Meteo daily forecast payload for a single day."""
    return {
        "daily": {
            "time": [FIXED_DATE],
            "temperature_2m_max": [max_temp],
            "temperature_2m_min": [min_temp],
            "apparent_temperature_max": [max_temp - 2],
            "apparent_temperature_min": [min_temp - 2],
            "precipitation_sum": [0.0],
            "windspeed_10m_max": [wind_speed],
            "uv_index_max": [3],
            "sunrise": [f"{FIXED_DATE}T06:30:00"],
            "sunset": [f"{FIXED_DATE}T17:45:00"],
            "weathercode": [weathercode],
        },
        "hourly": {
            "time": [f"{FIXED_DATE}T{h:02d}:00" for h in range(24)],
            "relativehumidity_2m": [60] * 24,
        },
    }


def _run_forecast(max_temp, min_temp, wind_speed=5, weathercode=0, unit_system="IMPERIAL"):
    """
    Call get_forecast() with mocked HTTP and a frozen date.
    Returns the full result string.
    """
    weather_json = _make_weather_json(max_temp, min_temp, wind_speed, weathercode)

    call_count = 0

    def fake_retry(url, **kwargs):
        nonlocal call_count
        call_count += 1
        resp = MagicMock()
        # First call → weather; second call → AQI (empty is fine)
        resp.json.return_value = weather_json if call_count == 1 else {}
        return resp

    with (
        patch("get_forecast._get_with_timeout_retry", side_effect=fake_retry),
        patch("get_forecast.datetime", _FixedDatetime),
        patch("get_forecast._fetch_alerts_us", return_value=""),
    ):
        return get_forecast(
            latitude=40.7128,
            longitude=-74.0060,
            country_code="us",
            city_state_str="New York, NY",
            unit_system=unit_system,
            time_system="12HR",
            timezone=FIXED_TZ,
            version="test",
        )


def _http_error(status_code):
    """Build a requests.HTTPError with a given status code."""
    err = requests.exceptions.HTTPError()
    err.response = MagicMock(status_code=status_code)
    return err


# ── _strip_html ────────────────────────────────────────────────────────────────

class TestStripHtml:
    def test_removes_tags(self):
        assert _strip_html("<b>hello</b>") == "hello"

    def test_collapses_whitespace(self):
        assert _strip_html("<p>  foo   bar  </p>") == "foo bar"

    def test_plain_text_unchanged(self):
        assert _strip_html("no tags here") == "no tags here"

    def test_empty_string(self):
        assert _strip_html("") == ""

    def test_nested_tags(self):
        assert _strip_html("<div><span>text</span></div>") == "text"


# ── _fmt_timestamp ─────────────────────────────────────────────────────────────

class TestFmtTimestamp:
    def test_iso_8601_24hr(self):
        result = _fmt_timestamp("2026-01-15T08:30:00+00:00", "24HR", pytz.UTC)
        assert "08:30" in result

    def test_iso_8601_12hr(self):
        result = _fmt_timestamp("2026-01-15T08:30:00+00:00", "12HR", pytz.UTC)
        assert "08:30 AM" in result

    def test_rfc_2822(self):
        result = _fmt_timestamp("Thu, 15 Jan 2026 08:30:00 +0000", "24HR", pytz.UTC)
        assert "08:30" in result

    def test_empty_returns_empty(self):
        assert _fmt_timestamp("", "12HR", pytz.UTC) == ""

    def test_unparseable_returns_raw(self):
        raw = "not-a-date"
        assert _fmt_timestamp(raw, "12HR", pytz.UTC) == raw


# ── _get_with_timeout_retry ────────────────────────────────────────────────────

class TestGetWithTimeoutRetry:
    def test_returns_on_first_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        with patch("requests.get", return_value=mock_resp):
            result = _get_with_timeout_retry("http://example.com")
        assert result is mock_resp

    def test_retries_on_504(self):
        with patch("requests.get", return_value=MagicMock()) as mock_get, \
             patch("time.sleep"):
            mock_get.return_value.raise_for_status.side_effect = [
                _http_error(504),
                None,
            ]
            _get_with_timeout_retry(
                "http://example.com",
                initial_retry_delay=0.01,
                max_elapsed_seconds=30,
            )
        assert mock_get.call_count == 2

    def test_retries_on_429(self):
        with patch("requests.get", return_value=MagicMock()) as mock_get, \
             patch("time.sleep"):
            mock_get.return_value.raise_for_status.side_effect = [
                _http_error(429),
                None,
            ]
            _get_with_timeout_retry(
                "http://example.com",
                initial_retry_delay=0.01,
                max_elapsed_seconds=30,
            )
        assert mock_get.call_count == 2

    def test_no_retry_on_404(self):
        with patch("requests.get", return_value=MagicMock()) as mock_get:
            mock_get.return_value.raise_for_status.side_effect = _http_error(404)
            with pytest.raises(requests.exceptions.HTTPError):
                _get_with_timeout_retry("http://example.com")
        assert mock_get.call_count == 1

    def test_retries_on_timeout(self):
        ok_resp = MagicMock()
        ok_resp.raise_for_status.return_value = None
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = [requests.exceptions.Timeout(), ok_resp]
            _get_with_timeout_retry(
                "http://example.com",
                initial_retry_delay=0.01,
                max_elapsed_seconds=30,
            )
        assert mock_get.call_count == 2

    def test_retries_on_connection_error(self):
        ok_resp = MagicMock()
        ok_resp.raise_for_status.return_value = None
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = [requests.exceptions.ConnectionError(), ok_resp]
            _get_with_timeout_retry(
                "http://example.com",
                initial_retry_delay=0.01,
                max_elapsed_seconds=30,
            )
        assert mock_get.call_count == 2

    def test_retries_on_chunked_encoding_error(self):
        """ChunkedEncodingError (504 body dropped mid-transfer) must be retried."""
        ok_resp = MagicMock()
        ok_resp.raise_for_status.return_value = None
        with patch("requests.get") as mock_get, patch("time.sleep"):
            mock_get.side_effect = [
                requests.exceptions.ChunkedEncodingError(),
                ok_resp,
            ]
            _get_with_timeout_retry(
                "http://example.com",
                initial_retry_delay=0.01,
                max_elapsed_seconds=30,
            )
        assert mock_get.call_count == 2

    def test_retries_when_http_error_has_no_response(self):
        """HTTPError with response=None should be treated as transient and retried."""
        err = requests.exceptions.HTTPError()
        err.response = None
        ok_resp = MagicMock()
        ok_resp.raise_for_status.return_value = None
        with patch("requests.get", return_value=MagicMock()) as mock_get, \
             patch("time.sleep"):
            mock_get.return_value.raise_for_status.side_effect = [err, None]
            _get_with_timeout_retry(
                "http://example.com",
                initial_retry_delay=0.01,
                max_elapsed_seconds=30,
            )
        assert mock_get.call_count == 2

    def test_gives_up_after_max_elapsed(self):
        """Once max_elapsed_seconds is exceeded, the last exception is re-raised."""
        with patch("requests.get", return_value=MagicMock()) as mock_get, \
             patch("time.sleep"):
            mock_get.return_value.raise_for_status.side_effect = _http_error(503)
            with pytest.raises(requests.exceptions.HTTPError):
                # max_elapsed_seconds=0 causes remaining to go negative after
                # the very first failure, so the function gives up immediately.
                _get_with_timeout_retry(
                    "http://example.com",
                    initial_retry_delay=0.01,
                    max_elapsed_seconds=0,
                )


# ── Outfit suggestions ─────────────────────────────────────────────────────────

class TestOutfitSuggestionsImperial:
    """
    Outfit suggestion logic — Imperial thresholds:
      hot=86°F, warm=68°F, chilly=50°F, cold=32°F, very_cold=10°F
      windy=20 mph
    """

    # Temperature tiers --------------------------------------------------------

    def test_hot(self):
        result = _run_forecast(max_temp=90, min_temp=72)
        assert "light, breathable" in result

    def test_warm(self):
        result = _run_forecast(max_temp=75, min_temp=60)
        assert "t-shirt" in result

    def test_chilly(self):
        result = _run_forecast(max_temp=55, min_temp=45)
        assert "light jacket" in result

    def test_cold(self):
        result = _run_forecast(max_temp=40, min_temp=25)
        assert "coat and scarf" in result
        assert "thermals" not in result

    def test_very_cold(self):
        result = _run_forecast(max_temp=20, min_temp=5)
        assert "thermals" in result
        assert "gloves" in result

    def test_extreme_cold(self):
        result = _run_forecast(max_temp=5, min_temp=-5)
        assert "dangerously cold" in result
        assert "face protection" in result

    # Morning low note ---------------------------------------------------------

    def test_warm_day_cold_morning_adds_drop_note(self):
        # max=65 > chilly(50), min=42 <= chilly(50) → note should appear
        result = _run_forecast(max_temp=65, min_temp=42)
        assert "Temperatures drop to" in result
        assert "42" in result

    def test_uniformly_warm_no_drop_note(self):
        result = _run_forecast(max_temp=75, min_temp=60)
        assert "Temperatures drop to" not in result

    def test_uniformly_cold_no_drop_note(self):
        # max=30 is not > chilly(50), so condition is false
        result = _run_forecast(max_temp=30, min_temp=20)
        assert "Temperatures drop to" not in result

    def test_chilly_day_exactly_at_threshold_no_drop_note(self):
        # max=51 > chilly(50), min=51 > chilly(50) → no note
        result = _run_forecast(max_temp=51, min_temp=51)
        assert "Temperatures drop to" not in result

    # Wind tiers ---------------------------------------------------------------

    def test_windy_hot_suggests_breathable_layer(self):
        # max=80 > warm(68)
        result = _run_forecast(max_temp=80, min_temp=65, wind_speed=25)
        assert "breathable layer" in result

    def test_windy_moderate_suggests_windbreaker(self):
        # max=55: warm(68) >= max > cold(32)
        result = _run_forecast(max_temp=55, min_temp=45, wind_speed=25)
        assert "windbreaker" in result

    def test_windy_cold_suggests_windproof_insulated(self):
        # max=25 <= cold(32)
        result = _run_forecast(max_temp=25, min_temp=10, wind_speed=25)
        assert "windproof" in result
        assert "insulated" in result

    def test_calm_no_wind_suggestion(self):
        result = _run_forecast(max_temp=70, min_temp=55, wind_speed=5)
        assert "windbreaker" not in result
        assert "windproof" not in result
        assert "breathable layer" not in result

    # Precipitation codes ------------------------------------------------------

    def test_rain_code_suggests_umbrella(self):
        result = _run_forecast(max_temp=60, min_temp=50, weathercode=61)
        assert "umbrella" in result

    def test_heavy_rain_code_suggests_umbrella(self):
        result = _run_forecast(max_temp=55, min_temp=45, weathercode=65)
        assert "umbrella" in result

    def test_snow_code_suggests_waterproof_boots(self):
        result = _run_forecast(max_temp=28, min_temp=18, weathercode=71)
        assert "waterproof boots" in result

    def test_thunderstorm_code_suggests_umbrella(self):
        result = _run_forecast(max_temp=70, min_temp=60, weathercode=95)
        assert "umbrella" in result

    def test_clear_sky_no_precip_suggestion(self):
        result = _run_forecast(max_temp=70, min_temp=55, weathercode=0)
        assert "umbrella" not in result
        assert "waterproof boots" not in result


class TestOutfitSuggestionsMetric:
    """Smoke-test that metric thresholds work (hot=30°C, warm=20°C, chilly=10°C)."""

    def test_hot_metric(self):
        result = _run_forecast(max_temp=35, min_temp=25, unit_system="METRIC")
        assert "light, breathable" in result

    def test_extreme_cold_metric(self):
        # very_cold_thresh in metric is -12°C; need max <= -12 to hit extreme tier
        result = _run_forecast(max_temp=-15, min_temp=-25, unit_system="METRIC")
        assert "dangerously cold" in result

    def test_morning_drop_note_metric(self):
        # max=15 > chilly(10), min=5 <= chilly(10)
        result = _run_forecast(max_temp=15, min_temp=5, unit_system="METRIC")
        assert "Temperatures drop to" in result
