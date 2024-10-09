import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime

def send_email(
        recipient_email,
        recipient_name,
        sender_email,
        smtp_username,
        smtp_password,
        smtp_host,
        smtp_port,
        weather_data,
        todoist_data,
        timezone
) -> None:

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {recipient_name}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = f"""\
{recipient_name},

{weather_data['forecast']['properties']['periods'][0]['name']}'s Weather Forecast for {weather_data['city']}, {weather_data['state']}: \
{weather_data['forecast']['properties']['periods'][0]['detailedForecast']}

Here are the tasks for the day:"""
        for task in todoist_data:
            if task.due.date != datetime.datetime.now(timezone).strftime("%Y-%m-%d"):
                if task.priority == 1:
                    text = text + f"\n - {task.content}, due {datetime.datetime.strptime(task.due.date, "%Y-%m-%d").strftime("%A, %B %d, %Y")}"
                else:
                    text = text + f"\n - {task.content}, due {datetime.datetime.strptime(task.due.date, "%Y-%m-%d").strftime("%A, %B %d, %Y")}, priority {(5-task.priority)}"
            else:
                if task.priority == 1:
                    text = text + f"\n - {task.content}"
                else:
                    text = text + f"\n - {task.content}, priority {(5-task.priority)}"

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
