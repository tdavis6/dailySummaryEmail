import logging
from datetime import datetime

import requests


def get_forecast(
    latitude, longitude, country_code, city_state_str, unit_system, time_system, timezone
):
    """
    Fetch weather forecast and AQI data for the given coordinates and return
    a formatted string summary. country_code and city_state_str are provided
    by the caller (resolved once at startup via get_coordinates).
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
        f"&alerts=true"
    )

    try:
        response = requests.get(weather_url, timeout=10)
        response.raise_for_status()
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
        aqi_response = requests.get(aqi_url, timeout=10)
        aqi_response.raise_for_status()
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
    def _format_alert_time(ts, time_system, timezone):
        try:
            dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone)
            return dt.strftime("%Y-%m-%d %I:%M %p %Z" if time_system.upper() == "12HR" else "%Y-%m-%d %H:%M %Z")
        except Exception:
            return "N/A"

    alerts_info = ""
    for source, label_suffix in [(forecast_data, ""), (aqi_data, " (AQI)")]:
        if "alerts" in source and source["alerts"]:
            for alert in source["alerts"].get("alert", []):
                start_str = _format_alert_time(alert.get("start", ""), time_system, timezone) if alert.get("start") else "N/A"
                end_str = _format_alert_time(alert.get("end", ""), time_system, timezone) if alert.get("end") else "N/A"
                alerts_info += (
                    f"\n**{alert.get('event', 'Unknown Event')}{label_suffix}**\n"
                    f"Start: {start_str}\n"
                    f"End: {end_str}\n"
                    f"{alert.get('description', '')}\n"
                )

    # ------------------------------------------------------------------
    # Outfit suggestions
    # ------------------------------------------------------------------
    outfit_suggestions = ""
    if max_temp > hot_thresh:
        outfit_suggestions += "It's hot outside! Wear light clothing and stay hydrated. "
    elif max_temp > warm_thresh:
        outfit_suggestions += "The weather is warm. A t-shirt and shorts should be comfortable. "
    elif max_temp > chilly_thresh:
        outfit_suggestions += "It's a bit chilly. Consider wearing a light jacket. "
    elif max_temp > cold_thresh:
        outfit_suggestions += "It's cold outside! Wear warm clothing such as a coat and scarf. "
    elif max_temp > very_cold_thresh:
        outfit_suggestions += "It's quite cold outside! Wear warm clothing such as a coat and scarf. Layer if necessary. "
    else:
        outfit_suggestions += "It's very cold outside! Wear warm clothing such as a coat and scarf. Make sure to layer. "

    if wind_speed > windy_thresh:
        outfit_suggestions += "It's quite windy. Wearing a windbreaker might be a good idea. "

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