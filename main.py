import os
from dotenv import load_dotenv
import datetime
import time
import pytz
import logging

from get_forecast import get_forecast
from send_email import send_email
from get_todoist_tasks import get_todoist_tasks
from get_ical_events import get_ics_events

VERSION = "0.1.0 (4)"

# Load the environment variables from the .env file
load_dotenv()

# Get the API key and coordinates from the environment variables
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
LATITUDE = os.getenv("LATITUDE")
LONGITUDE = os.getenv("LONGITUDE")
TODOIST_API_KEY = os.getenv("TODOIST_API_KEY")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
RECIPIENT_NAME = os.getenv("RECIPIENT_NAME")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")
TIMEZONE = os.getenv("TIMEZONE")
HOUR = os.getenv("HOUR")
MINUTE = os.getenv("MINUTE")
WEBCAL_LINKS = os.getenv("WEBCAL_LINKS")

if not SMTP_PORT:
    SMTP_PORT = 465 # Defaults to SSL

if not HOUR:
    HOUR = int(datetime.datetime.now(pytz.timezone(TIMEZONE)).hour) # Defaults to 6 AM

if not MINUTE:
    MINUTE = int(datetime.datetime.now(pytz.timezone(TIMEZONE)).minute) # Defaults to 00 minutes

if __name__ == "__main__":
    logging.info(f"Running version {VERSION}")
    print(f"Running version {VERSION}")
    try:
        timezone = pytz.timezone(TIMEZONE)
    except pytz.UnknownTimeZoneError:
        logging.critical(f"Timezone {TIMEZONE} is not valid")
        exit()
    while True: #I'm working on a more efficient method
        if int(datetime.datetime.now(timezone).hour) == int(HOUR) and int(datetime.datetime.now(timezone).minute) == int(MINUTE):
            try:
                weather_data = get_forecast(WEATHER_API_KEY, LATITUDE, LONGITUDE)
                logging.debug("Weather data received")
                todoist_data = get_todoist_tasks(TODOIST_API_KEY=TODOIST_API_KEY, TIMEZONE=TIMEZONE)
                logging.debug("Todoist data received")
                cal_data = ""
                for link in WEBCAL_LINKS.split(","):
                    cal_data = cal_data + get_ics_events(url=link, timezone=TIMEZONE)
                logging.debug("Calendar data received")
                send_email(
                    RECIPIENT_EMAIL,
                    RECIPIENT_NAME,
                    SENDER_EMAIL,
                    SMTP_USERNAME,
                    SMTP_PASSWORD,
                    SMTP_HOST,
                    SMTP_PORT,
                    weather_data,
                    todoist_data,
                    cal_data,
                    timezone,
                    TIMEZONE
                )
            except Exception as e:
                logging.critical(f"Error occurred: {e}")
        else:
            logging.info(f"Waiting until {HOUR}:{MINUTE} to send the message. Current time: {datetime.datetime.now(timezone).hour}:{datetime.datetime.now(timezone).minute}. Waiting 60 seconds.")
            print(f"Waiting until {HOUR}:{MINUTE} to send the message. Current time: {datetime.datetime.now(timezone).hour}:{datetime.datetime.now(timezone).minute}. Waiting 60 seconds.")
        time.sleep(60)
