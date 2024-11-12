from datetime import datetime, date
from get_ical_events import get_ics_events, make_aware, is_all_day_event

def ensure_datetime(dt):
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime.combine(dt, datetime.min.time())
    return dt

def get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM):
    events = []

    if WEBCAL_LINKS:
        for link in WEBCAL_LINKS.split(","):
            ics_events = get_ics_events(url=link, timezone=timezone)
            events.extend(ics_events)

        # Ensure all 'start' and 'end' times are timezone-aware datetime objects
        for event in events:
            event["start"] = make_aware(ensure_datetime(event["start"]), timezone)
            event["end"] = make_aware(ensure_datetime(event["end"]), timezone)

        # Sort events based on the start datetime
        events.sort(key=lambda event: event["start"])

    today = datetime.now(timezone).date()
    text = "\n\n# Events" if events else ""
    for event in events:
        text += f"\n\n### {event.get('summary')}"
        description = event.get("description")
        if description:
            text += f"\n\n{description}"

        # Check if the event is an all-day event based on `is_all_day` or `00:00` time check
        is_all_day = event.get("is_all_day") or (
                event["start"].time() == datetime.min.time() and event["end"].time() == datetime.min.time()
        )

        if is_all_day:
            text += "\n\nAll day event"
        else:
            time_format = "%I:%M %p" if TIME_SYSTEM.upper() == "12HR" else "%H:%M"
            date_time_format = (
                "%I:%M %p on %A, %B %d, %Y"
                if TIME_SYSTEM == "12hr"
                else "%H:%M on %A, %B %d, %Y"
            )

            # Only append the date if it's different from today
            if event["start"].date() == today:
                text += f"\n\nStarts at {event['start'].strftime(time_format)}"
            else:
                text += f"\n\nStarts at {event['start'].strftime(date_time_format)}"

            if event["end"].date() == today:
                text += f"\n\nEnds at {event['end'].strftime(time_format)}"
            else:
                text += f"\n\nEnds at {event['end'].strftime(date_time_format)}"

    return text
