from geopy.geocoders import Nominatim


def get_coordinates(address):
    geolocator = Nominatim(user_agent="dailySummaryEmail")
    location = geolocator.geocode(address)
    return location.latitude, location.longitude
