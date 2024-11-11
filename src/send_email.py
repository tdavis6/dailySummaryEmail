import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import markdown
from datetime import datetime
import pytz

def send_email(
        version,
        timezone,
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
        # Ensure that timezone is a valid pytz timezone object
        if isinstance(timezone, str):
            timezone = pytz.timezone(timezone)
            logging.debug(f"Converted timezone string to pytz timezone object: {timezone}")

        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary for {recipient_name}: {date_string}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = ""  # Initialize the plain text content
        html_text = ""  # Initialize the HTML content

        # Convert and append sections
        def convert_and_append(markdown_string, section_class, text_format=True, is_date=False):
            nonlocal text, html_text
            if markdown_string:
                html_converted = markdown.markdown(markdown_string, extensions=["markdown.extensions.fenced_code"])
                if text_format:
                    text += markdown_string + "\n\n"
                if not is_date:
                    html_text += f"<div class='section {section_class}'>{html_converted}</div>"
            else:
                logging.warning(f"{section_class} content is None or empty.")

        if date_string:
            text += "# " + date_string + "\n\n"
        else:
            logging.warning("date_string is None or empty.")
            text += "# Date Not Available\n\n"

        convert_and_append(weather_string, "weather", text_format=True)
        convert_and_append(todo_string, "todo", text_format=True)
        convert_and_append(cal_string, "calendar", text_format=True)
        convert_and_append(rss_string, "rss", text_format=True)
        convert_and_append(puzzles_string, "puzzles", text_format=True)
        convert_and_append(wotd_string, "wotd", text_format=True)
        convert_and_append(quote_string, "quote", text_format=True)
        convert_and_append(puzzles_ans_string, "puzzles-ans", text_format=True)

        html_content = markdown.markdown(
            html_text,
            extensions=["markdown.extensions.fenced_code"]
        )

        current_datetime = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
        logging.debug(f"Current datetime: {current_datetime}")

        html = f"""
        <html>
        <head>
            <style>
                @keyframes slideUp {{
                    from {{
                        transform: translateY(50%);
                        opacity: 0;
                    }}
                    to {{
                        transform: translateY(0);
                        opacity: 1;
                    }}
                }}

                body {{
                    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                    font-family: 'Georgia', 'Times', serif;
                    color: #003366;
                    margin: 0;
                    padding: 0;
                }}

                .container {{
                    background: #ffffff;
                    color: #003366;
                    box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.2);
                    max-width: 750px;
                    margin: 40px auto;
                    padding: 30px;
                    animation: slideUp 0.6s ease-out;
                    border-radius: 12px;
                }}

                .section {{
                    background-color: #f7f7f7;
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    margin-top: 20px;
                    margin-bottom: 20px;
                }}

                .section h2 {{
                    font-size: 30px;
                    font-weight: 600;
                    color: #003366;
                }}

                .section p, .section pre {{
                    font-size: 18px;
                    color: #000;
                }}

                .header {{
                    background: linear-gradient(135deg, #1e88e5, #42a5f5);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: 600;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                    animation: slideUp 1s ease-out;
                    border-radius: 12px;
                }}

                .header .date {{
                    font-size: 18px;
                    font-weight: 300;
                    color: #e3f2fd;
                }}

                @media (max-width: 768px) {{
                    .container {{
                        border-radius: 0;
                    }}
                }}

                @media (prefers-color-scheme: dark) {{
                    body {{
                        background: linear-gradient(135deg, #2a3c57, #1e2a3f);
                        color: #e0e0e0;
                    }}

                    .container {{
                        background: #1b263b;
                        color: #e0e0e0;
                        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.5);
                    }}

                    .header {{
                        background: linear-gradient(135deg, #0a3d62, #1e5799);
                    }}

                    .header .date {{
                        color: #bbdefb;
                    }}

                    .section {{
                        background-color: #2e3b4e;
                        color: #e0e0e0;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
                    }}

                    .section h2 {{
                        color: #bbdefb;
                    }}

                    .section p, .section pre {{
                        color: #e0e0e0;
                    }}
                }}

                .footer {{
                    text-align: center;
                    margin-top: 20px;
                }}
            </style>
            <meta name="color-scheme" content="light dark">
        </head>
        <body>
            <div class="container">
                <div class="header">
                    Daily Summary
                    <div class="date">{date_string}</div>
                </div>
                {html_content}
                <div class="footer">
                    <p style="font-size: 14px; color: inherit;">
                        View the project on 
                        <a href="https://github.com/tdavis6/dailySummaryEmail" target="_blank" style="color: inherit; text-decoration: underline;">GitHub</a>
                    </p>
                    <p style="font-size: 12px; color: inherit;">
                        Version: {version} | Generated on: {current_datetime}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.debug(f"Type of timezone in send_email: {type(timezone)}")
        logging.debug(f"Timezone in send_email: {timezone}")
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.critical(f"Error sending email: {e}")
