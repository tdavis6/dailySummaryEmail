import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import markdown
from datetime import datetime
import pytz
import traceback

from generate_summary import generate_summary
from add_emojis import add_emojis

def convert_section(markdown_string):
    """Convert markdown string to HTML."""
    if markdown_string:
        return markdown.markdown(markdown_string, extensions=["markdown.extensions.fenced_code"])
    else:
        return None

def append_section(text, html_text, markdown_string, section_class, text_format=True, is_date=False):
    """Append markdown and HTML content for a section."""
    if markdown_string and markdown_string.strip():
        converted_html = convert_section(markdown_string)
        if text_format:
            text += markdown_string + "\n\n"
        if not is_date and converted_html:
            html_text += f"<div class='section {section_class}'>{converted_html}</div>"
    else:
        logging.warning(f"{section_class} content is None, empty, or whitespace.")
    return text, html_text

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
        openai_api_key,
        date_string="",
        weather_string="",
        todo_string="",
        cal_string="",
        rss_string="",
        puzzles_string="",
        wotd_string="",
        quote_string="",
        puzzles_ans_string="",
) -> None:
    try:
        # Ensure timezone is a valid pytz timezone object
        if isinstance(timezone, str):
            timezone = pytz.timezone(timezone)
            logging.debug(f"Converted timezone string to pytz timezone object: {timezone}")

        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary for {recipient_name}: {date_string}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = ""  # Initialize the plain text content
        html_text = ""  # Initialize the HTML content

        # Apply emojis to each section with optional task lateness
        #weather_string = add_emojis(weather_string) # Do not apply emoji's to the weather string.
        todo_string = add_emojis(todo_string)
        cal_string = add_emojis(cal_string)
        rss_string = add_emojis(rss_string)
        #puzzles_string = add_emojis(puzzles_string) # Do not apple emoji's to the puzzle string.
        #wotd_string = add_emojis(wotd_string) # Do not apple emoji's to the wotd string.
        #quote_string = add_emojis(quote_string) # Do not apply emoji's to the qotd string.
        #puzzles_ans_string = add_emojis(puzzles_ans_string) # Do not apply emoji's to the puzzle string.

        # Append other sections
        if weather_string: text, html_text = append_section(text, html_text, weather_string, "weather")
        if todo_string: text, html_text = append_section(text, html_text, todo_string, "todo")
        if cal_string: text, html_text = append_section(text, html_text, cal_string, "calendar")
        if rss_string: text, html_text = append_section(text, html_text, rss_string, "rss")
        if puzzles_string: text, html_text = append_section(text, html_text, puzzles_string, "puzzles")
        if wotd_string: text, html_text = append_section(text, html_text, wotd_string, "wotd")
        if quote_string: text, html_text = append_section(text, html_text, quote_string, "quote")
        if puzzles_ans_string: text, html_text = append_section(text, html_text, puzzles_ans_string, "puzzles-ans")

        # Get summary
        if openai_api_key is not None:
            summary = "# Summary\n\n" + generate_summary(text, openai_api_key) + "\n\n"
            logging.debug("Summary obtained")

            text = summary + text
            summary_html = f"<div class='section summary'>{convert_section(summary)}</div>"
            html_text = summary_html + html_text

        # Append date section
        if date_string:
            text = "# " + date_string + "\n\n" + text
        else:
            logging.warning("date_string is None, empty, or whitespace.")
            text = "# Date Not Available\n\n" + text

        html_content = markdown.markdown(html_text, extensions=["markdown.extensions.fenced_code"])
        html_content = html_text if html_text else "<div class='section'>No additional content available</div>"
        current_datetime = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S %z")
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

                html {{
                    font-size: 18px;
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

                .section h1 {{
                    font-size: 1.5rem;
                    font-weight: 600;
                    color: #003366;
                }}
                
                .section h2 {{
                    font-size: 1.25rem;
                    font-weight: 500;
                    color: #003366;
                }}

                .section p, .section pre {{
                    font-size: 1rem;
                    line-height: 1.6;
                    color: #000;
                    margin-bottom: 16px;
                }}

                .header {{
                    background: linear-gradient(135deg, #1e88e5, #42a5f5);
                    color: white;
                    padding: 20px;
                    text-align: center;
                    font-size: 2rem;
                    font-weight: 600;
                    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
                    animation: slideUp 1s ease-out;
                    border-radius: 12px;
                }}

                .header .date {{
                    font-size: 1.125rem;
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

                    .section h1, .section h2 {{
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
                        📋 Version: {version} | Generated on: {current_datetime}
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        message.attach(MIMEText(text, "plain"))
        #message.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info(f"Email sent successfully on {current_datetime}.")
    except Exception as e:
        logging.critical(f"Error sending email: {e}")
        logging.critical(traceback.format_exc())
