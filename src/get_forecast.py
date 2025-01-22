import logging
from datetime import datetime, date
import requests

def get_forecast(
        latitude, longitude, city_state_str, unit_system, time_system, timezone
):
    weather_string = ""
    forecast_data = {}

    if latitude and longitude:
        # --------------------------------------------------
        # 1) Determine which AQI scale to use via geocoding
        # --------------------------------------------------
        country_code = "us"  # Default fallback
        try:
            # Use Nominatim for reverse geocoding
            geocode_url = (
                f"https://nominatim.openstreetmap.org/reverse?"
                f"lat={latitude}&lon={longitude}&format=json"
            )
            headers = {"User-Agent": "MyWeatherApp/1.0"}
            geocode_resp = requests.get(geocode_url, headers=headers)
            if geocode_resp.status_code == 200:
                geocode_data = geocode_resp.json()
                address_info = geocode_data.get("address", {})
                country_code = address_info.get("country_code", "us").lower()
            else:
                logging.warning(
                    f"Reverse geocoding failed with status {geocode_resp.status_code}"
                )
        except Exception as e:
            logging.warning(f"Error while reverse geocoding: {e}")

        # Decide on AQI parameter
        if country_code == "us":
            aqi_param = "us_aqi"
        else:
            aqi_param = "european_aqi"

        # -----------------------------------
        # 2) Fetch Weather Data
        # -----------------------------------
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

        if unit_system.upper() == "IMPERIAL":
            temperature_unit = "fahrenheit"
            windspeed_unit = "mph"
            precipitation_unit = "inch"
            temp_unit = "°F"
            precip_unit = "in"
            wind_unit = "mph"
        else:
            temperature_unit = "celsius"
            windspeed_unit = "kmh"
            precipitation_unit = "mm"
            temp_unit = "°C"
            precip_unit = "mm"
            wind_unit = "km/h"

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

        response = requests.get(weather_url)
        if response.status_code == 200:
            forecast_data = response.json()
        else:
            logging.error(f"Failed to retrieve forecast data: {response.status_code}")
            return f"Failed to retrieve forecast data: {response.status_code}"

        # -----------------------------------
        # 3) Fetch AQI Data
        # -----------------------------------
        aqi_data = {}
        aqi_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={latitude}&longitude={longitude}"
            f"&hourly={aqi_param},{aqi_param}_pm2_5,{aqi_param}_pm10,"
            f"{aqi_param}_nitrogen_dioxide,{aqi_param}_ozone,"
            f"{aqi_param}_sulphur_dioxide"
            f"&timezone=auto"
        )

        aqi_response = requests.get(aqi_url)
        if aqi_response.status_code == 200:
            aqi_data = aqi_response.json()
        else:
            logging.warning(f"Failed to retrieve AQI data: {aqi_response.status_code}")

        # -----------------------------------
        # Parse Daily Weather Data
        # -----------------------------------
        daily_data = forecast_data["daily"]
        dates = daily_data["time"]
        today = date.today().isoformat()

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
        if time_system.upper() == "12HR":
            sunrise_str = sunrise_time.strftime("%I:%M %p")
            sunset_str = sunset_time.strftime("%I:%M %p")
        else:
            sunrise_str = sunrise_time.strftime("%H:%M")
            sunset_str = sunset_time.strftime("%H:%M")

        # Calculate average humidity
        hourly_data = forecast_data["hourly"]
        hourly_times = hourly_data["time"]
        humidity_values = hourly_data["relativehumidity_2m"]
        today_humidity_values = [
            h for t, h in zip(hourly_times, humidity_values) if t.startswith(today)
        ]
        if today_humidity_values:
            avg_humidity = sum(today_humidity_values) / len(today_humidity_values)
            avg_humidity = round(avg_humidity, 1)
        else:
            avg_humidity = "N/A"

        # -------------------------------------------
        # Calculate average AQI for today's date
        # -------------------------------------------
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
                    avg_aqi_val = sum(today_aqi_values) / len(today_aqi_values)
                    avg_aqi = round(avg_aqi_val, 1)

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
                pollutant_suggestions = ""
                for pollutant_param, name in pollutants.items():
                    if pollutant_param in aqi_data["hourly"]:
                        pollutant_values = [
                            val for t, val in zip(aqi_times, aqi_data["hourly"][pollutant_param])
                            if t.startswith(today)
                        ]
                        if pollutant_values:
                            avg_pollutant_aqi = round(sum(pollutant_values) / len(pollutant_values), 1)
                            if avg_pollutant_aqi > 50:
                                pollutant_suggestions += f"- {name}: AQI {avg_pollutant_aqi}. Consider reducing exposure.\n"
                if pollutant_suggestions:
                    aqi_suggestion += f"\nPollutant-specific warnings:\n{pollutant_suggestions}"
        except Exception as e:
            logging.warning(f"Error calculating AQI: {e}")

        # -------------------------------------------
        # Check for alerts in forecast_data AND aqi_data
        # -------------------------------------------
        alerts_info = ""

        # 1) Weather alerts from forecast_data
        if "alerts" in forecast_data and forecast_data["alerts"]:
            alerts = forecast_data["alerts"].get("alert", [])
            for alert in alerts:
                alert_event = alert.get("event", "Unknown Event")
                alert_start = alert.get("start")
                alert_end = alert.get("end")
                alert_description = alert.get("description", "")

                if alert_start:
                    alert_start_time = datetime.strptime(
                        alert_start, "%Y-%m-%dT%H:%M:%S%z"
                    )
                    alert_start_time = alert_start_time.astimezone(timezone)
                    if time_system.upper() == "12HR":
                        alert_start_str = alert_start_time.strftime(
                            "%Y-%m-%d %I:%M %p %Z"
                        )
                    else:
                        alert_start_str = alert_start_time.strftime("%Y-%m-%d %H:%M %Z")
                else:
                    alert_start_str = "N/A"

                if alert_end:
                    alert_end_time = datetime.strptime(
                        alert_end, "%Y-%m-%dT%H:%M:%S%z"
                    )
                    alert_end_time = alert_end_time.astimezone(timezone)
                    if time_system.upper() == "12HR":
                        alert_end_str = alert_end_time.strftime(
                            "%Y-%m-%d %I:%M %p %Z"
                        )
                    else:
                        alert_end_str = alert_end_time.strftime("%Y-%m-%d %H:%M %Z")
                else:
                    alert_end_str = "N/A"

                alerts_info += (
                    f"\n**{alert_event}**\n"
                    f"Start: {alert_start_str}\n"
                    f"End: {alert_end_str}\n"
                    f"{alert_description}\n"
                )

        # 2) AQI alerts from aqi_data (if present)
        #    Some data sources might not provide alerts, but we include this in case they do.
        if "alerts" in aqi_data and aqi_data["alerts"]:
            aqi_alerts = aqi_data["alerts"].get("alert", [])
            for alert in aqi_alerts:
                alert_event = alert.get("event", "Unknown AQI Event")
                alert_start = alert.get("start")
                alert_end = alert.get("end")
                alert_description = alert.get("description", "")

                if alert_start:
                    alert_start_time = datetime.strptime(
                        alert_start, "%Y-%m-%dT%H:%M:%S%z"
                    )
                    alert_start_time = alert_start_time.astimezone(timezone)
                    if time_system.upper() == "12HR":
                        alert_start_str = alert_start_time.strftime(
                            "%Y-%m-%d %I:%M %p %Z"
                        )
                    else:
                        alert_start_str = alert_start_time.strftime("%Y-%m-%d %H:%M %Z")
                else:
                    alert_start_str = "N/A"

                if alert_end:
                    alert_end_time = datetime.strptime(
                        alert_end, "%Y-%m-%dT%H:%M:%S%z"
                    )
                    alert_end_time = alert_end_time.astimezone(timezone)
                    if time_system.upper() == "12HR":
                        alert_end_str = alert_end_time.strftime(
                            "%Y-%m-%d %I:%M %p %Z"
                        )
                    else:
                        alert_end_str = alert_end_time.strftime("%Y-%m-%d %H:%M %Z")
                else:
                    alert_end_str = "N/A"

                alerts_info += (
                    f"\n**{alert_event}** (AQI)\n"
                    f"Start: {alert_start_str}\n"
                    f"End: {alert_end_str}\n"
                    f"{alert_description}\n"
                )

        # Outfit suggestions (existing logic)
        outfit_suggestions = ""
        if unit_system.upper() == "IMPERIAL":
            if max_temp > 86:
                outfit_suggestions += (
                    "It's hot outside! Wear light clothing and stay hydrated. "
                )
            elif max_temp > 68:
                outfit_suggestions += (
                    "The weather is warm. A t-shirt and shorts should be comfortable. "
                )
            elif max_temp > 50:
                outfit_suggestions += (
                    "It's a bit chilly. Consider wearing a light jacket. "
                )
            elif max_temp > 32:
                outfit_suggestions += (
                    "It's cold outside! Wear warm clothing such as a coat and scarf. "
                )
            elif max_temp > 10:
                outfit_suggestions += (
                    "It's quite cold outside! Wear warm clothing such as a coat and scarf. Layer if necessary."
                )
            else:
                outfit_suggestions += (
                    "It's very cold outside! Wear warm clothing such as a coat and scarf. Make sure to layer. "
                )
            if wind_speed > 20:
                outfit_suggestions += (
                    "It's quite windy. Wearing a windbreaker might be a good idea. "
                )
        else:
            if max_temp > 30:
                outfit_suggestions += (
                    "It's hot outside! Wear light clothing and stay hydrated. "
                )
            elif max_temp > 20:
                outfit_suggestions += (
                    "The weather is warm. A t-shirt and shorts should be comfortable. "
                )
            elif max_temp > 10:
                outfit_suggestions += (
                    "It's a bit chilly. Consider wearing a light jacket. "
                )
            elif max_temp > 0:
                outfit_suggestions += (
                    "It's cold outside! Wear warm clothing such as a coat and scarf. "
                )
            elif max_temp > -12:
                outfit_suggestions += (
                    "It's quite cold outside! Wear warm clothing such as a coat and scarf. Layer if necessary."
                )
            else:
                outfit_suggestions += (
                    "It's very cold outside! Wear warm clothing such as a coat and scarf. Make sure to layer. "
                )
            if wind_speed > 32:
                outfit_suggestions += (
                    "It's quite windy. Wearing a windbreaker might be a good idea. "
                )

        # Precipitation suggestions
        rain_codes = [51, 53, 55, 56, 57, 61, 63, 65, 80, 81, 82, 95, 96, 99]
        snow_codes = [66, 67, 71, 73, 75, 77, 85, 86]

        if weathercode in rain_codes:
            outfit_suggestions += (
                "Rain is expected. Carry an umbrella or wear waterproof clothing. "
            )
        elif weathercode in snow_codes:
            outfit_suggestions += (
                "Snow is expected. Dress warmly in layers and consider waterproof boots and a winter coat. "
            )

        # Build final string
        weather_string = f"""\n\n# Weather\n
Today's Weather Forecast For {city_state_str if city_state_str else f"{latitude}, {longitude}"}:\n
Condition: {condition} {emoji}\n
Temperature: {min_temp}{temp_unit} to {max_temp}{temp_unit}\n
Feels Like Temperature: {feels_like_min}{temp_unit} to {feels_like_max}{temp_unit}\n
Humidity: {avg_humidity}%\n
Precipitation: {precipitation} {precip_unit}\n
Wind Speed: {wind_speed} {wind_unit}\n
UV Index: {uv_index}\n
Air Quality: {avg_aqi}\n
Sunrise: {sunrise_str}\n
Sunset: {sunset_str}\n
{aqi_suggestion if aqi_suggestion else ""}\n
{outfit_suggestions}\n
"""

        if alerts_info:
            weather_string += f"\n## Severe Weather Alerts:\n{alerts_info}"

    return weather_string
