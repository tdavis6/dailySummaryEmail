import requests
from icalendar import Calendar
from datetime import datetime, date
from dateutil.rrule import rrulestr
import logging

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

            if recurrence_id:  # This is an exception to a recurrent event
                ex_start = recurrence_id.dt
                exceptions[(uid, ex_start)] = component
                continue

            if start and end:
                description = component.get("description")
                rrule = component.get("rrule")
                start = start.dt
                end = end.dt
                event_duration = end - start

                if rrule:
                    rule = rrulestr(rrule.to_ical().decode(), dtstart=start)
                    exdates = component.get("exdate", [])
                    exdate_list = []

                    if exdates:
                        if not isinstance(exdates, list):
                            exdates = [exdates]

                        for ex in exdates:
                            exdate_list.extend(d.dt for d in ex.dts)

                    for dt in rule:
                        if dt.year >= datetime.now().year + MAX_FUTURE_YEARS:
                            break  # Skip dates that are too far in the future

                        if dt in exdate_list:
                            continue  # Skip dates specified in EXDATE

                        try:
                            event = {
                                "start": dt,
                                "end": dt + event_duration,
                                "summary": str(summary) if summary else "No Title",
                                "location": location,
                                "uid": uid,
                                "description": str(description) if description else None,
                                "description": str(description) if description else None,
                            }
                            events.append(event)
                        except Exception as e:
                            logging.critical(f"Error creating event: {e}")
                else:
                    event = {
                        "start": start,
                        "end": end,
                        "summary": str(summary) if summary else "No Title",
                        "location": location,
                        "uid": uid,
                        "description": str(description) if description else None,
                    }
                    events.append(event)

    # Process exceptions to recurring events
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
            if location:
                apple_maps_link = f"https://maps.apple.com/?q={location}"
                event["apple_maps_link"] = apple_maps_link

    return events
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
    event_start = make_aware(event_start, timezone)
    event_end = make_aware(event_end, timezone)

    # Exclude events that end exactly at 00:00 today and started on a previous day
    if event_end.date() == today and event_end.time() == datetime.min.time() and event_start.date() < today:
        return False

    # Check if today falls within the event start and end datetime range
    return event_start.date() <= today <= event_end.date()


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