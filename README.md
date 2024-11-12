# Daily Summary Email
![GitHub last commit](https://img.shields.io/github/last-commit/tdavis6/dailySummaryEmail)
![GitHub branch check runs](https://img.shields.io/github/check-runs/tdavis6/dailySummaryEmail/main)

## Summary
A simple program that emails the user the weather and any tasks on their to-do list at a designated time daily
(Only Todoist is currently supported, 
but I am working on more. Feel free to request any todo app with an issue)

To change the time of day that the email is sent, use the MINUTE and HOUR environment variables. 
All times should be in 24hr (0-23 for hours, 0-59 for minutes) time.

When the program starts up, an email will be sent so the user may see what it will look like. The next email will be 
sent at the specified time.

## Environment Variables
See .env.example for an example .env file.
- RECIPIENT_EMAIL: The recipient's email (required)
- RECIPIENT_NAME: The name that the email is addressed to (required)
- SENDER_EMAIL: The sending email (required)
- SMTP_USERNAME: The username of the sending account on the SMTP server (required)
- SMTP_PASSWORD: The password of the sending account on the SMTP server (required)
- SMTP_HOST: The host of the SMTP server (e.g. smtp.gmail.com) (required)
- SMTP_PORT: The port of the SMTP server (defaults to 465 for SSL) (optional)
- UNIT_SYSTEM: METRIC or IMPERIAL. (optional, defaults to metric)
- TIME_SYSTEM: 24HR or 12HR. (optional, defaults to 24HR)
- LATITUDE: The latitude you wish to use for the weather and timezone. (optional)
- LONGITUDE: The longitude you wish to use for the weather and timezone. (optional)
- ADDRESS: The address of which the weather and timezone should be used. (optional, required if latitude and longitude
  are not given. Use quotes.)
- WEATHER: True or False. Enables weather. (optional, defaults to false)
- TODOIST_API_KEY: Your Todoist API key (optional)
- WEBCAL_LINKS: Link(s) for webcal or ics calendars of which the events should appear in the email. Use one string, seperated by commas. Do not use quotes. (optional)
- RSS_LINKS: Link(s) for rss feeds of which the entries should appear in the email. Use one string, seperated by commas. Do not use quotes. (optional)
- PUZZLES: True or False. Enables puzzles. (optional, defaults to false)
- WOTD: True or False. Enables the Word of the Day. (optional, defaults to false)
- QOTD: True or False. Enables the Quote of the Day. (optional, defaults to false)
- HOUR: The hour to send the email. (optional, defaults to the time when the container started)
- MINUTE: The minute to send the email. (optional, defaults to the time when the container started)
- TIMEZONE: Timezone as a string. (Optional, not required if a latitude and longitude or an address are given, but will override that timezone. Ensure that it is spelt correctly.)
- LOGGING_LEVEL: Level for logging (optional, defaults to INFO). Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.

NOTE: You MUST provide either a coordinate pair or an address.

## Attribution
- Geocoding provided by [Nominatim](https://nominatim.org/).
- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Quotes provided by [ZenQuotes API](https://zenquotes.io/).

## Other Notes
- Versioning follows [semver](https://semver.org).