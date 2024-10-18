import logging
from datetime import datetime, date

import pytz
import requests
from icalendar import Calendar


def fetch_icalendar(url: str) -> str:
    if url.startswith("webcal://"):
        url = url.replace("webcal://", "https://", 1)

    response = requests.get(url)
    response.raise_for_status()

    return response.text


def parse_icalendar(ical_data: str) -> Calendar:
    calendar = Calendar.from_ical(ical_data)
    return calendar


def make_aware(event_time, timezone):
    """Converts given datetime/date to an aware datetime in the specified timezone."""
    local_timezone = pytz.timezone(timezone)

    if isinstance(event_time, datetime):
        if event_time.tzinfo is None:
            event_time = local_timezone.localize(event_time)
        else:
            event_time = event_time.astimezone(local_timezone)
    elif isinstance(event_time, date):
        event_time = local_timezone.localize(
            datetime.combine(event_time, datetime.min.time())
        )

    return event_time


def is_event_today(event, timezone) -> bool:
    """Checks if the event occurs today."""
    event_start = event.get("dtstart").dt
    event_end = event.get("dtend") and event.get("dtend").dt or event_start

    event_start = make_aware(event_start, timezone)
    event_end = make_aware(event_end, timezone)

    # Use only the date part for comparison
    event_start_date = event_start.date()
    event_end_date = event_end.date()

    today = date.today()
    return event_start_date <= today <= event_end_date


def is_all_day_event(event) -> bool:
    """Determines if the event is an all-day event."""
    return isinstance(event.get("dtstart").dt, date) and not isinstance(
        event.get("dtstart").dt, datetime
    )


def get_ics_events(url: str, timezone: str):
    """Fetches and processes ICS events."""
    text = ""
    try:
        ical_data = fetch_icalendar(url)
        calendar = parse_icalendar(ical_data)

        # Collect today's events
        today_events = []

        for component in calendar.walk():
            if component.name == "VEVENT":
                # Check the status of the event and ensure it is not cancelled or declined
                event_status = component.get("STATUS")
                if event_status and event_status.upper() in ["CANCELLED", "DECLINED"]:
                    continue

                if is_event_today(component, timezone):
                    event_start = component.get("dtstart").dt
                    event_end = (
                            component.get("dtend") and component.get("dtend").dt or None
                    )

                    event_start = make_aware(event_start, timezone)
                    event_end = make_aware(event_end, timezone) if event_end else None

                    today_events.append((component, event_start, event_end))

        # Sort events by their start time relative to the Unix epoch
        today_events.sort(key=lambda x: x[1].timestamp())

        # Process and display sorted events
        for event, start, end in today_events:
            text += f"\n\n### {event.get('summary')}"
            description = event.get("description")
            if description:
                text += f"\n\n*{description}*"

            if is_all_day_event(event):
                text += "\n\n(All day event)"
            else:
                if start:
                    if start.date() == date.today():
                        text += f"\n\nStarts at {start.strftime('%H:%M')}"
                    else:
                        text += f"\n\nStarts at {start.strftime('%H:%M on %A, %B %d, %Y')}"
                if end:
                    if end.date() == date.today():
                        text += f"\n\nEnds at {end.strftime('%H:%M')}"
                    else:
                        text += f"\n\nEnds at {end.strftime('%H:%M on %A, %B %d, %Y')}"

    except Exception as e:
        logging.critical(f"An error occurred: {e}")

    return text
