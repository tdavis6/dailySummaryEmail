from datetime import datetime, timedelta
import logging
import os
import time
import json
import pytz
import traceback
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
import waitress
from flask.logging import default_handler
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import signal
import sys
import threading

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

# Configuration file paths
CONFIG_FILE_PATH = "./data/config.json"
CACHE_FILE_PATH = "./cache/location_cache.json"

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

def ensure_directories_and_files_exist():
    """Ensure required directories and files exist."""
    os.makedirs("./data", exist_ok=True)
    os.makedirs("./cache", exist_ok=True)
    if not os.path.exists(CONFIG_FILE_PATH):
        with open(CONFIG_FILE_PATH, "w") as f:
            json.dump({}, f)
    if not os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, "w") as f:
            json.dump({}, f)

def load_config_from_json():
    """Load all configuration settings from the JSON file into a dictionary."""
    ensure_directories_and_files_exist()
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
        # Decrypt sensitive data fields
        if "SMTP_PASSWORD" in config and config["SMTP_PASSWORD"]:
            config["SMTP_PASSWORD"] = decrypt_data(config["SMTP_PASSWORD"])
        if "OPENAI_API_KEY" in config and config["OPENAI_API_KEY"]:
            config["OPENAI_API_KEY"] = decrypt_data(config["OPENAI_API_KEY"])
        if "TODOIST_API_KEY" in config and config["TODOIST_API_KEY"]:
            config["TODOIST_API_KEY"] = decrypt_data(config["TODOIST_API_KEY"])
        if "VIKUNJA_API_KEY" in config and config["VIKUNJA_API_KEY"]:
            config["VIKUNJA_API_KEY"] = decrypt_data(config["VIKUNJA_API_KEY"])
        return config

def get_config_value(config, key, default=None):
    """Retrieve a configuration setting from config.json dict, return default if not found."""
    return config.get(key, default)

def save_config_to_json(config_data):
    """Save the configuration data to the config.json file."""
    ensure_directories_and_files_exist()
    # Encrypt sensitive data fields before saving
    if "SMTP_PASSWORD" in config_data and config_data["SMTP_PASSWORD"]:
        config_data["SMTP_PASSWORD"] = encrypt_data(config_data["SMTP_PASSWORD"])
    if "OPENAI_API_KEY" in config_data and config_data["OPENAI_API_KEY"]:
        config_data["OPENAI_API_KEY"] = encrypt_data(config_data["OPENAI_API_KEY"])
    if "TODOIST_API_KEY" in config_data and config_data["TODOIST_API_KEY"]:
        config_data["TODOIST_API_KEY"] = encrypt_data(config_data["TODOIST_API_KEY"])
    if "VIKUNJA_API_KEY" in config_data and config_data["VIKUNJA_API_KEY"]:
        config_data["VIKUNJA_API_KEY"] = encrypt_data(config_data["VIKUNJA_API_KEY"])

    with open(CONFIG_FILE_PATH, "w") as json_file:
        json.dump(config_data, json_file, indent=4)

# Load environment variables from .env
load_dotenv()

with open("./version.json", "r") as f:
    VERSION = json.load(f)["version"]

# The ENCRYPTION_KEY must be provided as an environment variable
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise ValueError(
        "Encryption key not found. Please set the ENCRYPTION_KEY environment variable."
    )

cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return ""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

# Load config from JSON
json_config = load_config_from_json()

# Helper to get environment variable or fallback to config
def config_or_env(var_name, default=None):
    env_val = os.getenv(var_name)
    if env_val is not None:
        return env_val
    return get_config_value(json_config, var_name, default)

def str_to_bool(val):
    if isinstance(val, bool):
        return val
    return val.lower() in ["true", "1", "yes"]

RECIPIENT_EMAIL = config_or_env("RECIPIENT_EMAIL", "")
RECIPIENT_NAME = config_or_env("RECIPIENT_NAME", "")
SENDER_EMAIL = config_or_env("SENDER_EMAIL", "")
SMTP_USERNAME = config_or_env("SMTP_USERNAME", "")
SMTP_PASSWORD = config_or_env("SMTP_PASSWORD", "")
SMTP_HOST = config_or_env("SMTP_HOST", "")
SMTP_PORT = config_or_env("SMTP_PORT", "")
OPENAI_API_KEY = config_or_env("OPENAI_API_KEY", "")
UNIT_SYSTEM = config_or_env("UNIT_SYSTEM", "METRIC")
TIME_SYSTEM = config_or_env("TIME_SYSTEM", "24HR")
LATITUDE = config_or_env("LATITUDE")
LONGITUDE = config_or_env("LONGITUDE")
ADDRESS = config_or_env("ADDRESS", "")
WEATHER = str_to_bool(config_or_env("WEATHER", "False"))
TODOIST_API_KEY = config_or_env("TODOIST_API_KEY", "")
VIKUNJA_API_KEY = config_or_env("VIKUNJA_API_KEY", "")
VIKUNJA_BASE_URL = config_or_env("VIKUNJA_BASE_URL", "")
RSS_ENV = config_or_env("RSS_LINKS", "")
RSS_LINKS = RSS_ENV if RSS_ENV not in ["false", "False", None, ""] else False
WEBCAL_LINKS = config_or_env("WEBCAL_LINKS")
PUZZLES = str_to_bool(config_or_env("PUZZLES", "False"))
WOTD = str_to_bool(config_or_env("WOTD", "False"))
QOTD = str_to_bool(config_or_env("QOTD", "False"))
TIMEZONE = config_or_env("TIMEZONE", None)
HOUR = config_or_env("HOUR")
MINUTE = config_or_env("MINUTE")
LOGGING_LEVEL = config_or_env("LOGGING_LEVEL", "INFO").upper()

LOGGING_LEVEL = LOGGING_LEVEL if LOGGING_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] else "INFO"
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
logging.debug(f"Logging level set to: {LOGGING_LEVEL}")

# Ensure timezone is correctly loaded and utilized
global timezone
try:
    if not TIMEZONE:
        if LATITUDE and LONGITUDE:
            timezone_str = get_timezone(LATITUDE, LONGITUDE)
            timezone = pytz.timezone(timezone_str)
        else:
            # Default to UTC if no coords/timezone provided
            timezone = pytz.timezone("UTC")
    else:
        timezone = pytz.timezone(TIMEZONE)
    logging.info(f"Timezone set to: {timezone}.")
except Exception as e:
    logging.critical(f"Error creating timezone: {e}")
    exit(1)

executors = {
    'default': ThreadPoolExecutor(max_workers=5)
}

global scheduler
scheduler = BackgroundScheduler(executors=executors, timezone=timezone)

def refresh_configuration_variables():
    global RECIPIENT_EMAIL, RECIPIENT_NAME, SENDER_EMAIL, SMTP_USERNAME, \
        SMTP_PASSWORD, SMTP_HOST, SMTP_PORT, OPENAI_API_KEY, UNIT_SYSTEM, \
        TIME_SYSTEM, LATITUDE, LONGITUDE, ADDRESS, WEATHER, TODOIST_API_KEY, \
        VIKUNJA_API_KEY, VIKUNJA_BASE_URL, WEBCAL_LINKS, RSS_LINKS, PUZZLES, \
        WOTD, QOTD, TIMEZONE, HOUR, MINUTE, LOGGING_LEVEL, timezone, scheduler

    logging_level_old = LOGGING_LEVEL
    latitude_old, longitude_old, address_old = LATITUDE, LONGITUDE, ADDRESS
    hour_old, minute_old = HOUR, MINUTE

    # Reload from json and env
    new_json_config = load_config_from_json()

    def cfg(var_name, default=None):
        env_val = os.getenv(var_name)
        if env_val is not None:
            return env_val
        return get_config_value(new_json_config, var_name, default)

    RECIPIENT_EMAIL = cfg("RECIPIENT_EMAIL", "")
    RECIPIENT_NAME = cfg("RECIPIENT_NAME", "")
    SENDER_EMAIL = cfg("SENDER_EMAIL", "")
    SMTP_USERNAME = cfg("SMTP_USERNAME", "")
    SMTP_PASSWORD = cfg("SMTP_PASSWORD", "")
    SMTP_HOST = cfg("SMTP_HOST", "")
    SMTP_PORT = cfg("SMTP_PORT", "")
    OPENAI_API_KEY = cfg("OPENAI_API_KEY", "")
    UNIT_SYSTEM = cfg("UNIT_SYSTEM", "METRIC")
    TIME_SYSTEM = cfg("TIME_SYSTEM", "24HR")
    LATITUDE = cfg("LATITUDE")
    LONGITUDE = cfg("LONGITUDE")
    ADDRESS = cfg("ADDRESS", "")
    WEATHER = str_to_bool(cfg("WEATHER", "False"))
    TODOIST_API_KEY = cfg("TODOIST_API_KEY", "")
    VIKUNJA_API_KEY = cfg("VIKUNJA_API_KEY", "")
    VIKUNJA_BASE_URL = cfg("VIKUNJA_BASE_URL", "")
    RSS_ENV = cfg("RSS_LINKS", "")
    RSS_LINKS = RSS_ENV if RSS_ENV not in ["false", "False", None, ""] else False
    WEBCAL_LINKS = cfg("WEBCAL_LINKS")
    PUZZLES = str_to_bool(cfg("PUZZLES", "False"))
    WOTD = str_to_bool(cfg("WOTD", "False"))
    QOTD = str_to_bool(cfg("QOTD", "False"))
    TIMEZONE = cfg("TIMEZONE", None)
    HOUR = cfg("HOUR")
    MINUTE = cfg("MINUTE")
    LOGGING_LEVEL = cfg("LOGGING_LEVEL", "INFO").upper()

    if LOGGING_LEVEL != logging_level_old:
        change_logging_level()

    if latitude_old != LATITUDE or longitude_old != LONGITUDE or address_old != ADDRESS:
        refresh_location_cache()

    if (hour_old != HOUR or minute_old != MINUTE or address_old or latitude_old != LATITUDE or longitude_old != LONGITUDE
            or address_old != ADDRESS):

        if not LATITUDE or not LONGITUDE or LATITUDE == "" or LONGITUDE == "":
            logging.warning("Coordinates missing, attempting to calculate from address.")
            LATITUDE, LONGITUDE = get_coordinates(ADDRESS)

        try:
            LATITUDE = float(LATITUDE)
            LONGITUDE = float(LONGITUDE)
        except (ValueError, TypeError):
            logging.error("Unable to validate coordinates, setting as None.")
            LATITUDE, LONGITUDE = None, None

        timezone_str = get_timezone(LATITUDE, LONGITUDE)
        timezone = pytz.timezone(timezone_str)

        scheduler.shutdown(wait=False)

        scheduler = BackgroundScheduler(timezone=timezone)
        scheduler.start()

        # Check and remove the existing scheduled job
        if scheduler.get_job("daily_email_job"):
            logging.info("Removing existing job 'daily_email_job'.")
            scheduler.remove_job("daily_email_job")

        # Schedule the new job if HOUR and MINUTE are valid
        if scheduler.running and HOUR and MINUTE:
            scheduler.add_job(
                scheduled_email_job, "cron", hour=int(HOUR), minute=int(MINUTE), id="daily_email_job", timezone=timezone
            )
            logging.info("Email scheduling updated due to configuration change.")
        else:
            logging.warning("Scheduler is not running or invalid time provided. Cannot add job.")

    logging.info("Configuration refreshed.")

def load_location_cache():
    ensure_directories_and_files_exist()
    if not os.path.exists("./cache"):
        os.makedirs("./cache")
    if not os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, "w") as f:
            json.dump({}, f)

    if os.path.exists(CACHE_FILE_PATH):
        with open(CACHE_FILE_PATH, "r") as f:
            try:
                data = json.load(f)
                return (
                    data.get("LATITUDE"),
                    data.get("LONGITUDE"),
                    data.get("city_state_str"),
                )
            except json.JSONDecodeError:
                logging.error("Error decoding JSON from location cache.")
    return None, None, None

def save_location_cache(lat, long, city_state_str):
    with open(CACHE_FILE_PATH, "w") as f:
        json.dump(
            {"LATITUDE": lat, "LONGITUDE": long, "city_state_str": city_state_str}, f
        )
        logging.info("Location data saved to cache.")

def refresh_location_cache():
    ensure_directories_and_files_exist()
    global LATITUDE, LONGITUDE, city_state_str
    LATITUDE, LONGITUDE = get_coordinates(ADDRESS)
    logging.debug("Coordinates obtained from address.")
    city_state_str = get_city_state(LATITUDE, LONGITUDE)
    save_location_cache(LATITUDE, LONGITUDE, city_state_str)
    logging.debug("City and state obtained from coordinates.")
    return {"latitude": LATITUDE, "longitude": LONGITUDE, "city_state": city_state_str}

def change_logging_level():
    if LOGGING_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")
    logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
    logging.getLogger().setLevel(getattr(logging, LOGGING_LEVEL))
    app.logger.removeHandler(default_handler)  # Remove default handler
    app.logger.addHandler(logging.StreamHandler())  # Add new handler if needed
    app.logger.setLevel(getattr(logging, LOGGING_LEVEL))
    logging.info(f"Logging level changed to: {LOGGING_LEVEL}")

def get_weather():
    if WEATHER:
        weather = get_forecast(
            LATITUDE, LONGITUDE, city_state_str, UNIT_SYSTEM, TIME_SYSTEM, timezone
        )
        logging.debug("Weather data obtained.")
        return weather
    return ""

def get_todo():
    if TODOIST_API_KEY or VIKUNJA_API_KEY:
        todo = get_todo_tasks(
            timezone, TIME_SYSTEM, TODOIST_API_KEY, VIKUNJA_API_KEY, VIKUNJA_BASE_URL
        )
        logging.debug("Todo data obtained.")
        return todo
    logging.warning("Todo content is None or empty.")
    return ""

def get_rss_feed():
    if RSS_LINKS:
        rss = get_rss(RSS_LINKS, timezone, TIME_SYSTEM)
        logging.debug("RSS data obtained.")
        return rss
    logging.warning("RSS content is None or empty.")
    return ""

def get_quote_of_the_day():
    if QOTD:
        quote = get_quote()
        logging.debug("Quote of the day obtained.")
        return quote
    return ""

def get_word_of_the_day():
    if WOTD:
        wotd = get_wotd()
        logging.debug("Word of the day obtained.")
        return wotd
    return ""

def get_puzzles_of_the_day():
    if PUZZLES:
        puzzles, puzzles_ans = get_puzzles()
        logging.debug("Puzzles obtained.")
        return puzzles, puzzles_ans
    return "", ""

def prepare_send_email():
    """Function to send an email with all the gathered information."""
    try:
        logging.debug("prepare_send_email called.")

        # Start data collection
        logging.debug("Starting data collection for email content...")

        # Get current date string
        date_string = get_current_date_in_timezone(timezone)
        logging.debug("Date string obtained.")

        # Get weather information
        weather_string = get_weather() or ""
        logging.debug("Weather string obtained.")

        todo_string = get_todo() or ""
        logging.debug("Todo string obtained.")

        # Get calendar events
        calendar_events = get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM)
        logging.debug("Calendar events obtained.")

        # Get RSS feed
        rss_string = get_rss_feed() or ""
        logging.debug("RSS string obtained.")

        # Get Word of the Day
        wotd_string = get_word_of_the_day() or ""
        logging.debug("Word of the Day string obtained.")

        # Get Quote of the Day
        quote_string = get_quote_of_the_day() or ""
        logging.debug("Quote of the Day string obtained.")

        # Get puzzles
        puzzles_string, puzzles_ans_string = get_puzzles_of_the_day() or ("", "")
        logging.debug("Puzzles string obtained.")
        logging.debug("Puzzles answers string obtained.")

        # Attempt to send the email
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
            OPENAI_API_KEY if OPENAI_API_KEY else None,
            date_string,
            weather_string,
            todo_string,
            calendar_events,
            rss_string,
            puzzles_string,
            wotd_string,
            quote_string,
            puzzles_ans_string,
        )

        # If no exception occurred during send_email, log success here
        logging.info("Email sent successfully.")
        return True, None

    except Exception as e:
        error_message = str(e)
        traceback_str = traceback.format_exc()
        logging.critical(f"Error sending email: {error_message}")
        logging.critical(f"Traceback: {traceback_str}")
        # No success message here, just return failure
        return False, error_message

def scheduled_email_job():
    if not scheduler.running:
        logging.error("Scheduler is not running. Aborting job execution.")
        return
    logging.info("Executing scheduled_email_job.")
    try:
        prepare_send_email()
        logging.info("scheduled_email_job executed successfully.")
        reschedule_email_job()
    except RuntimeError as e:
        logging.error(f"RuntimeError in scheduled_email_job: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in scheduled_email_job: {e}")
        logging.error(traceback.format_exc())

def reschedule_email_job():
    try:
        scheduler.remove_job("daily_email_job")
        if HOUR and MINUTE:
            scheduler.add_job(
                scheduled_email_job, 'cron', hour=int(HOUR), minute=int(MINUTE), id='daily_email_job'
            )
            logging.info(f"Daily email job rescheduled at {HOUR}:{MINUTE} for the next day.")
        else:
            logging.warning("HOUR or MINUTE not configured properly, cannot reschedule job.")
    except Exception as e:
        logging.error(f"Failed to reschedule daily email job: {e}")

def format_wait_time(seconds):
    """Convert seconds into hours, minutes, and seconds for display."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

def get_seconds_until_next_schedule(hour, minute, timezone):
    """Calculate the seconds until the next scheduled time."""
    if isinstance(timezone, str):
        timezone = pytz.timezone(timezone)
        logging.debug(f"Converted timezone string to pytz timezone object: {timezone}")
    now = datetime.now(timezone).astimezone(timezone)  # Timezone-aware datetime
    next_schedule = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

    if now > next_schedule:
        next_schedule += timedelta(days=1)

    logging.debug(f"Current time: {now}")
    logging.debug(f"Next scheduled time: {next_schedule}")

    return (next_schedule - now).seconds

@app.route("/")
def home():
    return render_template('index.html', app_version=VERSION)

@app.route("/api/config", methods=["GET"])
def api_get_config():
    # Return the current config (excluding sensitive fields)
    current_config = load_config_from_json()
    # Sensitive fields are encrypted at rest, so safe to return decrypted version
    return jsonify(current_config)

@app.route("/api/save-config", methods=["POST"])
def api_save_config():
    try:
        data = request.json
        save_config_to_json(data)
        refresh_configuration_variables()
        return jsonify({"message": "Settings saved successfully!"})
    except Exception as e:
        return jsonify({"message": f"Failed to save settings. {str(e)}"}), 500

@app.route('/api/send-email', methods=['POST'])
def manually_send_email():
    success, error_message = prepare_send_email()
    if success:
        return jsonify({"message": "Email sent!"}), 200
    else:
        return jsonify({"message": f"Failed to send email: {error_message}"}), 500


@app.route("/api/schedule-email", methods=["POST"])
def schedule_email():
    try:
        data = request.json
        hour = data.get("hour", 0)
        minute = data.get("minute", 0)
        if scheduler.get_job("daily_email_job"):
            logging.info("Removing existing job 'daily_email_job'.")
            scheduler.remove_job("daily_email_job")
        scheduler.add_job(
            scheduled_email_job, 'cron', hour=int(hour), minute=int(minute), id='daily_email_job', timezone=timezone
        )
        return jsonify({"message": "Email schedule set!"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to schedule email. {e}"}), 500

@app.route("/api/interrupt-schedule", methods=["POST"])
def interrupt_schedule():
    try:
        scheduler.remove_job('daily_email_job')
        return jsonify({"message": "Email schedule interrupted!"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to interrupt schedule. {e}"}), 500

if __name__ == "__main__":
    def handle_shutdown_signal(signum, frame):
        logging.info("Shutdown signal received, shutting down scheduler...")
        scheduler.shutdown(wait=True)
        logging.info("Scheduler shutdown complete.")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    scheduler.start()
    logging.info("Scheduler started.")

    def run_flask():
        waitress.serve(app, host="0.0.0.0", port=8080)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    LATITUDE, LONGITUDE, city_state_str = load_location_cache()
    if not LATITUDE or not LONGITUDE or not city_state_str:
        refresh_location_cache()

    logging.info(f"Running version {VERSION}")

    # If HOUR/MINUTE not found, default to current time
    if not HOUR:
        HOUR = datetime.now(timezone).hour
    else:
        HOUR = int(HOUR)
    if not MINUTE:
        MINUTE = datetime.now(timezone).minute
    else:
        MINUTE = int(MINUTE)

    # Remove existing job if any before scheduling
    if scheduler.get_job("daily_email_job"):
        logging.info("Removing existing job 'daily_email_job'.")
        scheduler.remove_job("daily_email_job")

    # Schedule the email job with APScheduler if HOUR and MINUTE are set
    if HOUR is not None and MINUTE is not None:
        scheduler.add_job(
            scheduled_email_job, 'cron', hour=HOUR, minute=MINUTE, id='daily_email_job'
        )
        logging.info(f"Daily email job scheduled with APScheduler at {HOUR}:{MINUTE}.")

    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logging.info("Application shutting down...")
        scheduler.shutdown(wait=True)
        logging.info("Scheduler shutdown complete. Exiting.")
