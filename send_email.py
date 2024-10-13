import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import re
import markdown
import pytz
import logging


def send_email(
        recipient_email,
        recipient_name,
        sender_email,
        smtp_username,
        smtp_password,
        smtp_host,
        smtp_port,
        weather_data,
        todoist_data,
        cal_data,
        timezone,
        TIMEZONE
) -> None:
    iso_pattern_with_hm = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?$"
    )
    iso_pattern_with_hmZ = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?Z$"
    )

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {recipient_name}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = f"""\
# Weather
{weather_data['forecast']['properties']['periods'][0]['name']}'s Weather Forecast for {weather_data['city']}, {weather_data['state']}: \
{weather_data['forecast']['properties']['periods'][0]['detailedForecast']}"""

        if todoist_data is not None:
            text = text + "\n\n# Tasks"
            for task in todoist_data:
                text = text + f"\n\n - [{task.content}]({task.url})"
                if task.due.timezone is not None:
                    text = text + f", due {datetime.datetime.fromisoformat(task.due.datetime).astimezone(tz=pytz.timezone(TIMEZONE)).strftime("at %H:%M")}" if task.due.datetime is not None else text + ""
                else:
                    text = text + f", due {datetime.datetime.fromisoformat(task.due.datetime).strftime("at %H:%M")}" if task.due.datetime is not None else text + ""
                text = text + f", priority {(5-task.priority)}" if task.priority != 1 else text + ""
        else:
            None

        if cal_data is not None:
            text = text + "\n\n# Events"
            text = text + cal_data
        else:
            None

        html = markdown.markdown(text)

        part_1 = MIMEText(text, "plain")
        part_2 = MIMEText(html, "html")

        message.attach(part_1)
        message.attach(part_2)

        logging.info(text)
        print(text)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(
                sender_email, recipient_email, message.as_string()
            )
        logging.info("Email sent.")
        print("Email sent.")
    except Exception as e:
        logging.critical(f"Error occurred: {e}")
