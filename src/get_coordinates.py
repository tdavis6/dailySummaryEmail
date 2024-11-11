import time
import logging
from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Nominatim


def get_coordinates(address):
    while True:
        try:
            geolocator = Nominatim(user_agent="dailySummaryEmail")
            location = geolocator.geocode(address)
            latitude, longitude = location.latitude, location.longitude
            logging.debug(f"Latitude and longitude found.")
            return latitude, longitude
        except GeocoderUnavailable:
            logging.warning("Geocoder unavailable. Trying again in 30 seconds.")
            time.sleep(30)
            continue

