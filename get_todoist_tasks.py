import datetime
import logging

import pytz
from todoist_api_python.api import TodoistAPI


def get_todoist_tasks(TODOIST_API_KEY, TIMEZONE) -> str:
    api = TodoistAPI(TODOIST_API_KEY)
    text = """"""
    try:
        todoist_data = api.get_tasks(filter="due before: tomorrow")
        logging.debug(todoist_data)

        def get_due_datetime_and_priority(task):
            due_dt = datetime.datetime.fromisoformat(task.due.datetime).astimezone(
                pytz.utc) if task.due.datetime is not None else datetime.datetime.fromisoformat(
                f"{task.due.date}T23:59:59").astimezone(pytz.utc)
            return (due_dt, (5 - task.priority))

        # Sort tasks
        sorted_todoist_data = sorted(todoist_data, key=get_due_datetime_and_priority)
        logging.debug(sorted_todoist_data)

        # Current time in UTC for comparison
        now = datetime.datetime.now(tz=pytz.timezone(TIMEZONE)).date()

        if todoist_data is not None:
            for task in sorted_todoist_data:
                text += f"\n\n - [{task.content}]({task.url})"

                if task.due is not None:
                    due_datetime = None
                    if task.due.datetime is not None:
                        due_datetime = datetime.datetime.fromisoformat(task.due.datetime).astimezone(pytz.utc)
                    else:
                        due_datetime = datetime.datetime.fromisoformat(f"{task.due.date}T23:59:59").astimezone(pytz.utc)

                    # Due date in the specified timezone
                    due_date_local = due_datetime.astimezone(pytz.timezone(TIMEZONE)).date()

                    # Check if the task is overdue
                    is_overdue = due_date_local < now

                    if is_overdue:
                        if task.due.datetime is not None:
                            text += f", due {due_datetime.astimezone(pytz.timezone(TIMEZONE)).strftime('at %H:%M on %Y-%m-%d')}"
                        else:
                            text += f", due on {task.due.date}"
                    else:
                        if task.due.datetime is not None:
                            text += f", due {due_datetime.astimezone(pytz.timezone(TIMEZONE)).strftime('at %H:%M')}"

                if task.priority != 1:
                    text += f", priority {(5 - task.priority)}"

        return text

    except Exception as e:
        logging.critical(f"Error occurred: {e}")