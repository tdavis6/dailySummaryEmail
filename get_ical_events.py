import requests
from icalendar import Calendar
import pytz
from datetime import datetime, date


def fetch_icalendar(url):
    if url.startswith("webcal://"):
        url = url.replace("webcal://", "https://", 1)
    response = requests.get(url)
    response.raise_for_status()
    return response.text


def parse_icalendar(ical_string):
    calendar = Calendar.from_ical(ical_string)
    events = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            start = component.get("dtstart")
            end = component.get("dtend")
            summary = component.get("summary")
            if start and end:  # Make sure both start and end datetime exist
                event = {
                    "start": start.dt,
                    "end": end.dt,
                    "summary": str(summary) if summary else "No Title",
                }
                events.append(event)
    return events


def make_aware(dt, timezone="UTC"):
    tz = pytz.timezone(timezone)
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            return tz.localize(dt)
        return dt
    elif isinstance(dt, date):
        # Handle date objects as midnight at the beginning of the day
        dt = datetime.combine(dt, datetime.min.time())
        return tz.localize(dt)
    raise ValueError("Unsupported date type")


def is_event_today(event_start, event_end, timezone="UTC"):
    tz = pytz.timezone(timezone)
    today = datetime.now(tz).date()
    event_start = make_aware(event_start, timezone).date()
    event_end = make_aware(event_end, timezone).date()

    return event_start <= today <= event_end


def is_all_day_event(event):
    start = event["start"]
    end = event["end"]
    # All-day events use dates without time components
    return (
            isinstance(start, date)
            and not isinstance(start, datetime)
            and isinstance(end, date)
            and not isinstance(end, datetime)
    )


def get_ics_events(url, timezone):
    ical_string = fetch_icalendar(url)
    events = parse_icalendar(ical_string)
    events = [
        event
        for event in events
        if is_event_today(event["start"], event["end"], timezone)
    ]
    return events
