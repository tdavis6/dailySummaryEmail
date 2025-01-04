from datetime import datetime, date, timedelta

from get_ical_events import get_ics_events


def ensure_datetime(dt):
    """
    If 'dt' is date-only, convert it to a naive datetime at 00:00.
    If it's already a datetime, return as-is.
    """
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return datetime.combine(dt, datetime.min.time())
    return dt

def localize_or_convert(dt, timezone):
    """
    If dt is naive, localize it to 'timezone'.
    If dt is already offset-aware, convert to 'timezone'.
    """
    if dt.tzinfo is None:
        # dt is naive; localize (attach the timezone)
        return timezone.localize(dt)
    else:
        # dt is aware; convert to the desired timezone
        return dt.astimezone(timezone)


def handle_all_day_event(event):
    """
    Adjust the event's end date by subtracting one day,
    because ICS all-day events use exclusive end.
    """
    start_date = event["start"].date()
    end_date = event["end"].date()

    # Subtract one day from the end date to handle ICS exclusivity
    corrected_end_date = end_date - timedelta(days=1)

    # If after subtracting one day we have the same date,
    # then it's truly just a single all-day event on start_date
    if corrected_end_date == start_date:
        return "\n\nAll day event"
    else:
        # Multi-day
        return (
            f"\n\nAll day event, ends {corrected_end_date.strftime('%A, %B %d, %Y')}"
        )

def get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM):
    events = []

    if WEBCAL_LINKS:
        for link in WEBCAL_LINKS.split(","):
            ics_events = get_ics_events(url=link, timezone=timezone)
            events.extend(ics_events)

        # Unify all event start/end to aware datetimes in the same timezone
        for event in events:
            event["start"] = ensure_datetime(event["start"])
            event["end"] = ensure_datetime(event["end"])

            event["start"] = localize_or_convert(event["start"], timezone)
            event["end"] = localize_or_convert(event["end"], timezone)

        # Now safe to sort by start time (all are offset-aware)
        events.sort(key=lambda e: e["start"])

    # Prepare the final text
    text = "\n\n# Events" if events else ""
    today = datetime.now(timezone).date()

    for event in events:
        summary = event.get('summary', 'No Title')
        text += f"\n\n### {summary}"

        description = event.get("description")
        if description:
            text += f"\n\n{description}"

        is_all_day = event.get("is_all_day", False)

        if is_all_day:
            # Handle all-day event logic (exclusive end date)
            text += handle_all_day_event(event)
        else:
            # Time-based events
            start_dt = event["start"]
            end_dt = event["end"]

            time_format = "%I:%M %p" if TIME_SYSTEM.upper() == "12HR" else "%H:%M"
            date_time_format = (
                "%I:%M %p on %A, %B %d, %Y"
                if TIME_SYSTEM.lower() == "12hr"
                else "%H:%M on %A, %B %d, %Y"
            )

            if start_dt.date() == today:
                text += f"\n\nStarts at {start_dt.strftime(time_format)}"
            else:
                text += f"\n\nStarts at {start_dt.strftime(date_time_format)}"

            if end_dt.date() == today:
                text += f"\n\nEnds at {end_dt.strftime(time_format)}"
            else:
                text += f"\n\nEnds at {end_dt.strftime(date_time_format)}"

        # Append location if available
        location = event.get("location")
        if location:
            maps_link = f"https://maps.apple.com/?q={location.replace(' ', '+')}"
            text += f"\n\n[Directions]({maps_link})"

    return text
