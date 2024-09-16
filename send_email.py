import os
from dotenv import load_dotenv
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# Load SMTP related environment variables
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL")
RECIPIENT_NAME = os.getenv("RECIPIENT_NAME")
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = os.getenv("SMTP_PORT")


if not SMTP_PORT:
    SMTP_PORT = 465 # Defaults to SSL

def send_email(weather_data) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {RECIPIENT_NAME}"
        message["From"] = SMTP_USERNAME
        message["To"] = RECIPIENT_EMAIL

        text = f"""\
{weather_data['forecast']['properties']['periods'][0]['name']}'s Weather Forecast for {weather_data['city']}, {weather_data['state']}: \
{weather_data['forecast']['properties']['periods'][0]['detailedForecast']}

"""
        html = f"""\
        <html>
        <body>
        
        </body>
        </html>
"""
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(
                SENDER_EMAIL, RECIPIENT_EMAIL, message.as_string()
            )
    except Exception as e:
        print(f"Error occurred: {e}")
