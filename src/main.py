import json
import logging
import os
import signal
import sys
import threading
import time
import traceback
from datetime import datetime, timedelta
from functools import wraps

import pytz
import waitress
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.background import BackgroundScheduler
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from flask.logging import default_handler
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

from get_cal_data import get_cal_data
from get_city_state import get_city_state
from get_coordinates import get_coordinates
from get_date import get_current_date_in_timezone
from get_forecast import get_forecast
from get_puzzles import get_puzzles
from get_qotd import get_qotd
from get_rss import get_rss
from get_timezone import get_timezone
from get_todo_tasks import get_todo_tasks
from get_wotd import get_wotd
from send_email import send_email


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
    """Load all configuration settings from the JSON file into a dictionary, decrypting sensitive fields."""
    ensure_directories_and_files_exist()
    with open(CONFIG_FILE_PATH, "r") as f:
        config = json.load(f)
        # Decrypt sensitive data fields
        config["SMTP_PASSWORD"] = decrypt_data(config.get("SMTP_PASSWORD", ""))
        config["OPENAI_API_KEY"] = decrypt_data(config.get("OPENAI_API_KEY", ""))
        config["TODOIST_API_KEY"] = decrypt_data(config.get("TODOIST_API_KEY", ""))
        config["VIKUNJA_API_KEY"] = decrypt_data(config.get("VIKUNJA_API_KEY", ""))
        config["LATITUDE"] = decrypt_data(config.get("LATITUDE", ""))
        config["LONGITUDE"] = decrypt_data(config.get("LONGITUDE", ""))
        config["ADDRESS"] = decrypt_data(config.get("ADDRESS", ""))
        return config

def get_config_value(key, default=None):
    """Retrieve a specific configuration setting from the JSON file."""
    config = load_config_from_json()
    return config.get(key, default)

def save_config_to_json(config_data):
    """Save the configuration data to the config.json file with encrypted sensitive fields."""
    ensure_directories_and_files_exist()
    # Encrypt sensitive data fields before saving
    config_data["SMTP_PASSWORD"] = encrypt_data(config_data.get("SMTP_PASSWORD", ""))
    config_data["OPENAI_API_KEY"] = encrypt_data(config_data.get("OPENAI_API_KEY", ""))
    config_data["TODOIST_API_KEY"] = encrypt_data(config_data.get("TODOIST_API_KEY", ""))
    config_data["VIKUNJA_API_KEY"] = encrypt_data(config_data.get("VIKUNJA_API_KEY", ""))
    config_data["LATITUDE"] = encrypt_data(config_data.get("LATITUDE", ""))
    config_data["LONGITUDE"] = encrypt_data(config_data.get("LONGITUDE", ""))
    config_data["ADDRESS"] = encrypt_data(config_data.get("ADDRESS", ""))
    with open(CONFIG_FILE_PATH, "w") as json_file:
        json.dump(config_data, json_file, indent=4)

def initialize_config():
    """Initialize configuration by first loading config.json, then overriding with .env if present."""
    config_keys = [
        "RECIPIENT_EMAIL",
        "RECIPIENT_NAME",
        "SENDER_EMAIL",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "SMTP_HOST",
        "SMTP_PORT",
        "OPENAI_API_KEY",
        "ENABLE_SUMMARY",
        "UNIT_SYSTEM",
        "TIME_SYSTEM",
        "LATITUDE",
        "LONGITUDE",
        "ADDRESS",
        "WEATHER",
        "TODOIST_API_KEY",
        "VIKUNJA_API_KEY",
        "VIKUNJA_BASE_URL",
        "WEBCAL_LINKS",
        "RSS_LINKS",
        "PUZZLES",
        "PUZZLES_ANSWERS",
        "WOTD",
        "QOTD",
        "TIMEZONE",
        "HOUR",
        "MINUTE",
        "LOGGING_LEVEL",
    ]

    # Load existing configuration from JSON
    existing_config = load_config_from_json()

    # Create a dictionary to hold final configuration values
    config_data = {}

    for key in config_keys:
        env_val = os.getenv(key, None)

        if env_val is None:
            # Env var not present, log and use config.json or blank
            logging.debug(f"Environment variable '{key}' not found. Using config.json or blank.")
            config_data[key] = existing_config.get(key, "")
        else:
            # Env var present, use it and override config.json
            config_data[key] = env_val

    # Save final config to JSON
    save_config_to_json(config_data)

def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    if not encrypted_data:
        return ""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()

def refresh_configuration_variables():
    """
    Reload configuration settings, refresh global variables, and handle location/timezone changes.
    """
    global RECIPIENT_EMAIL, RECIPIENT_NAME, SENDER_EMAIL, SMTP_USERNAME, SMTP_PASSWORD
    global SMTP_HOST, SMTP_PORT, OPENAI_API_KEY, ENABLE_SUMMARY, UNIT_SYSTEM, TIME_SYSTEM
    global LATITUDE, LONGITUDE, ADDRESS, WEATHER, TODOIST_API_KEY, VIKUNJA_API_KEY
    global VIKUNJA_BASE_URL, WEBCAL_LINKS, RSS_LINKS, PUZZLES, PUZZLES_ANSWERS, WOTD, QOTD
    global TIMEZONE, HOUR, MINUTE, LOGGING_LEVEL, timezone, scheduler

    # Keep old values to detect changes
    logging_level_old = LOGGING_LEVEL
    latitude_old, longitude_old, address_old = float(LATITUDE) if LATITUDE not in [None, ""] else None, float(LONGITUDE) if LONGITUDE not in [None, ""] else None, str(ADDRESS) if ADDRESS not in [None, ""] else ""
    hour_old, minute_old = HOUR, MINUTE

    # Reload fresh config from JSON
    config = load_config_from_json()

    # Update global vars from config
    RECIPIENT_EMAIL = config.get("RECIPIENT_EMAIL")
    RECIPIENT_NAME = config.get("RECIPIENT_NAME")
    SENDER_EMAIL = config.get("SENDER_EMAIL")
    SMTP_USERNAME = config.get("SMTP_USERNAME")
    SMTP_PASSWORD = config.get("SMTP_PASSWORD")
    SMTP_HOST = config.get("SMTP_HOST")
    SMTP_PORT = config.get("SMTP_PORT")
    OPENAI_API_KEY = config.get("OPENAI_API_KEY")
    ENABLE_SUMMARY = config.get("ENABLE_SUMMARY", "False")
    UNIT_SYSTEM = config.get("UNIT_SYSTEM", "METRIC")
    TIME_SYSTEM = config.get("TIME_SYSTEM", "24HR")
    LATITUDE = config.get("LATITUDE")
    LONGITUDE = config.get("LONGITUDE")
    ADDRESS = config.get("ADDRESS")
    WEATHER = config.get("WEATHER", "False")
    TODOIST_API_KEY = config.get("TODOIST_API_KEY")
    VIKUNJA_API_KEY = config.get("VIKUNJA_API_KEY")
    VIKUNJA_BASE_URL = config.get("VIKUNJA_BASE_URL")
    WEBCAL_LINKS = config.get("WEBCAL_LINKS")
    RSS_LINKS = config.get("RSS_LINKS", "False")
    PUZZLES = config.get("PUZZLES", "False")
    PUZZLES_ANSWERS = config.get("PUZZLES_ANSWERS", "False")
    WOTD = config.get("WOTD", "False")
    QOTD = config.get("QOTD", "False")
    TIMEZONE = config.get("TIMEZONE", None)
    HOUR = config.get("HOUR")
    MINUTE = config.get("MINUTE")
    LOGGING_LEVEL = config.get("LOGGING_LEVEL", "INFO").upper()

    logging.debug(
        f"Latitude old='{latitude_old}' vs. new='{LATITUDE}'\n"
        f"Longitude old='{longitude_old}' vs. new='{LONGITUDE}'\n"
        f"Address old='{address_old}' vs. new='{ADDRESS}'"
    )

    if (LATITUDE is not None and LATITUDE != "" and float(LATITUDE) != latitude_old) or \
       (LONGITUDE is not None and LONGITUDE != "" and float(LONGITUDE) != longitude_old) or \
       (ADDRESS is not None and ADDRESS.strip() != address_old.strip()) :
        logging.debug("Location data changed. Refreshing location cache...")
        location_cache = refresh_location_cache()

        if location_cache:
            LATITUDE = location_cache["latitude"]
            LONGITUDE = location_cache["longitude"]
            if not ADDRESS or not ADDRESS.strip():
                ADDRESS = location_cache["city_state"]
        else:
            # fallback
            LATITUDE, LONGITUDE = latitude_old, longitude_old

        try:
            if not TIMEZONE or not TIMEZONE.strip():
                if LATITUDE and LONGITUDE:
                    TIMEZONE = get_timezone(LATITUDE, LONGITUDE)
                else:
                    logging.warning("Cannot derive TIMEZONE; missing lat/long.")
                    TIMEZONE = None
            timezone = pytz.timezone(TIMEZONE) if TIMEZONE else None
            logging.info(f"Timezone validated and set to: {timezone}")
        except Exception as e:
            logging.critical(f"Error validating TIMEZONE: {e}")
            timezone = None

    # Update logging level if changed
    if LOGGING_LEVEL != logging_level_old:
        change_logging_level()

    # If the schedule time changed, reschedule the daily email job
    if (float(hour_old) != float(HOUR)) or (float(minute_old) != float(MINUTE)):
        reschedule_email_job()

    logging.info("Configuration refreshed successfully.")

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
    """
    Refreshes location data. If valid LATITUDE and LONGITUDE exist, use them.
    Otherwise, if ADDRESS is set, try geocoding.
    Returns a dict with { 'latitude', 'longitude', 'city_state' } or None on failure.
    """
    ensure_directories_and_files_exist()
    global LATITUDE, LONGITUDE, city_state_str

    # If lat/long are already set in config (and valid), skip geocoding
    if LATITUDE and LONGITUDE:
        logging.debug("Manual LATITUDE/LONGITUDE provided. Skipping geocoding.")
        try:
            LATITUDE = float(LATITUDE)
            LONGITUDE = float(LONGITUDE)
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid manual LATITUDE or LONGITUDE. Error: {e}")
            return None

    # Otherwise, if no valid lat/long but an ADDRESS is specified, do geocoding
    elif ADDRESS and ADDRESS.strip():
        lat, lng = get_coordinates(ADDRESS)
        if lat is None or lng is None:
            logging.error("Failed to retrieve valid coordinates from ADDRESS.")
            return None
        # Convert to floats
        try:
            LATITUDE, LONGITUDE = float(lat), float(lng)
            logging.debug(f"Coordinates obtained from ADDRESS: {LATITUDE}, {LONGITUDE}")
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid geocoded LATITUDE/LONGITUDE. Error: {e}")
            return None
    else:
        # If neither manual lat/long nor valid ADDRESS is provided, fail
        logging.error("No valid ADDRESS or manual LATITUDE/LONGITUDE provided.")
        return None

    # Now, attempt city_state lookup
    city_state_str = get_city_state(LATITUDE, LONGITUDE) or ""

    # Save to cache
    save_location_cache(LATITUDE, LONGITUDE, city_state_str)
    return {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "city_state": city_state_str
    }

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
    if WEATHER in ["True", "true", True]:
        weather = get_forecast(
            LATITUDE, LONGITUDE, city_state_str, UNIT_SYSTEM, TIME_SYSTEM, timezone
        )
        logging.debug("Weather data obtained.")
        logging.debug(f"Weather data: {weather}")
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
    if QOTD and QOTD in ["True", "true", True]:
        quote = get_qotd()
        logging.debug("Quote of the day obtained.")
        return quote
    return ""

def get_word_of_the_day():
    if WOTD and WOTD in ["True", "true", True]:
        wotd = get_wotd()
        logging.debug("Word of the day obtained.")
        return wotd
    return ""

def get_puzzles_of_the_day():
    if PUZZLES and PUZZLES in ["True", "true", True]:
        puzzles, puzzles_ans = get_puzzles()
        if not PUZZLES_ANSWERS or PUZZLES_ANSWERS not in ["True", "true", True]:
            puzzles_ans = ""
        logging.debug("Puzzles obtained.")
        return puzzles, puzzles_ans
    return "", ""

def prepare_send_email():
    """Function to gather info and send an email."""
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
            OPENAI_API_KEY,
            ENABLE_SUMMARY,
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

    except Exception as e:
        error_message = str(e)
        traceback_str = traceback.format_exc()
        logging.critical(f"Error sending email: {error_message}")
        logging.critical(f"Traceback: {traceback_str}")

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
            scheduler.add_job(
                scheduled_email_job, 'cron', hour=6, minute=00, id='daily_email_job'
            )
            logging.info(f"Daily email job rescheduled at {HOUR}:{MINUTE} for the next day.")
            logging.warning("HOUR or MINUTE not properly configured, using 0600.")
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
    now = datetime.now(timezone).astimezone(timezone)
    next_schedule = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)

    if now > next_schedule:
        next_schedule += timedelta(days=1)

    logging.debug(f"Current time: {now}")
    logging.debug(f"Next scheduled time: {next_schedule}")

    return (next_schedule - now).seconds

# Configuration file paths
CONFIG_FILE_PATH = "./data/config.json"
CACHE_FILE_PATH = "./cache/location_cache.json"

app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

# Load .env variables and version
load_dotenv()

with open("./version.json", "r") as f:
    VERSION = json.load(f)["version"]

# Get the encryption key from environment variables
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError("Encryption key not found. Please set the ENCRYPTION_KEY environment variable.")

cipher_suite = Fernet(ENCRYPTION_KEY)

# Get the encryption key from environment variables
PASSWORD = os.getenv("PASSWORD")

if not PASSWORD:
    raise RuntimeError("Password not found. Please set the PASSWORD environment variable.")

hashed_password = generate_password_hash(PASSWORD)

# Initialize and save configuration from environment variables to JSON
initialize_config()

# Load configuration from JSON
CONFIG = load_config_from_json()

# Mandatory configuration checks
REQUIRED_CONFIG_KEYS = [
    "RECIPIENT_EMAIL",
    "RECIPIENT_NAME",
    "SENDER_EMAIL",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_HOST",
    "SMTP_PORT",
]

for key in REQUIRED_CONFIG_KEYS:
    assert CONFIG.get(key), f"{key} is not configured."

RECIPIENT_EMAIL = get_config_value("RECIPIENT_EMAIL")
RECIPIENT_NAME = get_config_value("RECIPIENT_NAME")
SENDER_EMAIL = get_config_value("SENDER_EMAIL")
SMTP_USERNAME = get_config_value("SMTP_USERNAME")
SMTP_PASSWORD = get_config_value("SMTP_PASSWORD")
SMTP_HOST = get_config_value("SMTP_HOST")
SMTP_PORT = get_config_value("SMTP_PORT")
OPENAI_API_KEY = get_config_value("OPENAI_API_KEY")
ENABLE_SUMMARY = get_config_value("ENABLE_SUMMARY", "False")
UNIT_SYSTEM = get_config_value("UNIT_SYSTEM", "METRIC")
TIME_SYSTEM = get_config_value("TIME_SYSTEM", "24HR")
LATITUDE = get_config_value("LATITUDE")
LONGITUDE = get_config_value("LONGITUDE")
ADDRESS = get_config_value("ADDRESS")
WEATHER = get_config_value("WEATHER", "False")
TODOIST_API_KEY = get_config_value("TODOIST_API_KEY")
VIKUNJA_API_KEY = get_config_value("VIKUNJA_API_KEY")
VIKUNJA_BASE_URL = get_config_value("VIKUNJA_BASE_URL")
WEBCAL_LINKS = get_config_value("WEBCAL_LINKS")
RSS_LINKS = get_config_value("RSS_LINKS", "False")
PUZZLES = get_config_value("PUZZLES", "False")
PUZZLES_ANSWERS = get_config_value("PUZZLES_ANSWERS", "False")
WOTD = get_config_value("WOTD", "False")
QOTD = get_config_value("QOTD", "False")
TIMEZONE = get_config_value("TIMEZONE", None)
HOUR = get_config_value("HOUR")
MINUTE = get_config_value("MINUTE")
LOGGING_LEVEL = get_config_value("LOGGING_LEVEL", "INFO").upper()

# Initialize logging
if LOGGING_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
logging.info(f"Logging level set to: {LOGGING_LEVEL}")

if not LATITUDE or not LONGITUDE:
    refresh_location_cache()

# Ensure timezone is correctly loaded and utilized
global timezone
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

executors = {
    'default': ThreadPoolExecutor(max_workers=5)
}

global scheduler
scheduler = BackgroundScheduler(executors=executors, timezone=timezone)

@app.route("/login", methods=["GET", "POST"])
def login():
    # Check if the user is already logged in
    if session.get("logged_in"):
        return redirect(url_for("home"))  # Redirect to the main page

    if request.method == "POST":
        password = request.form.get("password")
        if check_password_hash(hashed_password, password):
            session['logged_in'] = True
            return redirect(url_for("home"))  # Redirect to the main page after successful login
        else:
            return render_template("login.html", error="Invalid password")

    return render_template("login.html")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function

@app.route("/")
@login_required
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    current_config = load_config_from_json()
    return render_template('index.html', logged_in=session.get("logged_in"), app_version=VERSION, config=current_config)

@app.route("/api/config", methods=["GET"])
@login_required
def api_get_config():
    try:
        config = load_config_from_json()
        return jsonify(config)
    except Exception as e:
        logging.error(f"Error retrieving configuration: {e}")
        return jsonify({"error": "Failed to load configuration"}), 500

@app.route("/api/save-config", methods=["POST"])
@login_required
def api_save_config():
    try:
        data = request.json
        save_config_to_json(data)
        refresh_configuration_variables()
        return jsonify({"message": "Configuration saved successfully!"})
    except Exception as e:
        logging.error(f"Error saving configuration: {e}")
        return jsonify({"message": f"Failed to save configuration: {str(e)}"}), 500

@app.route('/api/send-email', methods=['POST'])
@login_required
def manually_send_email():
    try:
        prepare_send_email()
        return jsonify({"message": "Email sent successfully!"}), 200
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return jsonify({"message": f"Failed to send email: {str(e)}"}), 500

@app.route("/api/schedule-email", methods=["POST"])
@login_required
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
@login_required
def interrupt_schedule():
    try:
        scheduler.remove_job('daily_email_job')
        return jsonify({"message": "Email schedule interrupted!"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to interrupt schedule. {e}"}), 500


@app.route("/logout")
@login_required
def logout():
    session.clear()  # Clear all session data
    return redirect(url_for("login"))  # Redirect to the login page


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
        SECRET_KEY = os.getenv("SECRET_KEY")
        if not SECRET_KEY:
            raise RuntimeError("SECRET_KEY not found. Please set the SECRET_KEY environment variable.")
        app.secret_key = SECRET_KEY
        waitress.serve(app, host="0.0.0.0", port=8080)


    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    LATITUDE, LONGITUDE, city_state_str = load_location_cache()
    if not LATITUDE or not LONGITUDE or not city_state_str:
        refresh_location_cache()

    logging.info(f"Running version {VERSION}")

    config_data = load_config_from_json()

    if not HOUR:
        HOUR = 6
        config_data["HOUR"] = "6"
    else:
        HOUR = int(HOUR)
        config_data["HOUR"] = str(HOUR)

    if not MINUTE:
        MINUTE = 0
        config_data["MINUTE"] = "0"
    else:
        MINUTE = int(MINUTE)
        config_data["MINUTE"] = str(MINUTE)

    save_config_to_json(config_data)

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
