import logging
import requests

def get_forecast(weather_api_key, latitude, longitude):
    # Find WFO and NWS gridpoint
    gridpoint_url = f"https://api.weather.gov/points/{latitude},{longitude}"
    response = requests.get(gridpoint_url)
    if response.status_code == 200:
        gridpoint_data = response.json()
    else:
        logging.error(f"Failed to retrieve gridpoint data: {response.status_code}")
        return f"Failed to retrieve gridpoint data: {response.status_code}"
    # Get city
    city = gridpoint_data['properties']['relativeLocation']['properties']['city']

    # Get state
    state = gridpoint_data['properties']['relativeLocation']['properties']['state']

    # Construct the NWS API endpoint URL using the latitude and longitude
    forecast_url = gridpoint_data['properties']['forecast']

    # Add the Authorization header with the API key
    headers = {"User-Agent": weather_api_key}  # NWS requires a contact email

    response = requests.get(forecast_url, headers=headers)
    if response.status_code == 200:
        forecast_data = response.json()
    else:
        logging.error(f"Failed to retrieve forecast data: {response.status_code}")

    data = {
        "city": city,
        "state": state,
        "forecast": forecast_data
    }
    weather_string = f"""\
# Weather
{data['forecast']['properties']['periods'][0]['name']}'s Weather Forecast for {data['city']}, {data['state']}: \
{data['forecast']['properties']['periods'][0]['detailedForecast']}"""

    return weather_string
