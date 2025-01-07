import logging
from datetime import datetime, date

import requests
from icalendar import Calendar

# Configuration for retries and logging
MAX_RETRIES = 3
TIMEOUT = 5  # seconds
MAX_FUTURE_YEARS = 5

logging.basicConfig(level=logging.DEBUG)  # Set to DEBUG for detailed log


def fetch_icalendar(url):
    for attempt in range(MAX_RETRIES):
        try:
            if url.startswith("webcal://"):
                url = url.replace("webcal://", "https://", 1)
            logging.debug(f"Fetching iCalendar from: {url}")
            response = requests.get(url, timeout=TIMEOUT)
            response.raise_for_status()
            logging.debug("Fetched iCalendar data successfully")
            return response.text
        except requests.exceptions.RequestException as e:
            logging.critical(f"Attempt {attempt + 1}: Error occurred: {e}")
            if attempt < MAX_RETRIES - 1:
                continue  # Retry
            else:
                logging.critical("Max retries reached. Failing.")
                return None


def parse_icalendar(ical_string):
    if not ical_string:
        return []

    calendar = Calendar.from_ical(ical_string)
    events = []
    exceptions = {}

    for component in calendar.walk():
        if component.name == "VEVENT":
            start = component.get("dtstart")
            end = component.get("dtend")
            summary = component.get("summary")
            location = component.get("location")
            uid = component.get("uid")
            recurrence_id = component.get("recurrence-id")
            description = component.get("description")
            rrule = component.get("rrule")

            # Detect if it's an exception (modified occurrence) of a recurring event
            if recurrence_id:
                ex_start = recurrence_id.dt
                exceptions[(uid, ex_start)] = component
                continue

            if start and end:
                start_dt = start.dt
                end_dt = end.dt

                # ---- Detect if all-day (date only in ICS) ----
                # If the ICS parameter "VALUE=DATE" is present, it's an all-day event
                # (i.e., dtstart is a date, not a datetime).
                is_all_day = (
                        "VALUE" in start.params
                        and start.params["VALUE"] == "DATE"
                )

                # Build your base event dict
                base_event = {
                    "start": start_dt,
                    "end": end_dt,
                    "summary": str(summary) if summary else "No Title",
                    "location": location,
                    "uid": uid,
                    "description": str(description) if description else None,
                    "is_all_day": is_all_day,  # <--- store the flag here
                }

                # Check for RRULE-based recurring events
                if rrule:
                    # ... existing recurring logic ...
                    pass
                else:
                    events.append(base_event)

    # Process exceptions (this part left mostly unchanged)
    for (uid, ex_start), ex_component in exceptions.items():
        for event in events:
            if event["uid"] == uid and event["start"] == ex_start:
                event["start"] = ex_component.get("dtstart").dt
                event["end"] = ex_component.get("dtend").dt
                event["summary"] = (
                    str(ex_component.get("summary"))
                    if ex_component.get("summary")
                    else "No Title"
                )
                # Also detect if the exception is all-day
                if "VALUE" in ex_component.get("dtstart").params and ex_component.get("dtstart").params[
                    "VALUE"] == "DATE":
                    event["is_all_day"] = True
                else:
                    event["is_all_day"] = False

                location = ex_component.get("location")
                if location:
                    apple_maps_link = f"https://maps.apple.com/?q={location}"
                    event["apple_maps_link"] = apple_maps_link

    return events

def make_aware(dt, timezone):
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return timezone.localize(dt)
        return dt
    elif isinstance(dt, date):
        dt = datetime.combine(dt, datetime.min.time())
        return timezone.localize(dt)
    raise ValueError("Unsupported date type")


def is_event_today(event_start, event_end, timezone):
    today = datetime.now(timezone).date()

    # Convert event start and end times to the provided local timezone
    event_start = make_aware(event_start, timezone)
    event_end = make_aware(event_end, timezone)

    # Ensure comparisons are based on the local date in the provided timezone
    event_start_local_date = event_start.astimezone(timezone).date()
    event_end_local_date = event_end.astimezone(timezone).date()

    # Exclude events that end exactly at 00:00 today in local time and started on a previous day
    if (
            event_end_local_date == today
            and event_end.time() == datetime.min.time()
            and event_start_local_date < today
    ):
        return False

    # Check if today falls within the event's local start and end date range
    return event_start_local_date <= today <= event_end_local_date



def is_all_day_event(event):
    start = event["start"]
    end = event["end"]
    return (
            isinstance(start, date)
            and not isinstance(start, datetime)
            and isinstance(end, date)
            and not isinstance(end, datetime)
    )


def get_ics_events(url, timezone):
    try:
        ical_string = fetch_icalendar(url)
        events = parse_icalendar(ical_string)
        events = [
            event
            for event in events
            if is_event_today(event["start"], event["end"], timezone)
        ]
        return events
    except Exception as e:
        logging.critical(f"Failed to get events: {e}")
        return []