import logging
import requests
from datetime import datetime, date

def get_forecast(latitude, longitude, city_state_str, unit_system, time_system, timezone):
    weather_string = ""
    forecast_data = {}

    if latitude and longitude:
        # Construct the Open-Meteo API endpoint URL using the latitude and longitude
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
            "weathercode"
        ]

        hourly_parameters = ["relativehumidity_2m"]

        # Choose units based on unit_system parameter
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

        # Build the URL and include alerts
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={latitude}&longitude={longitude}"
            f"&daily={','.join(daily_parameters)}"
            f"&hourly={','.join(hourly_parameters)}"
            f"&temperature_unit={temperature_unit}"
            f"&windspeed_unit={windspeed_unit}"
            f"&precipitation_unit={precipitation_unit}"
            f"&timezone=auto"
            f"&alerts=true"
        )

        response = requests.get(weather_url)
        if response.status_code == 200:
            forecast_data = response.json()
        else:
            logging.error(f"Failed to retrieve forecast data: {response.status_code}")
            return f"Failed to retrieve forecast data: {response.status_code}"

        # Extract necessary information from the API response
        daily_data = forecast_data['daily']
        dates = daily_data['time']
        today = date.today().isoformat()

        try:
            index = dates.index(today)
        except ValueError:
            logging.error(f"Today's date {today} not found in forecast data.")
            return f"Today's date {today} not found in forecast data."

        min_temp = daily_data['temperature_2m_min'][index]
        max_temp = daily_data['temperature_2m_max'][index]
        wind_speed = daily_data['windspeed_10m_max'][index]
        precipitation = daily_data['precipitation_sum'][index]
        uv_index = daily_data['uv_index_max'][index]
        sunrise = daily_data['sunrise'][index]
        sunset = daily_data['sunset'][index]
        weathercode = daily_data['weathercode'][index]
        feels_like_min = daily_data['apparent_temperature_min'][index]
        feels_like_max = daily_data['apparent_temperature_max'][index]

        # Map weathercode to description and emoji
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
            99: ("Thunderstorm with heavy hail", "⛈️")
        }

        condition, emoji = weathercode_descriptions.get(weathercode, ("Unknown", "❓"))

        # Process sunrise and sunset times
        sunrise_time = datetime.fromisoformat(sunrise)
        sunset_time = datetime.fromisoformat(sunset)

        if time_system.upper() == "12HR":
            sunrise_str = sunrise_time.strftime("%I:%M %p")
            sunset_str = sunset_time.strftime("%I:%M %p")
        else:
            sunrise_str = sunrise_time.strftime("%H:%M")
            sunset_str = sunset_time.strftime("%H:%M")

        # Calculate average humidity for today
        hourly_data = forecast_data['hourly']
        hourly_times = hourly_data['time']
        humidity_values = hourly_data['relativehumidity_2m']

        today_humidity_values = [
            humidity for time_str, humidity in zip(hourly_times, humidity_values)
            if time_str.startswith(today)
        ]

        if today_humidity_values:
            avg_humidity = sum(today_humidity_values) / len(today_humidity_values)
            avg_humidity = round(avg_humidity, 1)
        else:
            avg_humidity = "N/A"

        # Check for severe weather alerts
        alerts_info = ""
        if 'alerts' in forecast_data and forecast_data['alerts']:
            alerts = forecast_data['alerts'].get('alert', [])
            for alert in alerts:
                alert_event = alert.get('event', 'Unknown Event')
                alert_start = alert.get('start')
                alert_end = alert.get('end')
                alert_description = alert.get('description', '')

                # Format alert times using the provided tzinfo object
                if alert_start:
                    alert_start_time = datetime.strptime(alert_start, "%Y-%m-%dT%H:%M:%S%z")
                    alert_start_time = alert_start_time.astimezone(timezone)
                    if time_system.upper() == "12HR":
                        alert_start_str = alert_start_time.strftime("%Y-%m-%d %I:%M %p %Z")
                    else:
                        alert_start_str = alert_start_time.strftime("%Y-%m-%d %H:%M %Z")
                else:
                    alert_start_str = "N/A"

                if alert_end:
                    alert_end_time = datetime.strptime(alert_end, "%Y-%m-%dT%H:%M:%S%z")
                    alert_end_time = alert_end_time.astimezone(timezone)
                    if time_system.upper() == "12HR":
                        alert_end_str = alert_end_time.strftime("%Y-%m-%d %I:%M %p %Z")
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

        outfit_suggestions = ""
        if unit_system.upper() == "IMPERIAL":
            if max_temp > 86:
                outfit_suggestions += "It's hot outside! Wear light clothing and stay hydrated. "
            elif max_temp > 68:
                outfit_suggestions += "The weather is warm. A t-shirt and shorts should be comfortable. "
            elif max_temp > 50:
                outfit_suggestions += "It's a bit chilly. Consider wearing a light jacket. "
            else:
                outfit_suggestions += "It's cold outside! Wear warm clothing such as a coat and scarf. "
            if wind_speed > 20:
                outfit_suggestions += "It's quite windy. Wearing a windbreaker might be a good idea. "
        else:
            if max_temp > 30:
                outfit_suggestions += "It's hot outside! Wear light clothing and stay hydrated. "
            elif max_temp > 20:
                outfit_suggestions += "The weather is warm. A t-shirt and shorts should be comfortable. "
            elif max_temp > 10:
                outfit_suggestions += "It's a bit chilly. Consider wearing a light jacket. "
            else:
                outfit_suggestions += "It's cold outside! Wear warm clothing such as a coat and scarf. "
            if wind_speed > 32:
                outfit_suggestions += "It's quite windy. Wearing a windbreaker might be a good idea. "
        # Define separate code lists for rain and snow
        rain_codes = [
            51, 53, 55, 56, 57,  # Drizzle variants
            61, 63, 65,          # Rain variants
            80, 81, 82,          # Rain showers
            95, 96, 99           # Thunderstorms (commonly associated with rain/hail)
        ]
        snow_codes = [
            66, 67,              # Freezing rain (treat as snow-like due to freezing conditions)
            71, 73, 75, 77,      # Snowfall variants
            85, 86               # Snow showers
        ]

        # Add precipitation-specific suggestions
        if weathercode in rain_codes:
            outfit_suggestions += (
                "Rain is expected. Carry an umbrella or wear waterproof clothing. "
            )
        elif weathercode in snow_codes:
            outfit_suggestions += (
                "Snow is expected. Dress warmly in layers and consider waterproof boots and a winter coat. "
            )

        weather_string = f"""\n\n# Weather\n
Today's Weather Forecast For {city_state_str if city_state_str else f"{latitude}, {longitude}"}:\n
Condition: {condition} {emoji}\n
Temperature: {min_temp}{temp_unit} to {max_temp}{temp_unit}\n
Feels Like Temperature: {feels_like_min}{temp_unit} to {feels_like_max}{temp_unit}\n
Humidity: {avg_humidity}%\n
Precipitation: {precipitation} {precip_unit}\n
Wind Speed: {wind_speed} {wind_unit}\n
UV Index: {uv_index}\n
Sunrise: {sunrise_str}\n
Sunset: {sunset_str}\n
{outfit_suggestions}\n
"""

        # Add alerts to the weather string if any
        if alerts_info:
            weather_string += f"\n## Severe Weather Alerts:\n{alerts_info}"

    return weather_string