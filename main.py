import os

from dotenv import load_dotenv

from get_forecast import get_forecast
from send_email import send_email

# Load the environment variables from the .env file
load_dotenv()

# Get the API key and coordinates from the environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")

if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY not found in environment variables")
if not LATITUDE:
    raise ValueError("LATITUDE not found in environment variables")
if not LONGITUDE:
    raise ValueError("LONGITUDE not found in environment variables")


if __name__ == "__main__":
    try:
        weather_data = get_forecast(WEATHER_API_KEY, LATITUDE, LONGITUDE)
        send_email(weather_data)
    except Exception as e:
        print(f"Error occurred: {e}")
