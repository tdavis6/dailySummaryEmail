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

        text = ""  # Initialize the plain text content
        html_text = ""  # Initialize the HTML content

        # Convert the Markdown strings to HTML and append to text and html_text
        def convert_and_append(markdown_string, section_class, text_format=True, is_date=False):
            nonlocal text, html_text  # Ensure we modify the outer variables
            if markdown_string is not None:
                # Convert Markdown to HTML
                html_converted = markdown.markdown(markdown_string, extensions=["markdown.extensions.fenced_code"])

                # Prepare text format for plain text email (if required)
                if text_format:
                    text += markdown_string + "\n\n"

                # Append HTML formatted content with section, skip date in HTML
                if not is_date:
                    html_text += f"<div class='section {section_class}'>{html_converted}</div>"

        if date_string is not None:
            # Include the date in plain text but skip in HTML content (header will be handled separately)
            text += "# " + date_string + "\n\n"

        # Convert the other sections to text and HTML
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
                    border-radius: 12px; /* Rounded corners */
                }}

                /* Media query for small screens (768px or smaller) */
                @media (max-width: 768px) {{
                    .container {{
                        border-radius: 0; /* Remove rounded corners on small screens */
                    }}
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
                    border-radius: 12px; /* Rounded all corners of the header */
                }}

                .header .date {{
                    font-size: 18px;
                    font-weight: 300;
                    color: #e3f2fd;
                }}

                .section {{
                    background-color: #f7f7f7; /* Light gray background for sections in light mode */
                    padding: 20px;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                    margin-top: 20px;
                    margin-bottom: 20px;
                }}

                .section h2, .weather h2 {{
                    font-size: 30px;
                    font-weight: 600;
                    color: #000; /* Text color changed back to black for light mode */
                }}

                .section p, .weather p {{
                    font-size: 18px;
                    color: #000; /* Text color changed back to black for light mode */
                }}

                /* Dark mode adjustments */
                @media (prefers-color-scheme: dark) {{
                    body {{
                        background: linear-gradient(135deg, #2a3c57, #1e2a3f); /* Blue gradient for dark mode */
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
                        background-color: #2e3b4e; /* Darker blue background for sections in dark mode */
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); /* Darker shadow */
                    }}

                    .weather {{
                        background-color: #2e3b4e; /* Dark background for weather section */
                        color: #bbdefb; /* Light blue text color */
                    }}

                    .weather h2, .section h2 {{
                        color: #bbdefb; /* Light blue for headers in dark mode */
                    }}

                    p, .section p {{
                        color: #e0e0e0; /* Ensure paragraph text is light in dark mode */
                    }}

                    .button {{
                        background-color: #1c7ed6;
                    }}

                    .button:hover {{
                        background-color: #82caff;
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
                </div>
            </div>
        </body>
        </html>
        """

        # Send the email as usual
        message.attach(MIMEText(text, "plain"))
        message.attach(MIMEText(html, "html"))

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        logging.info("Email sent successfully.")
    except Exception as e:
        logging.critical(f"Error sending email: {e}")
