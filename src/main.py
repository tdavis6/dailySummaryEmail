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

    existing_config = load_config_from_json()
    config_data = {}

    for key in config_keys:
        env_val = os.getenv(key, None)
        if env_val is None:
            logging.debug(f"Environment variable '{key}' not found. Using config.json or blank.")
            config_data[key] = existing_config.get(key, "")
        else:
            config_data[key] = env_val

    save_config_to_json(config_data)


def encrypt_data(data):
    return cipher_suite.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data):
    if not encrypted_data:
        return ""
    return cipher_suite.decrypt(encrypted_data.encode()).decode()


def refresh_configuration_variables():
    global RECIPIENT_EMAIL, RECIPIENT_NAME, SENDER_EMAIL, SMTP_USERNAME, SMTP_PASSWORD
    global SMTP_HOST, SMTP_PORT, OPENAI_API_KEY, ENABLE_SUMMARY, UNIT_SYSTEM, TIME_SYSTEM
    global LATITUDE, LONGITUDE, ADDRESS, WEATHER, TODOIST_API_KEY, VIKUNJA_API_KEY
    global VIKUNJA_BASE_URL, WEBCAL_LINKS, RSS_LINKS, PUZZLES, PUZZLES_ANSWERS, WOTD, QOTD
    global TIMEZONE, HOUR, MINUTE, LOGGING_LEVEL, timezone, scheduler
    global city_state_str, country_code

    # Keep old values to detect changes
    logging_level_old = LOGGING_LEVEL
    latitude_old = float(LATITUDE) if LATITUDE not in [None, ""] else None
    longitude_old = float(LONGITUDE) if LONGITUDE not in [None, ""] else None
    address_old = str(ADDRESS).strip() if ADDRESS not in [None, ""] else ""
    hour_old, minute_old = HOUR, MINUTE

    config = load_config_from_json()

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

    new_lat = float(LATITUDE) if LATITUDE not in [None, ""] else None
    new_lng = float(LONGITUDE) if LONGITUDE not in [None, ""] else None
    new_address = str(ADDRESS).strip() if ADDRESS not in [None, ""] else ""

    location_changed = (
        new_lat != latitude_old
        or new_lng != longitude_old
        or new_address != address_old
    )

    if location_changed:
        logging.info("Location data changed. Refreshing location cache...")
        location_cache = refresh_location_cache()

        if location_cache:
            LATITUDE = location_cache["latitude"]
            LONGITUDE = location_cache["longitude"]
            country_code = location_cache["country_code"]
            city_state_str = location_cache["city_state"]
            if not ADDRESS or not ADDRESS.strip():
                ADDRESS = city_state_str
        else:
            logging.warning("Location cache refresh failed, reverting to old coordinates.")
            LATITUDE, LONGITUDE = latitude_old, longitude_old

        # Re-derive timezone when location changes
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

    if LOGGING_LEVEL != logging_level_old:
        change_logging_level()

    if HOUR and MINUTE and (str(hour_old) != str(HOUR) or str(minute_old) != str(MINUTE)):
        reschedule_email_job()

    logging.info("Configuration refreshed successfully.")


def load_location_cache():
    """Load cached location data. Returns a dict or None if cache is missing/invalid."""
    ensure_directories_and_files_exist()
    try:
        with open(CACHE_FILE_PATH, "r") as f:
            data = json.load(f)
            if data.get("LATITUDE") and data.get("LONGITUDE"):
                return {
                    "latitude": data["LATITUDE"],
                    "longitude": data["LONGITUDE"],
                    "country_code": data.get("country_code", "us"),
                    "city_state": data.get("city_state_str", ""),
                }
    except (json.JSONDecodeError, FileNotFoundError):
        logging.error("Error reading location cache.")
    return None


def save_location_cache(lat, lng, country_code, city_state):
    """Save location data to the cache file."""
    with open(CACHE_FILE_PATH, "w") as f:
        json.dump(
            {
                "LATITUDE": lat,
                "LONGITUDE": lng,
                "country_code": country_code,
                "city_state_str": city_state,
            },
            f,
        )
    logging.info("Location data saved to cache.")


def refresh_location_cache():
    """
    Refreshes location data. If valid LATITUDE and LONGITUDE are provided, use them
    directly and do a single reverse-geocode via get_coordinates to get country_code
    and city_state. If only ADDRESS is set, forward-geocode it via get_coordinates.
    Returns a dict with { 'latitude', 'longitude', 'country_code', 'city_state' }
    or None on failure.
    """
    ensure_directories_and_files_exist()
    global LATITUDE, LONGITUDE, country_code, city_state_str

    if LATITUDE and LONGITUDE:
        # Manual coords provided — still call get_coordinates for reverse-geocode metadata
        logging.debug("Manual LATITUDE/LONGITUDE provided. Reverse-geocoding for metadata.")
        try:
            lat = float(LATITUDE)
            lng = float(LONGITUDE)
        except (ValueError, TypeError) as e:
            logging.error(f"Invalid manual LATITUDE or LONGITUDE: {e}")
            return None

        # Pass coords as a "lat,lng" string so get_coordinates can reverse-geocode
        resolved_lat, resolved_lng, resolved_country, resolved_city_state = get_coordinates(
            f"{lat},{lng}", VERSION
        )
        if resolved_lat is None:
            logging.warning(
                "Reverse-geocode for metadata failed; proceeding with coords only."
            )
            resolved_lat, resolved_lng = lat, lng
            resolved_country = "us"
            resolved_city_state = ""

    elif ADDRESS and ADDRESS.strip():
        logging.debug(f"Geocoding ADDRESS: {ADDRESS}")
        resolved_lat, resolved_lng, resolved_country, resolved_city_state = get_coordinates(
            ADDRESS, VERSION
        )
        if resolved_lat is None or resolved_lng is None:
            logging.error("Failed to retrieve valid coordinates from ADDRESS.")
            return None
    else:
        logging.error("No valid ADDRESS or manual LATITUDE/LONGITUDE provided.")
        return None

    LATITUDE = resolved_lat
    LONGITUDE = resolved_lng
    country_code = resolved_country
    city_state_str = resolved_city_state

    save_location_cache(LATITUDE, LONGITUDE, country_code, city_state_str)
    return {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "country_code": country_code,
        "city_state": city_state_str,
    }


def change_logging_level():
    if LOGGING_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")
    logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
    logging.getLogger().setLevel(getattr(logging, LOGGING_LEVEL))
    app.logger.removeHandler(default_handler)
    app.logger.addHandler(logging.StreamHandler())
    app.logger.setLevel(getattr(logging, LOGGING_LEVEL))
    logging.info(f"Logging level changed to: {LOGGING_LEVEL}")


def get_weather():
    if WEATHER in ["True", "true", True]:
        weather = get_forecast(
            LATITUDE, LONGITUDE, country_code, city_state_str, UNIT_SYSTEM, TIME_SYSTEM, timezone
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
    """Gather all content and send the daily summary email."""
    try:
        logging.debug("prepare_send_email called.")

        date_string = get_current_date_in_timezone(timezone)
        logging.debug("Date string obtained.")

        weather_string = get_weather() or ""
        logging.debug("Weather string obtained.")

        todo_string = get_todo() or ""
        logging.debug("Todo string obtained.")

        calendar_events = get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM)
        logging.debug("Calendar events obtained.")

        rss_string = get_rss_feed() or ""
        logging.debug("RSS string obtained.")

        wotd_string = get_word_of_the_day() or ""
        logging.debug("Word of the Day string obtained.")

        quote_string = get_quote_of_the_day() or ""
        logging.debug("Quote of the Day string obtained.")

        puzzles_string, puzzles_ans_string = get_puzzles_of_the_day() or ("", "")
        logging.debug("Puzzles strings obtained.")

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
        logging.critical(f"Error sending email: {e}")
        logging.critical(traceback.format_exc())


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
                scheduled_email_job, "cron", hour=int(HOUR), minute=int(MINUTE), id="daily_email_job"
            )
            logging.info(f"Daily email job rescheduled at {HOUR}:{MINUTE}.")
        else:
            scheduler.add_job(
                scheduled_email_job, "cron", hour=6, minute=0, id="daily_email_job"
            )
            logging.warning("HOUR or MINUTE not properly configured, using 06:00.")
    except Exception as e:
        logging.error(f"Failed to reschedule daily email job: {e}")


def format_wait_time(seconds):
    """Convert seconds into a human-readable hours/minutes/seconds string."""
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"


def get_seconds_until_next_schedule(hour, minute, timezone):
    """Calculate the seconds until the next scheduled time."""
    if isinstance(timezone, str):
        timezone = pytz.timezone(timezone)
    now = datetime.now(timezone).astimezone(timezone)
    next_schedule = now.replace(hour=int(hour), minute=int(minute), second=0, microsecond=0)
    if now >= next_schedule:
        next_schedule += timedelta(days=1)
    logging.debug(f"Current time: {now}, Next scheduled time: {next_schedule}")
    return (next_schedule - now).seconds


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

CONFIG_FILE_PATH = "./data/config.json"
CACHE_FILE_PATH = "./cache/location_cache.json"

app = Flask(__name__, template_folder="../templates", static_folder="../static")
CORS(app)

load_dotenv()

with open("./version.json", "r") as f:
    VERSION = json.load(f)["version"]

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    raise RuntimeError("Encryption key not found. Please set the ENCRYPTION_KEY environment variable.")
cipher_suite = Fernet(ENCRYPTION_KEY)

PASSWORD = os.getenv("PASSWORD")
if not PASSWORD:
    raise RuntimeError("Password not found. Please set the PASSWORD environment variable.")
hashed_password = generate_password_hash(PASSWORD)

initialize_config()

CONFIG = load_config_from_json()

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

# Initialize globals that get_weather() depends on so they always exist
country_code = "us"
city_state_str = ""

if LOGGING_LEVEL not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    raise ValueError(f"Invalid logging level: {LOGGING_LEVEL}")
logging.basicConfig(level=getattr(logging, LOGGING_LEVEL), force=True)
logging.info(f"Logging level set to: {LOGGING_LEVEL}")

# Ensure timezone is correctly loaded
try:
    if not TIMEZONE:
        timezone_str = get_timezone(LATITUDE, LONGITUDE)
        timezone = pytz.timezone(timezone_str)
    else:
        timezone = pytz.timezone(TIMEZONE)
    logging.info(f"Timezone found: {timezone}.")
except Exception as e:
    logging.critical(f"Error creating timezone: {e}")
    sys.exit(1)

executors = {"default": ThreadPoolExecutor(max_workers=5)}
scheduler = BackgroundScheduler(executors=executors, timezone=timezone)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("logged_in"):
        return redirect(url_for("home"))
    if request.method == "POST":
        password = request.form.get("password")
        if check_password_hash(hashed_password, password):
            session["logged_in"] = True
            return redirect(url_for("home"))
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
    current_config = load_config_from_json()
    return render_template(
        "index.html", logged_in=session.get("logged_in"), app_version=VERSION, config=current_config
    )


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


@app.route("/api/send-email", methods=["POST"])
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
            scheduler.remove_job("daily_email_job")
        scheduler.add_job(
            scheduled_email_job,
            "cron",
            hour=int(hour),
            minute=int(minute),
            id="daily_email_job",
            timezone=timezone,
        )
        return jsonify({"message": "Email schedule set!"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to schedule email: {e}"}), 500


@app.route("/api/interrupt-schedule", methods=["POST"])
@login_required
def interrupt_schedule():
    try:
        scheduler.remove_job("daily_email_job")
        return jsonify({"message": "Email schedule interrupted!"}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to interrupt schedule: {e}"}), 500


@app.route("/logout")
@login_required
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    shutdown_event = threading.Event()
    _waitress_server = None

    def handle_shutdown_signal(signum, frame):
        sig_name = signal.Signals(signum).name
        logging.info(f"Received {sig_name}. Initiating graceful shutdown...")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, handle_shutdown_signal)
    signal.signal(signal.SIGINT, handle_shutdown_signal)

    scheduler.start()
    logging.info("Scheduler started.")

    def run_flask():
        global _waitress_server
        SECRET_KEY = os.getenv("SECRET_KEY")
        if not SECRET_KEY:
            raise RuntimeError("SECRET_KEY not found. Please set the SECRET_KEY environment variable.")
        app.secret_key = SECRET_KEY
        from waitress.server import create_server
        _waitress_server = create_server(app, host="0.0.0.0", port=8080)
        logging.info("Waitress server started on port 8080.")
        _waitress_server.run()

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Populate location globals on startup (single Nominatim call)
    location_cache = refresh_location_cache()
    if location_cache:
        LATITUDE = location_cache["latitude"]
        LONGITUDE = location_cache["longitude"]
        country_code = location_cache["country_code"]
        city_state_str = location_cache["city_state"]
    else:
        logging.warning("Could not refresh location cache on startup.")

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

    if scheduler.get_job("daily_email_job"):
        scheduler.remove_job("daily_email_job")

    scheduler.add_job(
        scheduled_email_job, "cron", hour=HOUR, minute=MINUTE, id="daily_email_job"
    )
    logging.info(f"Daily email job scheduled at {HOUR}:{MINUTE}.")

    shutdown_event.wait()

    logging.info("Shutting down scheduler...")
    scheduler.shutdown(wait=False)
    logging.info("Scheduler shut down.")

    if _waitress_server is not None:
        logging.info("Closing Waitress server...")
        _waitress_server.close()

    flask_thread.join(timeout=5)
    if flask_thread.is_alive():
        logging.warning("Flask thread did not exit cleanly within timeout.")

    logging.info("Shutdown complete. Goodbye.")
    sys.exit(0)