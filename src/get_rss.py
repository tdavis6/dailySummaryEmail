import feedparser
import logging
from datetime import datetime, timedelta, timezone


def parse_recent_feed(feed_url):
    # Parse the feed (RSS/Atom)
    feed = feedparser.parse(feed_url)
    if "entries" not in feed:
        return []

    # Get the current time in UTC
    now = datetime.now(timezone.utc)

    # Define the time 24 hours ago
    time_24_hours_ago = now - timedelta(hours=24)

    # Filter and collect entries published in the last 24 hours
    recent_entries = []
    for entry in feed.entries:
        if "published_parsed" in entry:
            published_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        elif "updated_parsed" in entry:
            published_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        else:
            continue

        if published_time > time_24_hours_ago:
            entry_info = {
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", "No Link"),
                "published": published_time,
            }
            recent_entries.append(entry_info)

    return recent_entries


def get_rss(url_string):
    url_list = [url.strip() for url in url_string.split(",")]
    all_entries = []
    for url in url_list:
        entries = parse_recent_feed(url)
        all_entries.extend(entries)

    # Sort all entries by published date
    all_entries.sort(key=lambda x: x["published"], reverse=True)

    # Format the output
    now = datetime.now(timezone.utc)
    time_24_hours_ago = now - timedelta(hours=24)
    logging.debug(f"Current time (UTC): {now.isoformat()}")
    logging.debug(f"Filtering entries published after: {time_24_hours_ago.isoformat()}")
    output = []
    if all_entries:
        output.append("# Feed Entries\n\n")
        for entry in all_entries:
            output.append(f"\n\n### {entry['title']}")
            output.append(f"\n\nLink: {entry['link']}")
            output.append(f"\n\nPublished: {entry['published'].isoformat()}")
        return "\n".join(output)
    else:
        return ""
