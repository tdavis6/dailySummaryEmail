import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import markdown


def send_email(
        recipient_email,
        recipient_name,
        sender_email,
        smtp_username,
        smtp_password,
        smtp_host,
        smtp_port,
        date_string,
        weather_string,
        todo_string,
        cal_string,
        wotd_string,
        quote_string
) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {recipient_name}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = f""""""

        if date_string is not None:
            text += date_string

        if weather_string is not None:
            text += weather_string

        if todo_string is not None:
            text += todo_string

        if cal_string is not None:
            text += cal_string

        if wotd_string is not None:
            text += wotd_string

        if quote_string is not None:
            text += quote_string

        html = markdown.markdown(text)

        part_1 = MIMEText(text, "plain")
        part_2 = MIMEText(html, "html")

        message.attach(part_1)
        message.attach(part_2)

        logging.info(text)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(
                sender_email, recipient_email, message.as_string()
            )
        logging.info("Email sent.")
    except Exception as e:
        logging.critical(f"Error occurred: {e}")
