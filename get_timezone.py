import logging

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder


def get_timezone(lat, lon):
    try:
        # Initialize geolocator and timezone finder
        geolocator = Nominatim(user_agent="timezone_locator")
        tf = TimezoneFinder()

        # Get the location information
        location = geolocator.reverse((lat, lon), exactly_one=True)

        # Get the timezone name
        timezone_str = tf.timezone_at(lng=lon, lat=lat)

        if timezone_str:
            return timezone_str
        else:
            return "Timezone not found"
    except Exception as e:
        logging.critical(f"An error occurred: {e}")
        return None
