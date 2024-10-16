from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task
import datetime
import pytz
import logging

def get_todoist_tasks(TODOIST_API_KEY, TIMEZONE) -> list[Task]:
    api = TodoistAPI(TODOIST_API_KEY)
    text = """"""
    try:
        todoist_data = api.get_tasks(filter="due before: tomorrow")
        logging.debug(todoist_data)
        sorted_todoist_data = sorted(todoist_data, key=lambda task: (datetime.datetime.fromisoformat(task.due.datetime).astimezone(pytz.utc) if task.due.datetime is not None else datetime.datetime.fromisoformat(f"{task.due.date}T23:59:59").astimezone(task.due.timezone if task.due.timezone is not None else pytz.timezone(TIMEZONE)), (5-task.priority)))
        logging.debug(sorted_todoist_data)

        if todoist_data is not None:
            for task in todoist_data:
                text = text + f"\n\n - [{task.content}]({task.url})"
                if task.due.timezone is not None:
                    text = text + f", due {datetime.datetime.fromisoformat(task.due.datetime).astimezone(tz=pytz.timezone(TIMEZONE)).strftime("at %H:%M")}" if task.due.datetime is not None else text + ""
                else:
                    text = text + f", due {datetime.datetime.fromisoformat(task.due.datetime).strftime("at %H:%M")}" if task.due.datetime is not None else text + ""
                text = text + f", priority {(5-task.priority)}" if task.priority != 1 else text + ""
        else:
            None

        return text

    except Exception as e:
        logging.critical(f"Error occurred: {e}")
