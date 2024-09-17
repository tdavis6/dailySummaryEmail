import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from datetime import datetime


def send_email(
        recipient_email,
        recipient_name,
        sender_email,
        smtp_username,
        smtp_password,
        smtp_host,
        smtp_port,
        weather_data,
        todoist_data
) -> None:

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {recipient_name}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = f"""\
{weather_data['forecast']['properties']['periods'][0]['name']}'s Weather Forecast for {weather_data['city']}, {weather_data['state']}: \
{weather_data['forecast']['properties']['periods'][0]['detailedForecast']}

Here are the tasks for the day:"""
        for task in todoist_data:
            if task.due.date != datetime.today().strftime("%Y-%m-%d"):
                text = text + f"\n - {task.content}, due {task.due.date}, with priority {task.priority}"
            else:
                text = text + f"\n - {task.content} with priority {task.priority}"
        html = f"""\
        <html>
        <body>
        
        </body>
        </html>"""
        part_1 = MIMEText(text, "plain")
        #part_2 = MIMEText(html, "html")

        message.attach(part_1)
        #message.attach(part_2)

        print(text)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(
                sender_email, recipient_email, message.as_string()
            )
    except Exception as e:
        print(f"Error occurred: {e}")
