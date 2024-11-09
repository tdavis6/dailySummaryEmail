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
        rss_string,
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

        if rss_string is not None:
            text += rss_string + "\n\n"

        if puzzles_string is not None:
            text += puzzles_string + "\n\n"

        if wotd_string is not None:
            text += wotd_string + "\n\n"

        if quote_string is not None:
            text += quote_string + "\n\n"

        if puzzles_ans_string is not None:
            text += puzzles_ans_string + "\n\n"

        html_content = markdown.markdown(
            text,
            extensions=[
                "markdown.extensions.fenced_code",
            ],
        )

        html = f"""
        <html>
        <head>
            <style>
                body {{
                    background-color: #f4f7fc;
                    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.8;
                    margin: 0;
                    padding: 0;
                    color: #000;
                }}
                .container {{
                    width: 90%;
                    max-width: 750px;
                    margin: 40px auto;
                    background: #ffffff;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #000;
                    font-size: 26px;
                    margin-bottom: 20px;
                    border-bottom: 3px solid #e1e8f0;
                    padding-bottom: 10px;
                    text-align: left;
                }}
                p {{
                    color: #000;
                    font-size: 16px;
                    margin: 15px 0;
                    text-align: left;
                }}
                a {{
                    color: #1a73e8;
                    text-decoration: none;
                    font-weight: 500;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                .button {{
                    display: inline-block;
                    background: #1a73e8;
                    color: #fff;
                    padding: 12px 20px;
                    margin: 20px 0;
                    border-radius: 6px;
                    text-align: center;
                    font-weight: bold;
                    text-decoration: none;
                }}
                @media only screen and (max-width: 600px) {{
                    .container {{
                        width: 100%;
                        padding: 20px;
                    }}
                    h1 {{
                        font-size: 22px;
                    }}
                    p {{
                        font-size: 14px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                {html_content}
            </div>
        </body>
        </html>
        """

        part_1 = MIMEText(text, "plain")
        part_2 = MIMEText(html, "html")

        message.attach(part_1)
        message.attach(part_2)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info("Email sent.")
    except Exception as e:
        logging.critical(f"Error occurred: {e}")

