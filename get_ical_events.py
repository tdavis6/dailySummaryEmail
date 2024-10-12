import requests
from icalendar import Calendar
from datetime import datetime, date, timedelta
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

def is_event_today(event, timezone) -> bool:
    event_start = event.get("dtstart").dt
    event_end = event.get("dtend").dt if event.get("dtend") else event_start

    # Normalize to local timezone if datetime objects
    if isinstance(event_start, datetime) and event_start.tzinfo is not None:
        local_timezone = pytz.timezone(timezone)  # Replace with your timezone
        event_start = event_start.astimezone(local_timezone)
        event_end = event_end.astimezone(local_timezone)

    if isinstance(event_start, datetime):
        event_date = event_start.date()
    else:
        event_date = event_start

    return event_date == date.today()

def get_ics_events(url: str, timezone:str):
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
                today_events.append((component, event_start, event_end))

        # Sort events by their start time
        today_events.sort(key=lambda x: x[1])

        # Process and display sorted events
        for event, start, end in today_events:
            event_start_str = start.strftime('%H:%M') if isinstance(start, datetime) else str(start)
            event_end_str = end.strftime('%H:%M') if end and isinstance(end, datetime) else str(end)

            text = text + f"\n\n### {event.get('summary')}"
            text = text + f"\n\nStarts at {event_start_str}"
            if end:
                text = text + f"\n\nEnds at {event_end_str}"
            print("")

    except Exception as e:
        print(f"An error occurred: {e}")
        logging.critical(f"An error occurred: {e}")

    return text
