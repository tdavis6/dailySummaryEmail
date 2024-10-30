import datetime
import logging

import pytz
from todoist_api_python.api import TodoistAPI


def format_time(datetime_obj, time_system):
    if time_system.upper() == "12HR":
        return datetime_obj.strftime("%I:%M %p")
    else:  # default to 24hr
        return datetime_obj.strftime("%H:%M")


def get_todoist_tasks(TODOIST_API_KEY, TIMEZONE, TIME_SYSTEM) -> str:
    api = TodoistAPI(TODOIST_API_KEY)
    text = ""
    try:
        todoist_data = api.get_tasks(filter="due before: tomorrow")

        def get_due_datetime_and_priority(task):
            if task.due.datetime is not None:
                # Parse and localize naive datetime to the provided TIMEZONE
                due_dt = datetime.datetime.fromisoformat(task.due.datetime)
                if due_dt.tzinfo is None:
                    due_dt = pytz.timezone(TIMEZONE).localize(due_dt)
                due_dt = due_dt.astimezone(pytz.utc)
            else:
                # Parse and localize naive date to the provided TIMEZONE, end of the day
                due_dt = datetime.datetime.fromisoformat(f"{task.due.date}T23:59:59")
                if due_dt.tzinfo is None:
                    due_dt = pytz.timezone(TIMEZONE).localize(due_dt)
                due_dt = due_dt.astimezone(pytz.utc)
            return (due_dt, (5 - task.priority))

        # Sort tasks
        sorted_todoist_data = sorted(todoist_data, key=get_due_datetime_and_priority)
        logging.debug(sorted_todoist_data)

        # Current time in the specified timezone for comparison
        now = datetime.datetime.now(tz=pytz.timezone(TIMEZONE)).date()

        if todoist_data:
            for task in sorted_todoist_data:
                text += f"\n\n - [{task.content}]({task.url})"

                if task.due is not None:
                    due_datetime = None
                    if task.due.datetime is not None:
                        # Parse and localize naive datetime to the provided TIMEZONE
                        due_datetime = datetime.datetime.fromisoformat(
                            task.due.datetime
                        )
                        if due_datetime.tzinfo is None:
                            due_datetime = pytz.timezone(TIMEZONE).localize(
                                due_datetime
                            )
                        due_datetime = due_datetime.astimezone(pytz.utc)
                    else:
                        # Parse and localize naive date to the provided TIMEZONE, end of the day
                        due_datetime = datetime.datetime.fromisoformat(
                            f"{task.due.date}T23:59:59"
                        )
                        if due_datetime.tzinfo is None:
                            due_datetime = pytz.timezone(TIMEZONE).localize(
                                due_datetime
                            )
                        due_datetime = due_datetime.astimezone(pytz.utc)

                    # Due date in the specified timezone
                    due_date_local = due_datetime.astimezone(
                        pytz.timezone(TIMEZONE)
                    ).date()

                    # Check if the task is overdue
                    is_overdue = due_date_local < now

                    if is_overdue:
                        if task.due.datetime is not None:
                            due_time_formatted = format_time(
                                due_datetime.astimezone(pytz.timezone(TIMEZONE)),
                                TIME_SYSTEM,
                            )
                            text += f", due {due_time_formatted} on {due_datetime.astimezone(pytz.timezone(TIMEZONE)).strftime('%A, %B %d, %Y')}"
                        else:
                            text += f", due on {due_datetime.astimezone(pytz.timezone(TIMEZONE)).strftime('%A, %B %d, %Y')}"
                    else:
                        if task.due.datetime is not None:
                            due_time_formatted = format_time(
                                due_datetime.astimezone(pytz.timezone(TIMEZONE)),
                                TIME_SYSTEM,
                            )
                            text += f", due {due_time_formatted}"

                if task.priority != 1:
                    text += f", priority {(5 - task.priority)}"

        return text

    except Exception as e:
        logging.critical(f"Error occurred: {e}")