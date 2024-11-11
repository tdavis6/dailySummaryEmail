from datetime import datetime, timedelta
import logging
import os
import time
import json
import pytz
from dotenv import load_dotenv
from cachetools import TTLCache

from get_cal_data import get_cal_data
from get_coordinates import get_coordinates
from get_date import get_current_date_in_timezone
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


UNIT_SYSTEM = os.getenv("UNIT_SYSTEM", "METRIC")
TIME_SYSTEM = os.getenv("TIME_SYSTEM", "24HR")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")
ADDRESS = os.getenv("ADDRESS")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
WEBCAL_LINKS = os.getenv("WEBCAL_LINKS")
RSS_LINKS = os.getenv("RSS_LINKS")
PUZZLES = os.getenv("PUZZLES")
WOTD = os.getenv("WOTD")
QOTD = os.getenv("QOTD")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
HOUR = os.getenv("HOUR")
MINUTE = os.getenv("MINUTE")
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO").upper()

# Initialize logging
if LOGGING_LEVEL not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
    raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
logging.debug(f"Logging level set to: {LOGGING_LEVEL}")

# Initialize coordinates
if not LATITUDE and not LONGITUDE:
    if not ADDRESS:
        logging.critical("No address provided. Please set ADDRESS or LATITUDE and LONGITUDE.")
        exit(1)
    else:
        LATITUDE, LONGITUDE = get_coordinates(ADDRESS)
        logging.debug(f"Coordinates obtained from address: LATITUDE={LATITUDE}, LONGITUDE={LONGITUDE}")
else:
    # Use provided LATITUDE and LONGITUDE without re-fetching
    logging.info(f"Using provided LATITUDE: {LATITUDE}, LONGITUDE: {LONGITUDE}")

try:
    if not TIMEZONE:
        # Fetch timezone based on the coordinates
        timezone_str = get_timezone(LATITUDE, LONGITUDE)
        timezone = pytz.timezone(timezone_str)
    else:
        timezone = pytz.timezone(TIMEZONE)
    logging.info(f"Timezone found: {timezone}.")
except Exception as e:
    logging.critical(f"Error creating timezone: {e}")
    exit(1)

# Initialize Cache
cache = TTLCache(maxsize=100, ttl=3600)  # 1-hour TTL for cached data

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
    weather = get_cached_data(
        "weather",
        get_forecast,
        WEATHER_API_KEY,
        LATITUDE,
        LONGITUDE,
        UNIT_SYSTEM,
        TIME_SYSTEM
    )
    logging.debug(f"Weather data: {weather}")
    return weather

def get_todo():
    todo = get_cached_data(
        "todo",
        get_todo_tasks,
        timezone,
        TIME_SYSTEM,
        TODOIST_API_KEY
    )
    logging.debug(f"Todo data: {todo}")
    return todo

def get_rss_feed():
    rss = get_cached_data("rss", get_rss, RSS_LINKS, timezone, TIME_SYSTEM)
    logging.debug(f"RSS data: {rss}")
    return rss

def get_quote_of_the_day():
    if QOTD in ["True", "true", True]:
        quote = get_cached_data("quote", get_quote)
        logging.debug(f"Quote of the day: {quote}")
        return quote
    return ""

def get_word_of_the_day():
    if WOTD in ["True", "true", True]:
        wotd = get_cached_data("wotd", get_wotd)
        logging.debug(f"Word of the day: {wotd}")
        return wotd
    return ""

def get_puzzles_of_the_day():
    if PUZZLES in ["True", "true", True]:
        puzzles, puzzles_ans = get_cached_data("puzzles", get_puzzles)
        logging.debug(f"Puzzles: {puzzles}")
        logging.debug(f"Puzzles answers: {puzzles_ans}")
        return puzzles, puzzles_ans
    return "", ""

def send_scheduled_email(timezone):
    """Function to send an email with all the gathered information."""
    try:
        # Debug the timezone parameter
        logging.debug(f"send_scheduled_email called with timezone: {timezone} (type: {type(timezone)})")

        # Ensure timezone is a pytz timezone object
        if isinstance(timezone, str):
            timezone = pytz.timezone(timezone)
            logging.debug(f"Converted timezone string to pytz timezone object: {timezone} (type: {type(timezone)})")

        # Start data collection
        logging.debug("Starting data collection for email content...")

        # Get current date string
        logging.debug("Getting current date string...")
        date_string = get_current_date_in_timezone(timezone)
        logging.debug(f"Date string obtained: {date_string}")

        # Get weather information
        logging.debug("Getting weather information...")
        weather_string = get_weather()
        logging.debug(f"Weather string obtained: {weather_string}")

        # Get task items
        logging.debug("Getting todo tasks...")
        todo_string = get_todo()
        logging.debug(f"Todo string obtained: {todo_string}")

        # Get RSS feed updates
        logging.debug("Getting RSS feed updates...")
        rss_string = get_rss_feed()
        logging.debug(f"RSS string obtained: {rss_string}")

        # Get Word of the Day
        logging.debug("Getting Word of the Day...")
        wotd_string = get_word_of_the_day()
        logging.debug(f"Word of the Day string obtained: {wotd_string}")

        # Get Quote of the Day
        logging.debug("Getting Quote of the Day...")
        quote_string = get_quote_of_the_day()
        logging.debug(f"Quote of the Day string obtained: {quote_string}")

        # Get puzzles
        logging.debug("Getting puzzles...")
        puzzles_string, puzzles_ans_string = get_puzzles_of_the_day()
        logging.debug(f"Puzzles string obtained: {puzzles_string}")
        logging.debug(f"Puzzles answers string obtained: {puzzles_ans_string}")

        # Get calendar events
        logging.debug("Getting calendar events...")
        calendar_string = get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM)
        logging.debug(f"Calendar string obtained: {calendar_string}")

        logging.debug("All data collected. Preparing to send email...")

        # Call send_email with collected data
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
            date_string,
            weather_string,
            todo_string,
            calendar_string,
            rss_string,
            puzzles_string,
            wotd_string,
            quote_string,
            puzzles_ans_string
        )

        logging.debug(f"Type of timezone after send_email call: {type(timezone)}")
        logging.debug(f"Timezone after send_email call: {timezone}")

    except Exception as e:
        logging.critical(f"Error during email send: {e}")

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
    logging.debug(f"Type of timezone in get_seconds_until_next_schedule: {type(timezone)}")
    logging.debug(f"Timezone in get_seconds_until_next_schedule: {timezone}")

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
