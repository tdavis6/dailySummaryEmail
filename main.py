import datetime
import logging
import os
import time
import json
import pytz
from dotenv import load_dotenv

from get_cal_data import get_cal_data
from get_coordinates import get_coordinates
from get_date import get_current_date_in_timezone
from get_forecast import get_forecast
from get_puzzles import get_puzzles
from get_wotd import get_wotd
from get_quote import get_quote
from get_timezone import get_timezone
from get_todo_tasks import get_todo_tasks
from send_email import send_email

with open("version.json", "r"):
    VERSION = json.load(open("version.json"))["version"]

# Load the environment variables from the .env file
load_dotenv()

# Get the API key and coordinates from the environment variables
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
RECIPIENT_NAME = os.getenv("RECIPIENT_NAME")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
UNIT_SYSTEM = os.getenv("UNIT_SYSTEM")
TIME_SYSTEM = os.getenv("TIME_SYSTEM")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")
ADDRESS = os.getenv("ADDRESS")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
WEBCAL_LINKS = os.getenv("WEBCAL_LINKS")
PUZZLES = os.getenv("PUZZLES")
WOTD = os.getenv("WOTD")
QOTD = os.getenv("QOTD")

HOUR = os.getenv("HOUR")
MINUTE = os.getenv("MINUTE")
LOGGING_LEVEL=os.getenv("LOGGING_LEVEL")

# Reset logging configuration
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Validate and set logging level
if LOGGING_LEVEL:
    try:
        logging_level = getattr(logging, LOGGING_LEVEL.upper(), None)
        if not isinstance(logging_level, int):
            raise ValueError(f"Invalid log level: {LOGGING_LEVEL}")
        logging.basicConfig(level=logging_level)
    except Exception as e:
        logging.basicConfig(level=logging.INFO)
        logging.warning(
            f"Invalid LOGGING_LEVEL provided. Defaulting to INFO. Error: {e}"
        )
else:
    logging.basicConfig(level=logging.INFO)

if not SMTP_PORT:
    SMTP_PORT = 465 # Defaults to SSL

if not LATITUDE or not LONGITUDE:
    LATITUDE, LONGITUDE = get_coordinates(ADDRESS)

if not UNIT_SYSTEM:
    UNIT_SYSTEM = "METRIC" # Defaults to metric

if not TIME_SYSTEM:
    TIME_SYSTEM = "24HR" # Defaults to 24hr time

TIMEZONE = get_timezone(LATITUDE, LONGITUDE)
logging.info(f"Timezone set to {TIMEZONE} based on the coordinate pair {LATITUDE},{LONGITUDE}.")

if not HOUR:
    HOUR = int(datetime.datetime.now(pytz.timezone(TIMEZONE)).hour) # Defaults to current time

if not MINUTE:
    MINUTE = int(datetime.datetime.now(pytz.timezone(TIMEZONE)).minute) # Defaults to current time

if __name__ == "__main__":
    logging.info(f"Running version {VERSION}")
    try:
        timezone = pytz.timezone(TIMEZONE)
    except pytz.UnknownTimeZoneError:
        logging.critical(f"Timezone {TIMEZONE} is not valid")
        exit()
    while True: #I'm working on a more efficient method
        if int(datetime.datetime.now(timezone).hour) == int(HOUR) and int(datetime.datetime.now(timezone).minute) == int(MINUTE):
            try:
                date_string = get_current_date_in_timezone(timezone)
                weather_string = get_forecast(WEATHER_API_KEY, LATITUDE, LONGITUDE, UNIT_SYSTEM, TIME_SYSTEM)
                todo_string = get_todo_tasks(TIMEZONE, TIME_SYSTEM, TODOIST_API_KEY)
                cal_string = get_cal_data(WEBCAL_LINKS, TIMEZONE, TIME_SYSTEM)
                puzzles_string, puzzles_ans_string = get_puzzles() if PUZZLES in ["True", "true", True] else ("", "")
                wotd_string = get_wotd() if WOTD in ["True", "true", True] else ""
                quote_string = get_quote() if QOTD in ["True", "true", True] else ""

                send_email(
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
                    cal_string,
                    puzzles_string,
                    wotd_string,
                    quote_string,
                    puzzles_ans_string
                )
            except Exception as e:
                logging.critical(f"Error occurred: {e}")
        else:
            logging.info(f"Waiting until {"0" + str(HOUR) if len(str(HOUR)) == 1 else str(HOUR)}:{"0" + str(MINUTE) if len(str(MINUTE)) == 1 else str(MINUTE)} to send the message. Current time: {datetime.datetime.now(timezone).hour}:{"0" + str(datetime.datetime.now(timezone).minute) if len(str(datetime.datetime.now(timezone).minute)) == 1 else str(datetime.datetime.now(timezone).minute)}. Waiting 60 seconds.")
        time.sleep(60)
