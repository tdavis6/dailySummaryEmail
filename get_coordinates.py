from geopy.exc import GeocoderUnavailable
from geopy.geocoders import Photon
from geopy.geocoders import Nominatim


def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="dailySummaryEmail")
        location = geolocator.geocode(address)
        return location.latitude, location.longitude
    except GeocoderUnavailable:
        geolocator = Photon()
        location = geolocator.geocode(address)
        return location.latitude, location.longitude
