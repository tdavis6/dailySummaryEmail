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
        weather_string,
        todo_data,
        cal_data,
        quote_string,
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

        text = f""""""

        if weather_string is not None:
            text += weather_string

        if todo_data is not None:
            text += todo_data

        if cal_data is not None:
            text += cal_data

        if quote_string is not None:
            text += quote_string


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
