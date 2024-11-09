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
        # Updated concise subject line
        message["Subject"] = f"Daily Summary for {date_string}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = ""
        html_text = ""

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
            extensions=[
                "markdown.extensions.fenced_code",
            ],
        )

        html = f"""
        <html>
        <head>
            <style>
                @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@300;600&display=swap');
                
                body {{
                    background: linear-gradient(135deg, #e3f2fd, #bbdefb);  /* Soft light blue gradient */
                    font-family: 'Raleway', 'Segoe UI', Tahoma, Geneva, sans-serif;
                    color: #000000;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    width: 90%;
                    max-width: 750px;
                    margin: 40px auto;
                    background: #ffffff;
                    padding: 30px;
                    border-radius: 12px;
                    box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.2);  /* Slight drop shadow to bottom-left */
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #1e88e5, #42a5f5);
                    color: #fff;
                    padding: 20px;
                    text-align: center;
                    font-size: 28px;
                    font-weight: 600;
                    border-radius: 12px 12px 0 0;
                    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.2);
                }}
                .header .date {{
                    font-size: 16px;
                    font-weight: 300;
                    margin-top: 5px;
                    color: #e3f2fd;
                }}
                h1 {{
                    color: #1e88e5;
                    font-size: 24px;
                    margin-bottom: 15px;
                    border-bottom: 2px solid #e3e3e3;
                    padding-bottom: 5px;
                    text-align: left;
                }}
                h2, h3 {{
                    color: #1e88e5;
                    font-size: 20px;
                    margin-top: 20px;
                }}
                p {{
                    font-size: 18px;
                    color: #000000;
                    margin: 15px 0;
                    line-height: 1.8;
                }}
                /* Fixing bold text in the events/tasks list */
                strong {{
                    font-weight: normal;
                }}
                a {{
                    color: #1e88e5;
                    text-decoration: none;
                    font-weight: 600;
                }}
                a:hover {{
                    text-decoration: underline;
                    color: #1565c0;
                }}
                .highlight {{
                    background: #fff3cd;
                    border-left: 5px solid #ffc107;
                    padding: 10px 15px;
                    font-style: italic;
                    color: #856404;
                    margin: 15px 0;
                }}
                .footer {{
                    text-align: center;
                    font-size: 14px;
                    margin-top: 20px;
                }}
                .footer a {{
                    color: #1e88e5;
                    text-decoration: none;
                }}
                .footer a:hover {{
                    text-decoration: underline;
                    color: #1565c0;
                }}
                @media only screen and (max-width: 600px) {{
                    .container {{
                        padding: 20px;
                        border-radius: 0; /* Remove rounded corners */
                        box-shadow: none; /* Remove drop shadow */
                    }}
                    .header {{
                        font-size: 22px;
                    }}
                    h1 {{
                        font-size: 20px;
                    }}
                    h2, h3 {{
                        font-size: 18px;
                    }}
                    p {{
                        font-size: 16px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    Daily Summary
                    <div class="date">{date_string}</div>
                </div>
                {html_content}
                <div class="footer">
                    <a href="https://github.com/tdavis6/dailySummaryEmail" target="_blank">
                        View the project on GitHub
                    </a>
                </div>
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
