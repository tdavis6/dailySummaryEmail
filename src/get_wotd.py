import logging

import feedparser
import requests
from bs4 import BeautifulSoup

# URL of the Merriam-Webster Word of the Day RSS feed
rss_feed_url = "https://www.merriam-webster.com/wotd/feed/rss2"


def get_word_of_the_day():
    # Parse the RSS feed
    # Fetch with requests so there is a timeout (feedparser.parse(url) has none)
    response = requests.get(rss_feed_url, timeout=10)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    logging.debug(f"Feed parsed. Feed: {feed}")

    # Get the first entry from the feed
    if not feed.entries:
        raise RuntimeError("Word of the Day feed returned no entries.")
    entry = feed.entries[0]
    logging.debug(f"First entry: {entry}")

    # The title of the entry contains the word of the day
    word_of_the_day = entry.title
    logging.debug(f"Word of the Day: {word_of_the_day}")

    # Extract the definition from the summary field
    summary = entry.summary
    logging.debug(f"Summary: {summary}")

    soup = BeautifulSoup(summary, "html.parser")

    # Extract paragraphs
    paragraphs = soup.find_all("p")
    logging.debug(f"Paragraphs found: {paragraphs}")

    # Get the second paragraph, if it exists
    second_paragraph = None
    if len(paragraphs) > 1:
        second_paragraph = paragraphs[1].get_text()

        # Filter out "See the entry >"
        second_paragraph = second_paragraph.replace("See the entry >", "").strip()

        # Add additional newlines after the first and second lines
        lines = second_paragraph.split("\n")
        if len(lines) > 2:
            second_paragraph = (
                    lines[0] + "\n\n" + lines[1] + "\n\n" + "\n".join(lines[2:])
            )
        elif len(lines) > 1:
            second_paragraph = lines[0] + "\n\n" + lines[1]

    if not second_paragraph:
        second_paragraph = "Second paragraph not found."

    return second_paragraph


def get_wotd():
    second_paragraph = get_word_of_the_day()
    wotd_string = ""
    wotd_string += "\n\n# Word of the Day"
    wotd_string += f"\n\n{second_paragraph}"
    logging.debug(wotd_string)
    return wotd_string