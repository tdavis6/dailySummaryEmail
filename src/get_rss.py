import logging
from datetime import datetime, timedelta, timezone

import feedparser
import requests


def parse_recent_feed(feed_url):
    logging.debug(f"Fetching feed from URL: {feed_url}")
    try:
        response = requests.get(feed_url, timeout=10)
        response.raise_for_status()
        feed = feedparser.parse(response.content)
    except requests.RequestException as e:
        logging.error(f"Error fetching feed from {feed_url}: {e}")
        return []

    if not feed or not hasattr(feed, "entries") or not feed.entries:
        logging.warning(f"The feed from {feed_url} is empty or invalid.")
        return []

    # Get the current time in UTC
    now = datetime.now(timezone.utc)

    # Define the time 24 hours ago
    time_24_hours_ago = now - timedelta(hours=24)

    # Filter and collect entries published in the last 24 hours
    recent_entries = []
    for entry in feed.entries:
        published_time = None

        # Check if 'published_parsed' or 'updated_parsed' exists and is valid
        if entry.get("published_parsed"):
            published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif entry.get("updated_parsed"):
            published_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

        # If no valid date is present, skip the entry
        if not published_time:
            logging.warning(
                f"Skipping entry with no valid publication date: {entry.get('title', 'No Title')}"
            )
            continue

        # Add entries published in the last 24 hours
        if published_time > time_24_hours_ago:
            entry_info = {
                "title": entry.get("title", "No Title"),
                "description": entry.get("description", "No Description"),
                "link": entry.get("link", "No Link"),
                "published": published_time,
            }
            recent_entries.append(entry_info)

    return recent_entries

def get_rss(url_string, tz, TIME_SYSTEM):
    if not url_string:
        logging.error("The provided URL string is null or empty.")
        return ""

    url_list = [url.strip() for url in url_string.split(",")]
    all_entries = []
    for url in url_list:
        logging.debug(f"Processing URL: {url}")
        entries = parse_recent_feed(url)
        all_entries.extend(entries)

    # Sort all entries by published date
    all_entries.sort(key=lambda x: x["published"], reverse=True)

    logging.debug("Sorting and formatting the output")
    now = datetime.now(timezone.utc)
    time_24_hours_ago = now - timedelta(hours=24)
    logging.debug(f"Current time (UTC): {now.isoformat()}")
    logging.debug(f"Filtering entries published after: {time_24_hours_ago.isoformat()}")
    output = []
    date_time_format = (
        "%I:%M %p on %A, %B %d, %Y" if TIME_SYSTEM == "12HR" else "%H:%M on %A, %B %d, %Y"
    )

    if all_entries:
        output.append("# Feed Entries\n\n")
        for entry in all_entries:
            logging.debug(f"Formatting entry: {entry['title']}")
            published_str = entry["published"].astimezone(tz).strftime(date_time_format)
            output.append(f"\n\n### {entry['title']}")
            if entry.get("description"):
                output.append(f"\n\n{entry['description']}")
            output.append(f"\n\nLink: {entry['link']}")
            output.append(f"\n\nPublished: {published_str}")
        return "\n".join(output)
    else:
        return ""