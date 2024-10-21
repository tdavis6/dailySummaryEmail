from geopy.geocoders import Photon


def get_coordinates(address):
    geolocator = Photon()
    location = geolocator.geocode(address)
    return location.latitude, location.longitude