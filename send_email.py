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
        puzzles_string,
        wotd_string,
        quote_string,
        puzzles_ans_string,
) -> None:
    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {recipient_name}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = ""

        if date_string is not None:
            text += date_string + "\n\n"

        if weather_string is not None:
            text += weather_string + "\n\n"

        if todo_string is not None:
            text += todo_string + "\n\n"

        if cal_string is not None:
            text += cal_string + "\n\n"

        if puzzles_string is not None:
            text += puzzles_string+ "\n\n"

        if wotd_string is not None:
            text += wotd_string + "\n\n"

        if quote_string is not None:
            text += quote_string + "\n\n"

        if puzzles_ans_string is not None:
            text += puzzles_ans_string + "\n\n"


        html = markdown.markdown(
            text,
            extensions=[
                "markdown.extensions.fenced_code",
            ],
        )

        part_1 = MIMEText(text, "plain")
        part_2 = MIMEText(html, "html")

        message.attach(part_1)
        message.attach(part_2)

        logging.info(text)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info("Email sent.")
    except Exception as e:
        logging.critical(f"Error occurred: {e}")