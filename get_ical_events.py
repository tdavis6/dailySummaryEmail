import requests
from icalendar import Calendar
from datetime import datetime, date
import pytz
import logging

def fetch_icalendar(url: str) -> str:
    if url.startswith("webcal://"):
        url = url.replace("webcal://", "https://", 1)

    response = requests.get(url)
    response.raise_for_status()

    return response.text

def parse_icalendar(ical_data: str) -> Calendar:
    calendar = Calendar.from_ical(ical_data)
    return calendar

def convert_to_local_timezone(event_time, timezone):
    if isinstance(event_time, datetime) and event_time.tzinfo is not None:
        local_timezone = pytz.timezone(timezone)
        event_time = event_time.astimezone(local_timezone)
    return event_time

def is_event_today(event, timezone) -> bool:
    event_start = event.get("dtstart").dt
    event_end = event.get("dtend").dt if event.get("dtend") else event_start

    event_start = convert_to_local_timezone(event_start, timezone)
    event_end = convert_to_local_timezone(event_end, timezone)

    if isinstance(event_start, datetime):
        event_date = event_start.date()
    else:
        event_date = event_start

    return event_date == date.today()

def get_ics_events(url: str, timezone: str):
    text = ""
    try:
        ical_data = fetch_icalendar(url)
        calendar = parse_icalendar(ical_data)

        # Collect today's events
        today_events = []

        for component in calendar.walk():
            if component.name == "VEVENT" and is_event_today(component, timezone):
                event_start = component.get("dtstart").dt
                event_end = component.get("dtend").dt if component.get("dtend") else None

                event_start = convert_to_local_timezone(event_start, timezone)
                event_end = convert_to_local_timezone(event_end, timezone)

                today_events.append((component, event_start, event_end))

        # Sort events by their start time
        today_events.sort(key=lambda x: x[1])

        # Process and display sorted events
        for event, start, end in today_events:
            text += f"\n\n### {event.get('summary')}"
            description = event.get('description')
            if description:
                text += f"\n\n{description}"
            text += f"\n\nStarts at {start.strftime('%H:%M') if isinstance(start, datetime) else str(start)}"
            if end:
                text += f"\n\nEnds at {end.strftime('%H:%M') if end and isinstance(end, datetime) else str(end)}"

    except Exception as e:
        logging.critical(f"An error occurred: {e}")

    return text
