from datetime import datetime, date
from get_ical_events import get_ics_events, make_aware, is_all_day_event


def get_cal_data(WEBCAL_LINKS, timezone, TIME_SYSTEM):
    events = []

    if WEBCAL_LINKS:
        for link in WEBCAL_LINKS.split(","):
            ics_events = get_ics_events(url=link, timezone=timezone)
            events.extend(ics_events)

        # Sort events based on the start datetime
        events.sort(key=lambda event: make_aware(event["start"], timezone))

    text = "\n\n# Events" if events else ""
    for event in events:
        text += f"\n\n### {event.get('summary')}"
        description = event.get("description")
        if description:
            text += f"\n\n{description}"

        if is_all_day_event(event):
            text += "\n\n(All day event)"
        else:
            time_format = "%I:%M %p" if TIME_SYSTEM.upper() == "12HR" else "%H:%M"
            date_time_format = (
                "%I:%M %p on %A, %B %d, %Y"
                if TIME_SYSTEM == "12hr"
                else "%H:%M on %A, %B %d, %Y"
            )

            if event["start"]:
                start = make_aware(event["start"], timezone)
                if start.date() == date.today():
                    text += f"\n\nStarts at {start.strftime(time_format)}"
                else:
                    text += f"\n\nStarts at {start.strftime(date_time_format)}"
            if event["end"]:
                end = make_aware(event["end"], timezone)
                if end.date() == date.today():
                    text += f"\n\nEnds at {end.strftime(time_format)}"
                else:
                    text += f"\n\nEnds at {end.strftime(date_time_format)}"

    return text