# get_cal_data.py

from datetime import datetime, date
from get_ical_events import get_ics_events, make_aware, is_all_day_event


def get_cal_data(WEBCAL_LINKS, TIMEZONE):
    events = []

    if WEBCAL_LINKS:
        for link in WEBCAL_LINKS.split(","):
            ics_events = get_ics_events(url=link, timezone=TIMEZONE)
            events.extend(ics_events)

        # Sort events based on the start datetime
        events.sort(key=lambda event: make_aware(event["start"], TIMEZONE))

    text = "\n\n# Events" if events else ""
    for event in events:
        text += f"\n\n### {event.get('summary')}"
        description = event.get("description")
        if description:
            text += f"\n\n{description}"

        if is_all_day_event(event):
            text += "\n\n(All day event)"
        else:
            if event["start"]:
                start = make_aware(event["start"], TIMEZONE)
                if start.date() == date.today():
                    text += f"\n\nStarts at {start.strftime('%H:%M')}"
                else:
                    text += f"\n\nStarts at {start.strftime('%H:%M on %A, %B %d, %Y')}"
            if event["end"]:
                end = make_aware(event["end"], TIMEZONE)
                if end.date() == date.today():
                    text += f"\n\nEnds at {end.strftime('%H:%M')}"
                else:
                    text += f"\n\nEnds at {end.strftime('%H:%M on %A, %B %d, %Y')}"

    return text
