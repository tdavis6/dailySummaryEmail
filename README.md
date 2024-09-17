# Daily Summary Email
A simple program that emails the user the weather and any tasks on their to-do list at 6 AM daily
(Only Todoist is currently supported, 
but I am working on more. Feel free to request any todo app with an issue)

Unfortunately, the weather component only works in the United States because the used API is from the NWS,
a US government agency.

To change the time of day that the email is sent, edit the cron job definition in the Dockerfile.

If you want to run this manually, run ``python main.py`` in the container console.

## Environment Variables
- WEATHER_API_KEY: Your NWS weather API key. Currently, this is your email address as a string. (required)
- LATITUDE: The latitude you wish to use for the weather. (required)
- LONGITUDE: The longitude you wish to use for the weather. (required)
- TODOIST_API_KEY: Your Todoist API key (required)
- RECIPIENT_EMAIL: The recipient's email (required)
- RECIPIENT_NAME: The name that the email is addressed to (required)
- SENDER_EMAIL: The sending email (required)
- SMTP_USERNAME: The username of the sending account on the SMTP server (required)
- SMTP_PASSWORD: The password of the sending account on the SMTP server (required)
- SMTP_HOST: The host of the SMTP server (e.g. smtp.gmail.com) (required)
- SMTP_PORT: The port of the SMTP server (defaults to 465 for SSL) (optional)
