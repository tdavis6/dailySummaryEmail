import logging
from datetime import datetime, date, timedelta

import pytz
import requests
from dateutil.rrule import rrulestr
from icalendar import Calendar
from icalendar.prop import vRecur

# Configuration for retries
MAX_RETRIES = 3
TIMEOUT = 5  # seconds
# Recurring events are only expanded this far past today; only today's events are ever used.
EXPANSION_LOOKAHEAD_DAYS = 3


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


def _as_date(value):
    return value.date() if isinstance(value, datetime) else value


def _normalize_until(rrule, start):
    """Return the RRULE as a string whose UNTIL is compatible with DTSTART.

    dateutil requires UNTIL to be UTC when DTSTART is timezone-aware and naive when
    DTSTART is naive/a date. Calendars in the wild often violate this.
    """
    rule = dict(rrule)
    until_values = rule.get("UNTIL")
    if until_values:
        start_is_aware = isinstance(start, datetime) and start.tzinfo is not None
        fixed = []
        for until in until_values:
            if start_is_aware:
                if not isinstance(until, datetime):
                    until = datetime.combine(until, datetime.max.time().replace(microsecond=0))
                if until.tzinfo is None:
                    until = start.tzinfo.localize(until) if hasattr(start.tzinfo, "localize") else until.replace(tzinfo=start.tzinfo)
                until = until.astimezone(pytz.utc)
            else:
                if isinstance(until, datetime):
                    if until.tzinfo is not None:
                        until = until.astimezone(pytz.utc).replace(tzinfo=None)
                else:
                    until = datetime.combine(until, datetime.max.time().replace(microsecond=0))
            fixed.append(until)
        rule["UNTIL"] = fixed
    return vRecur(rule).to_ical().decode()


def _collect_exdates(component):
    exdates = component.get("exdate", [])
    if not isinstance(exdates, list):
        exdates = [exdates]
    result = []
    for ex in exdates:
        result.extend(d.dt for d in ex.dts)
    return result


def _is_excluded(occurrence, exdates):
    """True if `occurrence` matches an EXDATE (which may be a date or a datetime)."""
    for ex in exdates:
        if isinstance(ex, datetime) and isinstance(occurrence, datetime):
            try:
                if ex == occurrence:
                    return True
            except TypeError:
                # naive vs aware: fall through to a wall-clock comparison
                if ex.replace(tzinfo=None) == occurrence.replace(tzinfo=None):
                    return True
        elif _as_date(ex) == _as_date(occurrence):
            return True
    return False


def _expand_recurrence(component, start, duration):
    """Yield (start, end) for each occurrence of a recurring VEVENT, up to the lookahead cutoff."""
    rule = rrulestr(_normalize_until(component.get("rrule"), start), dtstart=start)
    exdates = _collect_exdates(component)
    cutoff = date.today() + timedelta(days=EXPANSION_LOOKAHEAD_DAYS)

    for dt in rule:
        if _as_date(dt) > cutoff:
            break  # occurrences are ascending, so nothing later can matter
        if _is_excluded(dt, exdates):
            continue
        yield dt, dt + duration


def parse_icalendar(ical_string):
    if not ical_string:
        return []

    calendar = Calendar.from_ical(ical_string)
    events = []
    exceptions = {}

    for component in calendar.walk():
        if component.name != "VEVENT":
            continue

        start = component.get("dtstart")
        if not start:
            continue
        summary = component.get("summary")
        location = component.get("location")
        uid = component.get("uid")
        recurrence_id = component.get("recurrence-id")

        if recurrence_id:
            logging.debug("Processing recurring exception")
            exceptions[(uid, recurrence_id.dt)] = component
            continue

        description = component.get("description")
        start = start.dt

        end = component.get("dtend")
        if end:
            end = end.dt
        elif component.get("duration"):
            end = start + component.get("duration").dt
        else:
            # RFC 5545: a date-only event lasts one day; a timed event with no end is instantaneous
            end = start + timedelta(days=1) if not isinstance(start, datetime) else start
        event_duration = end - start

        base = {
            "summary": str(summary) if summary else "No Title",
            "location": location,
            "uid": uid,
            "description": str(description) if description else None,
        }

        if component.get("rrule"):
            try:
                for occ_start, occ_end in _expand_recurrence(component, start, event_duration):
                    events.append({**base, "start": occ_start, "end": occ_end})
            except Exception as e:
                logging.warning(f"Skipping recurring event '{base['summary']}' (uid={uid}): {e}")
        else:
            events.append({**base, "start": start, "end": end})

    # Apply modified instances of recurring events
    for (uid, ex_start), ex_component in exceptions.items():
        for event in events:
            if event["uid"] == uid and event["start"] == ex_start:
                new_start = ex_component.get("dtstart").dt
                new_end = ex_component.get("dtend")
                new_end = new_end.dt if new_end else new_start + (event["end"] - event["start"])
                event["start"] = new_start
                event["end"] = new_end
                if ex_component.get("summary"):
                    event["summary"] = str(ex_component.get("summary"))
                if ex_component.get("location"):
                    event["location"] = ex_component.get("location")
                if ex_component.get("description"):
                    event["description"] = str(ex_component.get("description"))

    return events

def make_aware(dt, timezone):
    try:
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return timezone.localize(dt)
            return dt
        elif isinstance(dt, date):
            dt = datetime.combine(dt, datetime.min.time())
            return timezone.localize(dt)
    except Exception as e:
        logging.critical(f"Error in make_aware: {e}")
        raise
    raise ValueError("Unsupported date type")


def is_event_today(event_start, event_end, timezone):
    try:
        today = datetime.now(timezone).date()
        event_start = make_aware(event_start, timezone)
        event_end = make_aware(event_end, timezone)

        # Handle exclusive end time on all-day events that ends exactly at 00:00
        if event_end.time() == datetime.min.time() and event_end.date() != event_start.date():
            event_end -= timedelta(seconds=1)

        return event_start.date() <= today <= event_end.date()
    except Exception as e:
        logging.critical(f"Error in is_event_today: {e}")
        raise


def convert_all_day_event(event, timezone):
    try:
        if isinstance(event["start"], date) and not isinstance(event["start"], datetime):
            event["start"] = make_aware(datetime.combine(event["start"], datetime.min.time()), timezone)
        if isinstance(event["end"], date) and not isinstance(event["end"], datetime):
            event["end"] = make_aware(datetime.combine(event["end"], datetime.min.time()), timezone)
    except Exception as e:
        logging.critical(f"Error in convert_all_day_event: {e}")
        raise
    return event


def get_ics_events(url, timezone):
    ical_string = fetch_icalendar(url)
    converted = []
    for event in parse_icalendar(ical_string):
        try:
            converted.append(convert_all_day_event(event, timezone))
        except Exception as e:
            logging.warning(f"Skipping event due to conversion error: {e}")

    result = []
    for event in converted:
        try:
            if is_event_today(event["start"], event["end"], timezone):
                result.append(event)
        except Exception as e:
            logging.warning(f"Skipping event due to date filter error: {e}")

    short_url = url[:60] + "..." if len(url) > 60 else url
    logging.info(f"iCal {short_url}: {len(converted)} total events, {len(result)} today")
    return result