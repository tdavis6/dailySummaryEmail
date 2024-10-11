from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task
import datetime
import pytz
import logging

def get_todoist_tasks(TODOIST_API_KEY, TIMEZONE) -> list[Task]:
    api = TodoistAPI(TODOIST_API_KEY)
    try:
        todoist_data = api.get_tasks(filter="due before: tomorrow")
        logging.debug(todoist_data)
        sorted_todoist_data = sorted(todoist_data, key=lambda task: (datetime.datetime.fromisoformat(task.due.datetime).astimezone(pytz.utc) if task.due.datetime is not None else datetime.datetime.fromisoformat(f"{task.due.date}T23:59:59").astimezone(task.due.timezone if task.due.timezone is not None else pytz.timezone(TIMEZONE)), (5-task.priority)))
        logging.debug(sorted_todoist_data)
        return sorted_todoist_data

    except Exception as e:
        print(f"Error occurred: {e}")
        logging.critical(f"Error occurred: {e}")
