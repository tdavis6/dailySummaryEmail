# Daily Summary Email
![GitHub last commit](https://img.shields.io/github/last-commit/tdavis6/dailySummaryEmail)
![GitHub branch check runs](https://img.shields.io/github/check-runs/tdavis6/dailySummaryEmail/main)

## Summary
A program that emails the user the weather, any tasks on their to-do list, their events, puzzles, a word of the day, a
quote of the day, and more at a designated time daily.
(Only Todoist and Vikunja are currently supported, but I am working on more.
Feel free to request any todo app with an issue.)

To change the time of day that the email is sent, use the MINUTE and HOUR environment variables. 
All times should be in 24hr (0-23 for hours, 0-59 for minutes) time.

When the program starts up, an email will be sent so the user may see what it will look like. The next email will be 
sent at the specified time.

## Setup

Run this in Docker, using the provided `docker-compose.yml`. Use the `.env.example` as a guideline for the `.env` file,
however
all these options are not necessary to put in the `.env` file, they can be added later in the web UI. The only necessary
variables to set are the `ENCRYPTION_KEY` and `PASSWORD`. The set `PASSWORD` is used to log into the web UI.

## Environment Variables
See .env.example for an example .env file.

- RECIPIENT_EMAIL: The recipient's email
- RECIPIENT_NAME: The name that the email is addressed to
- SENDER_EMAIL: The sending email
- SMTP_USERNAME: The username of the sending account on the SMTP server
- SMTP_PASSWORD: The password of the sending account on the SMTP server
- SMTP_HOST: The host of the SMTP server (e.g. smtp.gmail.com)
- SMTP_PORT: The port of the SMTP server (defaults to 465 for SSL)
- OPENAI_API_KEY: Your OpenAI API key. Used to generate a short summary of the email.
- UNIT_SYSTEM: METRIC or IMPERIAL. (defaults to metric)
- TIME_SYSTEM: 24HR or 12HR. (defaults to 24HR)
- LATITUDE: The latitude you wish to use for the weather and timezone.
- LONGITUDE: The longitude you wish to use for the weather and timezone.
- ADDRESS: The address of which the weather and timezone should be used. (Use quotes)
- WEATHER: True or False. Enables weather. (defaults to false)
- TODOIST_API_KEY: Your Todoist API key
- VIKUNJA_API_KEY: Your Vikunja API key
  VIKUNJA_BASE_URL: Your Vikunja base url
- WEBCAL_LINKS: Link(s) for webcal or ics calendars of which the events should appear in the email. Use one string,
  seperated by commas. Do not use quotes.
- RSS_LINKS: Link(s) for rss feeds of which the entries should appear in the email. Use one string, seperated by commas.
  Do not use quotes.
- PUZZLES: True or False. Enables puzzles. (defaults to false)
- WOTD: True or False. Enables the Word of the Day. (defaults to false)
- QOTD: True or False. Enables the Quote of the Day. (defaults to false)
- HOUR: The hour to send the email. (defaults to the time when the container started)
- MINUTE: The minute to send the email. (defaults to the time when the container started)
- TIMEZONE: Timezone as a string. (not required if a latitude and longitude or an address are given, but will override
  that timezone. Ensure that it is spelt correctly.)
- LOGGING_LEVEL: Level for logging (defaults to INFO). Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
- ENCRYPTION_KEY: Fernet encryption key for passwords and API keys. You can use [this](https://fernetkeygen.com/)
  website to generate them.
- PASSWORD: Web UI password. Must be alphanumerical.
- SECRET_KEY: Random alphanumerical string. Used for session cookies of the Web UI.

NOTE: You MUST provide either a coordinate pair or an address.

## OpenAI Integration
The OpenAI Integration allows a 2-3 sentence summary of the email near the top. 

Under the current API pricing (last updated 11/13/24), this integration costs about \$0.104025 USD per year of operation,
with very long emails (1250+170 input tokens per day, a maximum of 120 tokens of output per day). The output is limited at 120 
tokens per day. The model used is GPT-4o mini, which allows for it to cost much less than a larger model. The current pricing 
is $0.150 / 1M input tokens and \$0.600 / 1M output tokens.

### Cost Breakdown
$\text{Total Input Tokens per Year: } 1,420 \text{ tokens/day} \times 365 \text{ days} = 518,300 \text{ tokens}$

$\text{Total Output Tokens per Year: } 120 \text{ tokens/day} \times 365 \text{ days} = 43,800 \text{ tokens}$

$\text{Total Input Cost} = \frac{518,300}{1,000,000}\times0.150 = 0.077745 \text{ USD per year}$

$\text{Total Output Cost} = \frac{43,800}{1,000,000}\times0.600 = 0.02628 \text{ USD per year}$

$0.077745+0.02628=0.104025 \text{ USD per year}$

### Setup Instructions
To set this up, make an account with OpenAI, or log in with one, and get your API key. Note: The OpenAI API is a different
product that ChatGPT, ChatGPT Plus does not grant access to the OpenAI API.

## Attribution
- Geocoding provided by [Nominatim](https://nominatim.org/).
- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Quotes provided by [ZenQuotes API](https://zenquotes.io/).

## Other Notes
- Versioning follows [semver](https://semver.org).
- If you want news articles, add their RSS feed as a feed. For example, the Wall Street Journal supplies RSS feeds, and 
other newspapers likely do too ([WSJ World News Feed](https://feeds.content.dowjones.io/public/rss/RSSWorldNews)).
  - I do not claim responsibility for any content in this feed. I do not support any particular news paper, nor wish to make any
political comments on any work. This feed was choosen because it was shown to be [close to the center of the political spectrum](https://www.allsides.com/news-source/wall-street-journal-media-bias).

## Buy me a cup of coffee ☕️!
If you find this program to be valuable, and have all your personal financials taken care of, 
consider buying me a coffee me through [GitHub Sponsors](https://github.com/sponsors/tdavis6)!
