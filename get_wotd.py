import logging
import feedparser
from bs4 import BeautifulSoup

# URL of the Merriam-Webster Word of the Day RSS feed
rss_feed_url = "https://www.merriam-webster.com/wotd/feed/rss2"


def get_word_of_the_day():
    # Parse the RSS feed
    feed = feedparser.parse(rss_feed_url)

    # Get the first entry from the feed
    entry = feed.entries[0]

    # The title of the entry contains the word of the day
    word_of_the_day = entry.title

    # Extract the definition from the summary field
    summary = entry.summary
    soup = BeautifulSoup(summary, "html.parser")

    # Extract paragraphs and identify the one that contains the definition
    paragraphs = soup.find_all("p")
    definition = None
    for para in paragraphs:
        text = para.get_text()
        if text.startswith("To"):
            definition = text
            break

    if not definition:
        definition = "Definition not found in expected format."

    return word_of_the_day, definition

def get_wotd():
    word, definition = get_word_of_the_day()
    wotd_string = ""
    wotd_string += "\n\n# Word of the Day"
    wotd_string += f"\n**{word}**"
    wotd_string += f"\n\n{definition}"
    logging.info(wotd_string)
    return wotd_string