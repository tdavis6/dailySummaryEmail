from datetime import datetime
import pytz


def get_current_date_in_timezone(timezone) -> str:
    """Returns the current date in the given timezone as a string."""
    try:
        # Get the current datetime in UTC and convert it to the local timezone
        local_datetime = datetime.now(timezone)

        # Extract the date part
        local_date = local_datetime.date()

        return str(f"# {local_date.strftime("%A, %B %d, %Y")}")
    except pytz.UnknownTimeZoneError:
        return f"Unknown timezone: {timezone}"
