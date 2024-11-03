# Daily Summary Email
## Summary
A simple program that emails the user the weather and any tasks on their to-do list at a designated time daily
(Only Todoist is currently supported, 
but I am working on more. Feel free to request any todo app with an issue)

To change the time of day that the email is sent, use the MINUTE and HOUR environment variables. 
All times should be in 24hr (0-23 for hours, 0-59 for minutes) time.

## Environment Variables
- RECIPIENT_EMAIL: The recipient's email (required)
- RECIPIENT_NAME: The name that the email is addressed to (required)
- SENDER_EMAIL: The sending email (required)
- SMTP_USERNAME: The username of the sending account on the SMTP server (required)
- SMTP_PASSWORD: The password of the sending account on the SMTP server (required)
- SMTP_HOST: The host of the SMTP server (e.g. smtp.gmail.com) (required)
- SMTP_PORT: The port of the SMTP server (defaults to 465 for SSL) (optional)
- WEATHER_API_KEY: Your WeatherAPI.com weather API key. (free) (optional, required for
  weather compatibility)
- UNIT_SYSTEM: METRIC or IMPERIAL. (optional, defaults to metric)
- TIME_SYSTEM: 24HR or 12HR. (optional, defaults to 24HR)
- WOTD: True or False. Enables the Word of the Day. (optional, required for WOTD) (defaults to false)
- QOTD: True or False. Enables the Quote of the Day. (optional, required for QOTD) (defaults to false)
- LATITUDE: The latitude you wish to use for the weather and timezone. (optional)
- LONGITUDE: The longitude you wish to use for the weather and timezone. (optional)
- ADDRESS: The address of which the weather and timezone should be used. (optional, required if latitude and longitude
  are not given. Use quotes.)
- TODOIST_API_KEY: Your Todoist API key (optional, required for Todoist compatibility)
- WEBCAL_LINKS: Link(s) for webcal or ics calendars of which the events should appear in the email.
  Use one string, seperated by commas. Do not quotes. (Optional, required for calendar
  compatibility)
- HOUR: The hour to send the email. (Defaults to the time when the container started.) (optional)
- MINUTE: The minute to send the email. (Defaults to the time when the container started.) (Optional)
- LOGGING_LEVEL: Level for logging (defaults to INFO). Options: INFO, CRITICAL, DEBUG, WARNING.

NOTE: You MUST provide either a coordinate pair or an address.

## Weather API Key Setup
- Register for an account at [WeatherAPI.com](https://www.weatherapi.com/), using the free plan.
- Paste API key into the WEATHER_API_KEY environment variable. Do not use quotes.

## Attribution

Inspirational quotes provided by <a href="https://zenquotes.io/" target="_blank">ZenQuotes API</a>