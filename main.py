import datetime
import logging
import os
import time
import pytz
from dotenv import load_dotenv

from get_cal_data import get_cal_data
from get_coordinates import get_coordinates
from get_date import get_current_date_in_timezone
from get_forecast import get_forecast
from get_quote import get_quote
from get_timezone import get_timezone
from get_todo_tasks import get_todo_tasks
from send_email import send_email

VERSION = "0.1.0 (14)"

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
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")
ADDRESS = os.getenv("ADDRESS")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
WEBCAL_LINKS = os.getenv("WEBCAL_LINKS")
HOUR = os.getenv("HOUR")
MINUTE = os.getenv("MINUTE")
LOGGING_LEVEL=os.getenv("LOGGING_LEVEL")

if not LOGGING_LEVEL:
    LOGGING_LEVEL = logging.INFO
else:
    logging.basicConfig(level=logging.getLevelName(LOGGING_LEVEL))

if not SMTP_PORT:
    SMTP_PORT = 465 # Defaults to SSL

if not LATITUDE or not LONGITUDE:
    LATITUDE, LONGITUDE = get_coordinates(ADDRESS)

TIMEZONE = get_timezone(LATITUDE, LONGITUDE)

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
                weather_string = get_forecast(WEATHER_API_KEY, LATITUDE, LONGITUDE)
                todo_string = get_todo_tasks(TIMEZONE, TODOIST_API_KEY)
                cal_string = get_cal_data(WEBCAL_LINKS, TIMEZONE)
                quote_string = get_quote()

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
                    quote_string
                )
            except Exception as e:
                logging.critical(f"Error occurred: {e}")
        else:
            logging.info(f"Waiting until {"0" + str(HOUR) if len(str(HOUR)) == 1 else str(HOUR)}:{"0" + str(MINUTE) if len(str(MINUTE)) == 1 else str(MINUTE)} to send the message. Current time: {datetime.datetime.now(timezone).hour}:{"0" + str(datetime.datetime.now(timezone).minute) if len(str(datetime.datetime.now(timezone).minute)) == 1 else str(datetime.datetime.now(timezone).minute)}. Waiting 60 seconds.")
        time.sleep(60)
