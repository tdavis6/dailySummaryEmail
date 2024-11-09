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
                    background-color: #f0f8ff;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 90%;
                    max-width: 800px;
                    margin: 30px auto;
                    background: #ffffff;
                    padding: 25px;
                    border-radius: 15px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                }}
                h1 {{
                    color: #333;
                    font-size: 24px;
                    border-bottom: 2px solid #eee;
                    padding-bottom: 10px;
                }}
                p {{
                    color: #666;
                    font-size: 16px;
                }}
                a {{
                    color: #0066cc;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
                }}
                @media only screen and (max-width: 600px) {{
                    .container {{
                        width: 100%;
                        padding: 15px;
                    }}
                    h1 {{
                        font-size: 20px;
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