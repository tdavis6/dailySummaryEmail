import os
from dotenv import load_dotenv
import datetime
import time
import pytz
import logging

from get_forecast import get_forecast
from send_email import send_email
from get_todoist_tasks import get_todoist_tasks

VERSION = "0.1.0 (3)"

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

if not SMTP_PORT:
    SMTP_PORT = 465 # Defaults to SSL

if not HOUR:
    HOUR = 6 # Defaults to 6 AM

if not MINUTE:
    MINUTE = 00 # Defaults to 00 minutes

if __name__ == "__main__":
    print(f"Running version {VERSION}")
    logging.info(f"Running version {VERSION}")
    try:
        timezone = pytz.timezone(TIMEZONE)
    except pytz.UnknownTimeZoneError:
        print(f"Timezone {TIMEZONE} is not valid")
        logging.critical(f"Timezone {TIMEZONE} is not valid")
        exit()
    while True: #I'm working on a more efficient method
        if int(datetime.datetime.now(timezone).hour) == int(HOUR) and int(datetime.datetime.now(timezone).minute) == int(MINUTE):
            try:
                weather_data = get_forecast(WEATHER_API_KEY, LATITUDE, LONGITUDE)
                todoist_data = get_todoist_tasks(TODOIST_API_KEY=TODOIST_API_KEY, TIMEZONE=TIMEZONE)
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
                    timezone,
                    TIMEZONE
                )
            except Exception as e:
                print(f"Error occurred: {e}")
                logging.critical(f"Error occurred: {e}")
        else:
            print(f"Waiting until {HOUR}:{MINUTE} to send the message. Current time: {datetime.datetime.now(timezone).hour}:{datetime.datetime.now(timezone).minute}. Waiting 60 seconds.")
            logging.info(f"Waiting until {HOUR}:{MINUTE} to send the message. Current time: {datetime.datetime.now(timezone).hour}:{datetime.datetime.now(timezone).minute}. Waiting 60 seconds.")
        time.sleep(60)
