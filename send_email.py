import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import datetime
import re
import markdown

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
    iso_pattern_with_hm = re.compile(
        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d{1,6})?)?$"
    )

    try:
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Daily Summary Email for {recipient_name}"
        message["From"] = f"Daily Summary <{smtp_username}>"
        message["To"] = recipient_email

        text = f"""\
{recipient_name},

{weather_data['forecast']['properties']['periods'][0]['name']}'s Weather Forecast for {weather_data['city']}, {weather_data['state']}: \
{weather_data['forecast']['properties']['periods'][0]['detailedForecast']}"""

        if todoist_data != None:
            text = text + "\n\nHere are the tasks for the day:"
            for task in todoist_data:
                if task.due.date != datetime.datetime.now(timezone).strftime("%Y-%m-%d"):
                    if iso_pattern_with_hm.match(task.due.datetime):
                        if task.priority == 1:
                            text = text + f"\n\n - [{task.content}]({task.url}), due {datetime.datetime.strptime(task.due.datetime, "%Y-%m-%dT%H:%M:%S").strftime("%A, %B %d, %Y at %H:%M")}"
                        else:
                            text = text + f"\n\n - [{task.content}]({task.url}), due {datetime.datetime.strptime(task.due.datetime, "%Y-%m-%dT%H:%M:%S").strftime("%A, %B %d, %Y at %H:%M")}, priority {(5-task.priority)}"
                    else:
                        if task.priority == 1:
                            text = text + f"\n\n - [{task.content}]({task.url}), due {datetime.datetime.strptime(task.due.date, "%Y-%m-%d").strftime("%A, %B %d, %Y")}"
                        else:
                            text = text + f"\n\n - [{task.content}]({task.url}), due {datetime.datetime.strptime(task.due.date, "%Y-%m-%d").strftime("%A, %B %d, %Y")}, priority {(5-task.priority)}"
                elif task.due.datetime:
                    if task.priority == 1:
                        text = text + f"\n\n - [{task.content}]({task.url}), due {datetime.datetime.strptime(task.due.datetime, "%Y-%m-%dT%H:%M:%S").strftime("at %H:%M")}"
                    else:
                        text = text + f"\n\n - [{task.content}]({task.url}), due {datetime.datetime.strptime(task.due.datetime, "%Y-%m-%dT%H:%M:%S").strftime("at %H:%M")}, priority {(5-task.priority)}"
                else:
                    if task.priority == 1:
                        text = text + f"\n\n - [{task.content}]({task.url})"
                    else:
                        text = text + f"\n\n - [{task.content}]({task.url}), priority {(5-task.priority)}"
        else:
            text = text + "\n\nThere are no tasks in Todoist!"

        html = markdown.markdown(text)

        part_1 = MIMEText(text, "plain")
        part_2 = MIMEText(html, "html")

        message.attach(part_1)
        message.attach(part_2)

        print(text)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_username, smtp_password)
            server.sendmail(
                sender_email, recipient_email, message.as_string()
            )
        print("Email sent.")
    except Exception as e:
        print(f"Error occurred: {e}")
