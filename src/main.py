from datetime import datetime, timedelta
import logging
import os
import time
import json
import pytz
from dotenv import load_dotenv
from cachetools import TTLCache
import traceback

from get_cal_data import get_cal_data
from get_coordinates import get_coordinates
from get_date import get_current_date_in_timezone
from get_city_state import get_city_state
from get_forecast import get_forecast
from get_rss import get_rss
from get_puzzles import get_puzzles
from get_wotd import get_wotd
from get_quote import get_quote
from get_timezone import get_timezone
from get_todo_tasks import get_todo_tasks
from send_email import send_email

# Load .env variables
load_dotenv()

# Cache file path
CACHE_FILE_PATH = "./cache/location_cache.json"

# Load version from version.json
with open("./version.json", "r") as f:
    VERSION = json.load(f)["version"]

# Configuration from environment variables
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
assert RECIPIENT_EMAIL, "RECIPIENT_EMAIL environment variable is not set."

RECIPIENT_NAME = os.getenv("RECIPIENT_NAME")
assert RECIPIENT_NAME, "RECIPIENT_NAME environment variable is not set."

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
assert SENDER_EMAIL, "SENDER_EMAIL environment variable is not set."

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
assert SMTP_USERNAME, "SMTP_USERNAME environment variable is not set."

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
assert SMTP_PASSWORD, "SMTP_PASSWORD environment variable is not set."

SMTP_HOST = os.getenv("SMTP_HOST")
assert SMTP_HOST, "SMTP_HOST environment variable is not set."

SMTP_PORT = os.getenv("SMTP_PORT")
assert SMTP_PORT, "SMTP_PORT environment variable is not set."

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
UNIT_SYSTEM = os.getenv("UNIT_SYSTEM", "METRIC")
TIME_SYSTEM = os.getenv("TIME_SYSTEM", "24HR")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")
ADDRESS = os.getenv("ADDRESS")
WEATHER = os.getenv("WEATHER", False)
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
WEBCAL_LINKS = os.getenv("WEBCAL_LINKS")
RSS_LINKS = os.getenv("RSS_LINKS")
PUZZLES = os.getenv("PUZZLES")
WOTD = os.getenv("WOTD")
QOTD = os.getenv("QOTD")
TIMEZONE = os.getenv("TIMEZONE")
HOUR = os.getenv("HOUR")
MINUTE = os.getenv("MINUTE")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

# Initialize logging
if LOGGING_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
logging.debug(f"Logging level set to: {LOGGING_LEVEL}")

# Initialize Cache
cache = TTLCache(maxsize=100, ttl=3600)  # 1-hour TTL for cached data

# Check for or load cached location data
def load_location_cache():
    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, 'r') as f:
            try:
                data = json.load(f)
                return data.get("LATITUDE"), data.get("LONGITUDE"), data.get("city_state_str")
            except json.JSONDecodeError:
                logging.error("Error decoding JSON from location cache.")
    return None, None, None

def save_location_cache(lat, long, city_state_str):
    with open(CACHE_FILE_PATH, 'w') as f:
        json.dump({"LATITUDE": lat, "LONGITUDE": long, "city_state_str": city_state_str}, f)
        logging.info("Location data saved to cache.")

# Initialize coordinates
LATITUDE, LONGITUDE, city_state_str = load_location_cache()

if not LATITUDE or not LONGITUDE or not city_state_str:
    if not ADDRESS:
        logging.critical("No address provided. Please set ADDRESS or LATITUDE and LONGITUDE.")
        exit(1)
    else:
        LATITUDE, LONGITUDE = get_coordinates(ADDRESS)
        logging.debug("Coordinates obtained from address.")
        city_state_str = get_city_state(LATITUDE, LONGITUDE)
        save_location_cache(LATITUDE, LONGITUDE, city_state_str)
else:
    logging.info("Using cached LATITUDE, LONGITUDE, and city_state_str.")

try:
    if not TIMEZONE:
        timezone_str = get_timezone(LATITUDE, LONGITUDE)
        timezone = pytz.timezone(timezone_str)
    else:
        timezone = pytz.timezone(TIMEZONE)
    logging.info(f"Timezone found: {timezone}.")
except Exception as e:
    logging.critical(f"Error creating timezone: {e}")
    exit(1)

def get_cached_data(key, fetch_function, *args, **kwargs):
    """Fetch data from cache or call the function if not cached."""
    if key in cache:
        logging.info(f"Using cached data for {key}.")
        return cache[key]

    logging.info(f"Fetching fresh data for {key}.")
    data = fetch_function(*args, **kwargs)
    cache[key] = data
    return data

def get_weather():
    if WEATHER in ["True", "true", True]:
        weather = get_cached_data(
            "weather",
            get_forecast,
            LATITUDE,
            LONGITUDE,
            city_state_str,
            UNIT_SYSTEM,
            TIME_SYSTEM,
            timezone
        )
        logging.debug(f"Weather data obtained")
        return weather
    return ""

def get_todo():
    todo = get_cached_data(
        "todo",
        get_todo_tasks,
        timezone,
        TIME_SYSTEM,
        TODOIST_API_KEY
    )
    logging.debug(f"Todo data obtained")
    return todo

def get_rss_feed():
    rss = get_cached_data("rss", get_rss, RSS_LINKS, timezone, TIME_SYSTEM)
    logging.debug(f"RSS data obtained")
    return rss

def get_quote_of_the_day():
    if QOTD in ["True", "true", True]:
        quote = get_cached_data("quote", get_quote)
        logging.debug(f"Quote of the day obtained")
        return quote
    return ""

def get_word_of_the_day():
    if WOTD in ["True", "true", True]:
        wotd = get_cached_data("wotd", get_wotd)
        logging.debug(f"Word of the day obtained")
        return wotd
    return ""

def get_puzzles_of_the_day():
    if PUZZLES in ["True", "true", True]:
        puzzles, puzzles_ans = get_cached_data("puzzles", get_puzzles)
        logging.debug(f"Puzzles obtained")
        logging.debug(f"Puzzles answers obtained")
        return puzzles, puzzles_ans
    return "", ""

def send_scheduled_email(timezone):
    """Function to send an email with all the gathered information."""
    try:
        logging.debug("send_scheduled_email called with timezone")

        # Ensure timezone is a pytz timezone object
        if isinstance(timezone, str):
            timezone = pytz.timezone(timezone)
            logging.debug(f"Converted timezone string to pytz timezone object")

        # Start data collection
        logging.debug("Starting data collection for email content...")

        # Get current date string
        date_string = get_current_date_in_timezone(timezone)
        logging.debug(f"Date string obtained")

        # Get weather information
        weather_string = get_weather()
        logging.debug(f"Weather string obtained")

        # Get task items
        todo_string = get_todo()
        logging.debug(f"Todo string obtained")

        # Get RSS feed updates
        rss_string = get_rss_feed()
        logging.debug(f"RSS string obtained")

        # Get Word of the Day
        wotd_string = get_word_of_the_day()
        logging.debug(f"Word of the Day string obtained")

        # Get Quote of the Day
        quote_string = get_quote_of_the_day()
        logging.debug(f"Quote of the Day string obtained")

        # Get puzzles
        puzzles_string, puzzles_ans_string = get_puzzles_of_the_day()
        logging.debug(f"Puzzles string obtained")
        logging.debug(f"Puzzles answers string obtained")

        # Get calendar events as a list of dictionaries
        calendar_events = get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM)
        logging.debug(f"Calendar events obtained")

        # Pass all gathered data to the send_email function
        send_email(
            VERSION,
            timezone,
            RECIPIENT_EMAIL,
            RECIPIENT_NAME,
            SENDER_EMAIL,
            SMTP_USERNAME,
            SMTP_PASSWORD,
            SMTP_HOST,
            SMTP_PORT,
            OPENAI_API_KEY,
            date_string,
            weather_string,
            todo_string,
            calendar_events,
            rss_string,
            puzzles_string,
            wotd_string,
            quote_string,
            puzzles_ans_string
        )

    except Exception as e:
        logging.critical(f"Error during email send: {e}")
        traceback_str = traceback.format_exc()
        logging.critical(f"Traceback: {traceback_str}")

def format_wait_time(seconds):
    """Convert seconds into hours, minutes, and seconds for display."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

def get_seconds_until_next_schedule(hour, minute, timezone):
    """Calculate the seconds until the next scheduled time."""
    # Ensure timezone is a pytz timezone object
    if isinstance(timezone, str):
        timezone = pytz.timezone(timezone)
        logging.debug(f"Converted timezone string to pytz timezone object: {timezone}")

    now = datetime.now(timezone)  # Timezone-aware datetime
    next_schedule = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if now > next_schedule:
        next_schedule += timedelta(days=1)

    logging.debug(f"Current time: {now}")
    logging.debug(f"Next scheduled time: {next_schedule}")

    return (next_schedule - now).seconds

if __name__ == "__main__":
    logging.info(f"Running version {VERSION}")

    # Send email immediately upon start
    send_scheduled_email(timezone)

    if HOUR and MINUTE:
        HOUR = int(HOUR)
        MINUTE = int(MINUTE)
    else:
        HOUR = datetime.now(timezone).hour
        MINUTE = datetime.now(timezone).minute

    # Run the email scheduling loop
    while True:
        wait_time = get_seconds_until_next_schedule(HOUR, MINUTE, timezone)
        logging.info(f"Next email scheduled in {format_wait_time(wait_time)}.")
        time.sleep(wait_time)

        # Send the email when the time arrives
        send_scheduled_email(timezone)
