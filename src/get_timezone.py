import logging
from functools import lru_cache

from timezonefinder import TimezoneFinder


@lru_cache(maxsize=1)
def _finder():
    # Building a TimezoneFinder loads its data files, so create it once.
    return TimezoneFinder()


def get_timezone(lat, lon):
    try:
        # Convert latitude and longitude to float
        lat = float(lat)
        lon = float(lon)

        # Get the timezone name
        timezone_str = _finder().timezone_at(lng=lon, lat=lat)

        if timezone_str:
            return timezone_str
        else:
            logging.warning(f"No timezone found for coordinates ({lat}, {lon}).")
            return None
    except Exception as e:
        logging.critical(f"An error occurred: {e}")
        return None
