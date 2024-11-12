import time
import logging
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

def get_city_state(latitude, longitude, retries=5):
    geolocator = Nominatim(user_agent="dailySummaryEmail")

    for attempt in range(retries):
        try:
            # Perform the reverse geocoding
            location = geolocator.reverse((latitude, longitude), language='en')
            if location:
                address = location.raw.get('address', {})
                city = address.get('city', 'Unknown city')
                state = address.get('state', 'Unknown state')
                return f"{city}, {state}"
            else:
                logging.error("Failed to retrieve the location")
                return ""
        except GeocoderTimedOut as e:
            if attempt < retries - 1:
                time.sleep(10)  # Wait a bit before retrying
                continue
            else:
                logging.error(f"Geocoder timed out: {e}")
                return ""
        except GeocoderServiceError as e:
            logging.error(f"Geocoding service error: {str(e)}")
            return ""
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return ""
    logging.error("Failed to retrieve the city and state from coordinates after retries")
    return ""
