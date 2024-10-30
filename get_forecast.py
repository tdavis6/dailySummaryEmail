import logging
import requests
from datetime import datetime


def get_forecast(weather_api_key, latitude, longitude, unit_system, time_system):
    weather_string = ""
    forecast_data = {}

    if weather_api_key and latitude and longitude:
        # Construct the WeatherAPI endpoint URL using the latitude and longitude
        weather_url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_api_key}&q={latitude},{longitude}&days=1"

        response = requests.get(weather_url)
        if response.status_code == 200:
            forecast_data = response.json()
        else:
            logging.error(f"Failed to retrieve forecast data: {response.status_code}")
            return f"Failed to retrieve forecast data: {response.status_code}"

        # Extract necessary information from the API response
        city = forecast_data["location"]["name"]
        state = forecast_data["location"]["region"]

        forecast = forecast_data["forecast"]["forecastday"][0]["day"]
        astro = forecast_data["forecast"]["forecastday"][0]["astro"]

        # Choose measurement units based on temperature_units parameter
        if unit_system.upper() == "IMPERIAL":
            min_temp = forecast["mintemp_f"]
            max_temp = forecast["maxtemp_f"]
            wind_speed = forecast["maxwind_mph"]
            precipitation = forecast["totalprecip_in"]
            temp_unit = "°F"
            precip_unit = "in"
            wind_unit = "mph"
        else:
            min_temp = forecast["mintemp_c"]
            max_temp = forecast["maxtemp_c"]
            wind_speed = forecast["maxwind_kph"]
            precipitation = forecast["totalprecip_mm"]
            temp_unit = "°C"
            precip_unit = "mm"
            wind_unit = "kph"

        # Get the UV index
        uv_index = forecast["uv"]

        # Convert times based on time_system
        sunrise = datetime.strptime(astro["sunrise"], "%I:%M %p")
        sunset = datetime.strptime(astro["sunset"], "%I:%M %p")

        if time_system.upper() == "12HR":
            sunrise_str = sunrise.strftime("%I:%M %p")
            sunset_str = sunset.strftime("%I:%M %p")
        else:
            sunrise_str = sunrise.strftime("%H:%M")
            sunset_str = sunset.strftime("%H:%M")

        # Format the weather string with additional data
        logging.debug(forecast_data)
        weather_string = f"""\n\n# Weather\n
Today's Weather Forecast for {city}, {state}:\n
Condition: {forecast['condition']['text']}\n
Temperature: {min_temp}{temp_unit} to {max_temp}{temp_unit}\n
Humidity: {forecast['avghumidity']}%\n
Precipitation: {precipitation} {precip_unit}\n
Wind Speed: {wind_speed} {wind_unit}\n
UV Index: {uv_index}\n
Sunrise: {sunrise_str}\n
Sunset: {sunset_str}\n"""

    return weather_string