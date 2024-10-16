from get_ical_events import get_ics_events

def get_cal_data(WEBCAL_LINKS, TIMEZONE):
    text = ""
    if WEBCAL_LINKS is not None:
        text += "\n\n# Events"
        for link in WEBCAL_LINKS.split(","):
            text += get_ics_events(url=link, timezone=TIMEZONE)
    return text
