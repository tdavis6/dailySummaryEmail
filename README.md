# Daily Summary Email
A simple program that emails the user the weather and any tasks on their to-do list at 6 AM daily
(Only Todoist is currently supported, 
but I am working on more. Feel free to request any todo app with an issue)

Unfortunately, the weather component only works in the United States because the used API is from the NWS,
a US government agency.

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
- WEATHER_API_KEY: Your NWS weather API key. Currently, this is your email address as a string. (optional, required for
  weather compatibility)
- LATITUDE: The latitude you wish to use for the weather. (optional, required for weather compatibility)
- LONGITUDE: The longitude you wish to use for the weather. (optional, required for weather compatibility)
- TODOIST_API_KEY: Your Todoist API key (optional, required for Todoist compatibility)
- WEBCAL_LINKS: Link(s) for webcal or ics calendars of which the events should appear in the email.
  Use one string, seperated by commas. Do not use "" or '' around the entire string. (Optional, required for calendar
  compatibility)
- TIMEZONE: The timezone that the user lives in. This will be used for the times in the emails. 
Refer to [pytz package documentation](https://pypi.org/project/pytz/) for timezones. (required)
- HOUR: The hour to send the email. (Defaults to the time when the container started.) (optional)
- MINUTE: The minute to send the email. (Defaults to the time when the container started.) (Optional)
