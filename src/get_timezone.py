import logging

from timezonefinder import TimezoneFinder


def get_timezone(lat, lon):
    try:
        # Convert latitude and longitude to float
        lat = float(lat)
        lon = float(lon)

        # Initialize timezone finder
        tf = TimezoneFinder()

        # Get the timezone name
        timezone_str = tf.timezone_at(lng=lon, lat=lat)

        if timezone_str:
            return timezone_str
        else:
            return "Timezone not found"
    except Exception as e:
        logging.critical(f"An error occurred: {e}")
        return None