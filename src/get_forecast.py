import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime

import requests


# MeteoAlarm RSS feed slugs keyed by ISO 3166-1 alpha-2 country code (lowercase).
# Source: https://feeds.meteoalarm.org/
_METEOALARM_SLUGS = {
    "ad": "andorra",
    "at": "austria",
    "be": "belgium",
    "ba": "bosnia-herzegovina",
    "bg": "bulgaria",
    "hr": "croatia",
    "cy": "cyprus",
    "cz": "czechia",
    "dk": "denmark",
    "ee": "estonia",
    "fi": "finland",
    "fr": "france",
    "de": "germany",
    "gr": "greece",
    "hu": "hungary",
    "is": "iceland",
    "ie": "ireland",
    "il": "israel",
    "it": "italy",
    "lv": "latvia",
    "lt": "lithuania",
    "lu": "luxembourg",
    "mt": "malta",
    "md": "moldova",
    "me": "montenegro",
    "nl": "netherlands",
    "mk": "republic-of-north-macedonia",
    "no": "norway",
    "pl": "poland",
    "pt": "portugal",
    "ro": "romania",
    "rs": "serbia",
    "sk": "slovakia",
    "si": "slovenia",
    "es": "spain",
    "se": "sweden",
    "ch": "switzerland",
    "ua": "ukraine",
    "gb": "united-kingdom",
}

_HTTP_TIMEOUT_SECONDS = 10
_HTTP_INITIAL_RETRY_DELAY_SECONDS = 10
_HTTP_MAX_RETRY_DELAY_SECONDS = 60
_HTTP_MAX_ELAPSED_SECONDS = 300  # give up after 5 minutes total
_TRANSIENT_HTTP_STATUS_CODES = {408, 429, 500, 502, 503, 504}


def _get_with_timeout_retry(
    url,
    headers=None,
    timeout=_HTTP_TIMEOUT_SECONDS,
    initial_retry_delay=_HTTP_INITIAL_RETRY_DELAY_SECONDS,
    max_retry_delay=_HTTP_MAX_RETRY_DELAY_SECONDS,
    max_elapsed_seconds=_HTTP_MAX_ELAPSED_SECONDS,
):
    """
    Run an HTTP GET with exponential backoff + jitter on transient failures.

    Retries on timeouts, connection errors, and 408/429/5xx responses.
    Fails fast on non-transient HTTP errors (e.g. 400, 404).

    The delay sequence starts at `initial_retry_delay`, doubles each attempt,
    caps at `max_retry_delay`, and adds ±20 % jitter to spread concurrent
    callers.  Gives up entirely once `max_elapsed_seconds` have passed since
    the first attempt.
    """
    import random

    start_time = time.monotonic()
    delay = initial_retry_delay
    last_exc = None

    while True:
        elapsed = time.monotonic() - start_time
        if last_exc is not None and elapsed >= max_elapsed_seconds:
            logging.error(
                f"Giving up on '{url}' after {elapsed:.0f}s ({max_elapsed_seconds}s limit). "
                f"Last error: {last_exc}"
            )
            raise last_exc

        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            if status_code is None or status_code in _TRANSIENT_HTTP_STATUS_CODES:
                last_exc = e
            else:
                raise
        except (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as e:
            last_exc = e

        # Jitter: ±20 % of current delay
        jitter = delay * 0.2 * (2 * random.random() - 1)
        sleep_time = min(delay + jitter, max_retry_delay)

        # Don't sleep past the overall deadline
        remaining = max_elapsed_seconds - (time.monotonic() - start_time)
        sleep_time = min(sleep_time, remaining)
        if sleep_time <= 0:
            logging.error(
                f"Giving up on '{url}' after {time.monotonic() - start_time:.0f}s "
                f"({max_elapsed_seconds}s limit). Last error: {last_exc}"
            )
            raise last_exc

        logging.warning(
            f"Transient error for '{url}'. "
            f"Retrying in {sleep_time:.1f}s (elapsed {time.monotonic() - start_time:.0f}s / "
            f"{max_elapsed_seconds}s). Last error: {last_exc}"
        )
        time.sleep(sleep_time)
        delay = min(delay * 2, max_retry_delay)


def _fmt_timestamp(ts, time_system, timezone):
    """
    Parse a timestamp string (ISO 8601 or RFC 2822) and return a
    formatted string in the user's preferred time format and timezone.
    Returns the raw string unchanged if all parsing attempts fail.
    """
    if not ts:
        return ""
    # ISO 8601 variants (CAP standard)
    for fmt_str in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(ts, fmt_str)
            if dt.tzinfo:
                dt = dt.astimezone(timezone)
            out_fmt = (
                "%Y-%m-%d %I:%M %p %Z" if time_system.upper() == "12HR" else "%Y-%m-%d %H:%M %Z"
            )
            return dt.strftime(out_fmt)
        except ValueError:
            pass
    # RFC 2822 (standard RSS pubDate)
    try:
        dt = parsedate_to_datetime(ts).astimezone(timezone)
        out_fmt = (
            "%Y-%m-%d %I:%M %p %Z" if time_system.upper() == "12HR" else "%Y-%m-%d %H:%M %Z"
        )
        return dt.strftime(out_fmt)
    except Exception:
        pass
    return ts


def _strip_html(text):
    """Remove HTML tags and collapse whitespace for plain-text email output."""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _fetch_alerts_us(latitude, longitude, time_system, timezone, version):
    """
    Fetch active weather alerts from the NWS API for a US location.
    Returns a formatted string, or "" if no alerts or on error.
    Endpoint: https://api.weather.gov/alerts/active?point={lat},{lon}
    """
    url = f"https://api.weather.gov/alerts/active?point={latitude},{longitude}"
    headers = {
        "User-Agent": f"dailySummaryEmail/{version}",
        "Accept": "application/geo+json",
    }
    try:
        resp = _get_with_timeout_retry(url, headers=headers)
        data = resp.json()
    except requests.RequestException as e:
        logging.warning(f"Failed to fetch NWS alerts: {e}")
        return ""
    except Exception as e:
        logging.warning(f"Unexpected error fetching NWS alerts: {e}")
        return ""

    features = data.get("features", [])
    if not features:
        logging.debug("NWS: no active alerts for this location.")
        return ""

    blocks = []
    for feature in features:
        props = feature.get("properties", {})
        event = props.get("event") or "Unknown Event"
        severity = props.get("severity") or ""
        headline = props.get("headline") or ""
        description = props.get("description") or ""
        onset = _fmt_timestamp(props.get("onset") or "", time_system, timezone)
        expires = _fmt_timestamp(props.get("expires") or "", time_system, timezone)

        header = f"**{event}**"
        if severity and severity.lower() not in ("unknown", ""):
            header += f" [{severity}]"

        parts = [header]
        if headline:
            parts.append(headline)
        if onset:
            parts.append(f"Onset:   {onset}")
        if expires:
            parts.append(f"Expires: {expires}")
        if description:
            # NWS descriptions use \n\n for paragraph breaks — show first paragraph only
            first_para = description.split("\n\n")[0].replace("\n", " ").strip()
            if first_para:
                parts.append(first_para)

        blocks.append("\n\n".join(parts))

    logging.info(f"NWS: found {len(blocks)} active alert(s).")
    return "\n\n".join(blocks)


def _fetch_alerts_meteoalarm(country_code, city_state_str, time_system, timezone, version):
    """
    Fetch active weather alerts from MeteoAlarm RSS feeds for European countries.
    Filters items whose title contains any word from city_state_str so only
    locally-relevant alerts are shown. Falls back to all alerts if city_state_str
    is empty or no items match.
    Returns a formatted string, or "" if no alerts or on error.
    Feed index: https://feeds.meteoalarm.org/
    """
    slug = _METEOALARM_SLUGS.get(country_code.lower())
    if not slug:
        logging.debug(f"MeteoAlarm: no feed available for country '{country_code}'.")
        return ""

    url = f"https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-rss-{slug}"
    headers = {"User-Agent": f"dailySummaryEmail/{version}"}
    try:
        resp = _get_with_timeout_retry(url, headers=headers)
        root = ET.fromstring(resp.content)
    except requests.RequestException as e:
        logging.warning(f"Failed to fetch MeteoAlarm feed for '{slug}': {e}")
        return ""
    except ET.ParseError as e:
        logging.warning(f"Failed to parse MeteoAlarm feed XML for '{slug}': {e}")
        return ""
    except Exception as e:
        logging.warning(f"Unexpected error fetching MeteoAlarm feed for '{slug}': {e}")
        return ""

    items = root.findall(".//item")
    if not items:
        logging.debug(f"MeteoAlarm: no items in feed for '{slug}'.")
        return ""

    # Build a set of lowercase tokens from city_state_str for region matching
    location_tokens = (
        {w.lower() for w in re.split(r"[\s,]+", city_state_str) if len(w) > 2}
        if city_state_str
        else set()
    )

    def _item_matches_location(item):
        if not location_tokens:
            return True
        title = (item.findtext("title") or "").lower()
        return any(token in title for token in location_tokens)

    matched = [i for i in items if _item_matches_location(i)]
    # Fall back to all items if nothing matched (avoids silently dropping everything)
    display_items = matched if matched else items

    cap_ns = {"cap": "urn:oasis:names:tc:emergency:cap:1.2"}
    blocks = []
    for item in display_items:
        title = _strip_html(item.findtext("title") or "")
        description = _strip_html(item.findtext("description") or "")
        pub_date_raw = (item.findtext("pubDate") or "").strip()

        onset = _fmt_timestamp(
            (item.findtext("cap:onset", namespaces=cap_ns) or "").strip(),
            time_system, timezone,
        )
        expires = _fmt_timestamp(
            (item.findtext("cap:expires", namespaces=cap_ns) or "").strip(),
            time_system, timezone,
        )
        severity = (item.findtext("cap:severity", namespaces=cap_ns) or "").strip()
        pub_date_str = _fmt_timestamp(pub_date_raw, time_system, timezone)

        header = f"**{title}**" if title else "**Weather Alert**"
        if severity and severity.lower() not in ("unknown", ""):
            header += f" [{severity}]"

        parts = [header]
        if onset:
            parts.append(f"Onset:   {onset}")
        if expires:
            parts.append(f"Expires: {expires}")
        elif pub_date_str:
            parts.append(f"Issued:  {pub_date_str}")
        if description and description.lower() != title.lower():
            parts.append(description)

        blocks.append("\n\n".join(parts))

    if blocks:
        logging.info(f"MeteoAlarm: found {len(blocks)} alert(s) for '{slug}'.")
    else:
        logging.debug(f"MeteoAlarm: no matching alerts for '{slug}'.")
    return "\n\n".join(blocks)


def get_forecast(
    latitude, longitude, country_code, city_state_str, unit_system, time_system, timezone, version="unknown"
):
    """
    Fetch weather forecast and AQI data for the given coordinates and return
    a formatted string summary. country_code and city_state_str are provided
    by the caller (resolved once at startup via get_coordinates).

    Alerts are sourced from:
      - US:     NWS API  (https://api.weather.gov/alerts/active?point=lat,lon)
      - Europe: MeteoAlarm RSS feeds (https://feeds.meteoalarm.org/)
      - Other:  No alerts (graceful no-op)
    All sources are free and require no API key.
    """
    if not latitude or not longitude:
        logging.error("get_forecast called without valid latitude/longitude.")
        return ""

    # country_code is passed in — no Nominatim call needed here
    country_code = (country_code or "us").lower()
    aqi_param = "us_aqi" if country_code == "us" else "european_aqi"

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------
    if unit_system.upper() == "IMPERIAL":
        temperature_unit = "fahrenheit"
        windspeed_unit = "mph"
        precipitation_unit = "inch"
        temp_unit = "°F"
        precip_unit = "in"
        wind_unit = "mph"
        hot_thresh, warm_thresh, chilly_thresh, cold_thresh, very_cold_thresh = 86, 68, 50, 32, 10
        windy_thresh = 20
    else:
        temperature_unit = "celsius"
        windspeed_unit = "kmh"
        precipitation_unit = "mm"
        temp_unit = "°C"
        precip_unit = "mm"
        wind_unit = "km/h"
        hot_thresh, warm_thresh, chilly_thresh, cold_thresh, very_cold_thresh = 30, 20, 10, 0, -12
        windy_thresh = 32

    # ------------------------------------------------------------------
    # Fetch weather forecast
    # ------------------------------------------------------------------
    daily_parameters = [
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "precipitation_sum",
        "windspeed_10m_max",
        "uv_index_max",
        "sunrise",
        "sunset",
        "weathercode",
    ]
    hourly_parameters = ["relativehumidity_2m"]

    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&daily={','.join(daily_parameters)}"
        f"&hourly={','.join(hourly_parameters)}"
        f"&temperature_unit={temperature_unit}"
        f"&windspeed_unit={windspeed_unit}"
        f"&precipitation_unit={precipitation_unit}"
        f"&timezone={timezone}"
    )

    try:
        response = _get_with_timeout_retry(weather_url)
        forecast_data = response.json()
    except requests.RequestException as e:
        logging.error(f"Failed to retrieve forecast data: {e}")
        return f"Failed to retrieve forecast data: {e}"

    # ------------------------------------------------------------------
    # Fetch AQI data
    # ------------------------------------------------------------------
    aqi_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={latitude}&longitude={longitude}"
        f"&hourly={aqi_param},{aqi_param}_pm2_5,{aqi_param}_pm10,"
        f"{aqi_param}_nitrogen_dioxide,{aqi_param}_ozone,"
        f"{aqi_param}_sulphur_dioxide"
        f"&timezone=auto"
    )

    aqi_data = {}
    try:
        aqi_response = _get_with_timeout_retry(aqi_url)
        aqi_data = aqi_response.json()
    except requests.RequestException as e:
        logging.warning(f"Failed to retrieve AQI data: {e}")

    # ------------------------------------------------------------------
    # Parse daily weather for today
    # ------------------------------------------------------------------
    daily_data = forecast_data.get("daily", {})
    dates = daily_data.get("time", [])
    today = datetime.now(timezone).date().isoformat()

    try:
        index = dates.index(today)
    except ValueError:
        logging.error(f"Today's date {today} not found in forecast data.")
        return f"Today's date {today} not found in forecast data."

    min_temp = daily_data["temperature_2m_min"][index]
    max_temp = daily_data["temperature_2m_max"][index]
    wind_speed = daily_data["windspeed_10m_max"][index]
    precipitation = daily_data["precipitation_sum"][index]
    uv_index = daily_data["uv_index_max"][index]
    sunrise = daily_data["sunrise"][index]
    sunset = daily_data["sunset"][index]
    weathercode = daily_data["weathercode"][index]
    feels_like_min = daily_data["apparent_temperature_min"][index]
    feels_like_max = daily_data["apparent_temperature_max"][index]

    weathercode_descriptions = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Fog", "🌫️"),
        48: ("Depositing rime fog", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Moderate drizzle", "🌧️"),
        55: ("Dense drizzle", "🌧️"),
        56: ("Light freezing drizzle", "🌧️"),
        57: ("Dense freezing drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        66: ("Light freezing rain", "🌧️"),
        67: ("Heavy freezing rain", "🌧️"),
        71: ("Slight snow fall", "❄️"),
        73: ("Moderate snow fall", "❄️"),
        75: ("Heavy snow fall", "❄️"),
        77: ("Snow grains", "❄️"),
        80: ("Slight rain showers", "🌦️"),
        81: ("Moderate rain showers", "🌧️"),
        82: ("Violent rain showers", "🌧️"),
        85: ("Slight snow showers", "❄️"),
        86: ("Heavy snow showers", "❄️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm with slight hail", "⛈️"),
        99: ("Thunderstorm with heavy hail", "⛈️"),
    }
    condition, emoji = weathercode_descriptions.get(weathercode, ("Unknown", "❓"))

    sunrise_time = datetime.fromisoformat(sunrise)
    sunset_time = datetime.fromisoformat(sunset)
    fmt = "%-I:%M %p" if time_system.upper() == "12HR" else "%H:%M"
    sunrise_str = sunrise_time.strftime(fmt)
    sunset_str = sunset_time.strftime(fmt)

    # Average humidity for today
    hourly_data = forecast_data.get("hourly", {})
    hourly_times = hourly_data.get("time", [])
    humidity_values = hourly_data.get("relativehumidity_2m", [])
    today_humidity = [h for t, h in zip(hourly_times, humidity_values) if t.startswith(today)]
    avg_humidity = round(sum(today_humidity) / len(today_humidity), 1) if today_humidity else "N/A"

    # ------------------------------------------------------------------
    # AQI summary
    # ------------------------------------------------------------------
    avg_aqi = "N/A"
    aqi_suggestion = ""
    try:
        if aqi_data and "hourly" in aqi_data:
            aqi_times = aqi_data["hourly"]["time"]
            today_aqi_values = [
                val for t, val in zip(aqi_times, aqi_data["hourly"][aqi_param])
                if t.startswith(today)
            ]
            if today_aqi_values:
                avg_aqi = round(sum(today_aqi_values) / len(today_aqi_values), 1)

                if country_code == "us":
                    if avg_aqi > 300:
                        aqi_suggestion = "Air quality is hazardous. Stay indoors and use air purifiers."
                    elif avg_aqi > 200:
                        aqi_suggestion = "Air quality is very unhealthy. Avoid outdoor activities."
                    elif avg_aqi > 150:
                        aqi_suggestion = "Air quality is unhealthy. Sensitive groups should stay indoors."
                    elif avg_aqi > 100:
                        aqi_suggestion = "Air quality is unhealthy for sensitive groups. Limit outdoor exposure."
                else:
                    if avg_aqi > 100:
                        aqi_suggestion = "Air quality is extremely poor. Stay indoors and avoid physical activities."
                    elif avg_aqi > 80:
                        aqi_suggestion = "Air quality is very poor. Minimize outdoor activities."
                    elif avg_aqi > 60:
                        aqi_suggestion = "Air quality is poor. Consider staying indoors."
                    elif avg_aqi > 40:
                        aqi_suggestion = "Air quality is moderate. Sensitive individuals take caution."
                    elif avg_aqi > 20:
                        aqi_suggestion = "Air quality is fair. Some pollutants may affect sensitive individuals."

            pollutants = {
                f"{aqi_param}_pm2_5": "PM2.5",
                f"{aqi_param}_pm10": "PM10",
                f"{aqi_param}_nitrogen_dioxide": "Nitrogen Dioxide",
                f"{aqi_param}_ozone": "Ozone",
                f"{aqi_param}_sulphur_dioxide": "Sulphur Dioxide",
            }
            pollutant_warnings = []
            for param, name in pollutants.items():
                if param in aqi_data["hourly"]:
                    values = [
                        v for t, v in zip(aqi_times, aqi_data["hourly"][param])
                        if t.startswith(today)
                    ]
                    if values:
                        avg_val = round(sum(values) / len(values), 1)
                        if avg_val > 50:
                            pollutant_warnings.append(f"- {name}: AQI {avg_val}. Consider reducing exposure.")
            if pollutant_warnings:
                aqi_suggestion += "\nPollutant-specific warnings:\n" + "\n".join(pollutant_warnings)
    except Exception as e:
        logging.warning(f"Error calculating AQI: {e}")

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------
    if country_code == "us":
        alerts_info = _fetch_alerts_us(latitude, longitude, time_system, timezone, version)
    elif country_code in _METEOALARM_SLUGS:
        alerts_info = _fetch_alerts_meteoalarm(country_code, city_state_str, time_system, timezone, version)
    else:
        alerts_info = ""
        logging.debug(f"No alerts source available for country '{country_code}'.")

    # ------------------------------------------------------------------
    # Outfit suggestions
    # ------------------------------------------------------------------
    outfit_suggestions = ""
    # Primary suggestion based on daytime high
    if max_temp > hot_thresh:
        outfit_suggestions += "It's hot outside! Wear light, breathable clothing and stay hydrated. "
    elif max_temp > warm_thresh:
        outfit_suggestions += "The weather is warm. A t-shirt and shorts should be comfortable. "
    elif max_temp > chilly_thresh:
        outfit_suggestions += "It's a bit chilly. Consider wearing a light jacket. "
    elif max_temp > cold_thresh:
        outfit_suggestions += "It's cold outside! Wear warm clothing such as a coat and scarf. "
    elif max_temp > very_cold_thresh:
        outfit_suggestions += "It's quite cold outside! Layer up with thermals, a heavy coat, scarf, and gloves. "
    else:
        outfit_suggestions += "It's dangerously cold outside! Wear multiple thermal layers, a heavy insulated coat, face protection, and warm gloves and boots. "

    # If the daily low is noticeably colder than the high, flag it
    if max_temp > chilly_thresh and min_temp <= chilly_thresh:
        outfit_suggestions += f"Temperatures drop to {min_temp}{temp_unit}, bring a layer for morning and evening. "

    # Wind suggestion scaled to temperature context
    if wind_speed > windy_thresh:
        if max_temp > warm_thresh:
            outfit_suggestions += "It's windy. A light, breathable layer will help cut the wind. "
        elif max_temp > cold_thresh:
            outfit_suggestions += "It's quite windy. A windbreaker would be a good idea. "
        else:
            outfit_suggestions += "It's windy and cold — a windproof, insulated outer layer is essential. "

    rain_codes = {51, 53, 55, 56, 57, 61, 63, 65, 80, 81, 82, 95, 96, 99}
    snow_codes = {66, 67, 71, 73, 75, 77, 85, 86}
    if weathercode in rain_codes:
        outfit_suggestions += "Rain is expected. Carry an umbrella or wear waterproof clothing. "
    elif weathercode in snow_codes:
        outfit_suggestions += "Snow is expected. Dress warmly in layers and consider waterproof boots and a winter coat. "

    # ------------------------------------------------------------------
    # Assemble output
    # ------------------------------------------------------------------
    location_label = city_state_str if city_state_str else f"{latitude}, {longitude}"
    weather_string = (
        f"\n\n# Weather\n"
        f"\nToday's Weather Forecast For {location_label}:\n"
        f"\nCondition: {condition} {emoji}\n"
        f"\nTemperature: {min_temp}{temp_unit} to {max_temp}{temp_unit}\n"
        f"\nFeels Like Temperature: {feels_like_min}{temp_unit} to {feels_like_max}{temp_unit}\n"
        f"\nHumidity: {avg_humidity}%\n"
        f"\nPrecipitation: {precipitation} {precip_unit}\n"
        f"\nWind Speed: {wind_speed} {wind_unit}\n"
        f"\nUV Index: {uv_index}\n"
        f"\nAir Quality: {avg_aqi}\n"
        f"\nSunrise: {sunrise_str}\n"
        f"\nSunset: {sunset_str}\n"
    )
    if aqi_suggestion:
        weather_string += f"\n{aqi_suggestion}"
    weather_string += f"\n{outfit_suggestions}"
    if alerts_info:
        weather_string += f"\n\n## Severe Weather Alerts:\n{alerts_info}"

    return weather_string
