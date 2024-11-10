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
        message["Subject"] = f"Daily Summary for {recipient_name}: {date_string}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = ""
        html_text = ""

        # Append content dynamically
        if date_string is not None:
            text += "# " + date_string + "\n\n"

        if weather_string is not None:
            text += weather_string + "\n\n"
            html_text += weather_string + "\n\n"

        if todo_string is not None:
            text += todo_string + "\n\n"
            html_text += todo_string + "\n\n"

        if cal_string is not None:
            text += cal_string + "\n\n"
            html_text += cal_string + "\n\n"

        if rss_string is not None:
            text += rss_string + "\n\n"
            html_text += rss_string + "\n\n"

        if puzzles_string is not None:
            text += puzzles_string + "\n\n"
            html_text += puzzles_string + "\n\n"

        if wotd_string is not None:
            text += wotd_string + "\n\n"
            html_text += wotd_string + "\n\n"

        if quote_string is not None:
            text += quote_string + "\n\n"
            html_text += quote_string + "\n\n"

        if puzzles_ans_string is not None:
            text += puzzles_ans_string + "\n\n"
            html_text += puzzles_ans_string + "\n\n"

        html_content = markdown.markdown(
            html_text,
            extensions=["markdown.extensions.fenced_code"]
        )

        html = f"""
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;600&display=swap');

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
                    font-family: 'Raleway', 'Segoe UI', Tahoma, Geneva, sans-serif;
                    color: #000;
                    margin: 0;
                    padding: 0;
                }}

                .container {{
                    background: #ffffff;
                    color: #000000;
                    box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.2);
                    max-width: 750px;
                    margin: 40px auto;
                    padding: 30px;
                    animation: slideUp 0.6s ease-out;
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
                    border-radius: 12px 12px 0 0;
                }}

                .header .date {{
                    font-size: 18px;
                    font-weight: 300;
                    color: #e3f2fd;
                }}

                p {{
                    font-size: 18px;
                    line-height: 1.6;
                }}

                a {{
                    text-decoration: none;
                }}

                .button {{
                    display: inline-block;
                    padding: 8px 16px;
                    font-size: 16px;
                    font-weight: bold;
                    color: white;
                    background-color: #1e88e5;
                    border-radius: 8px;
                    text-align: center;
                    margin-top: 20px;
                    animation: slideUp 1s ease-out 0.5s;
                }}

                .button:hover {{
                    background-color: #1565c0;
                }}

                .footer {{
                    text-align: center;
                }}

                /* Remove rounded corners for small screens */
                @media (min-width: 768px) {{
                    .container {{
                        border-radius: 12px;
                    }}
                }}

                @media (prefers-color-scheme: dark) {{
                    body {{
                        background: linear-gradient(135deg, #1b263b, #0d1b2a);
                        color: #e0e0e0;
                    }}

                    .container {{
                        background: #000;
                        color: #e0e0e0;
                        box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.5);
                    }}

                    .header {{
                        background: linear-gradient(135deg, #0a3d62, #1e5799);
                    }}

                    .header .date {{
                        color: #bbdefb;
                    }}

                    p {{
                        color: #e0e0e0;
                    }}

                    .button {{
                        background-color: #1c7ed6;
                    }}

                    .button:hover {{
                        background-color: #82caff;
                    }}
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
                    <a href="https://github.com/tdavis6/dailySummaryEmail" target="_blank" class="button">
                        View the project on GitHub
                    </a>
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
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.critical(f"Error sending email: {e}")
