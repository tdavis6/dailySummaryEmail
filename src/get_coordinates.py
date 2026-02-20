import logging
import time

from geopy.exc import GeocoderUnavailable, GeocoderTimedOut
from geopy.geocoders import Nominatim


def get_coordinates(address, version="unknown"):
    """
    Geocode an address to coordinates using Nominatim.
    Returns (latitude, longitude, country_code, city_state_str) or (None, None, None, None) on failure.
    Only calls Nominatim once per invocation; retries only on transient unavailability.
    """
    while True:
        try:
            geolocator = Nominatim(user_agent=f"dailySummaryEmail/{version}")
            location = geolocator.geocode(address, addressdetails=True, language="en")

            if location is None:
                logging.warning(f"Nominatim returned no results for address: {address}")
                return None, None, None, None

            latitude = location.latitude
            longitude = location.longitude

            raw = location.raw.get("address", {})
            country_code = raw.get("country_code", "us").lower()

            # Build a city/state string from available fields
            city = (
                raw.get("city")
                or raw.get("town")
                or raw.get("village")
                or raw.get("county")
                or ""
            )
            state = raw.get("state", "")
            if city and state:
                city_state_str = f"{city}, {state}"
            elif city:
                city_state_str = city
            elif state:
                city_state_str = state
            else:
                city_state_str = ""

            logging.info(
                f"Geocoded '{address}' -> ({latitude}, {longitude}), "
                f"country={country_code}, city_state='{city_state_str}'"
            )
            return latitude, longitude, country_code, city_state_str

        except (GeocoderUnavailable, GeocoderTimedOut):
            logging.warning("Geocoder unavailable or timed out. Retrying in 30 seconds...")
            time.sleep(30)
            continue

        except Exception as e:
            logging.error(f"Unexpected error while geocoding address '{address}': {e}")
            return None, None, None, None