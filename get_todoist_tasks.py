from datetime import datetime
from lib2to3.pytree import convert

from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task
import pytz


def convertTaskTimeToUTC(taskTimezone:str, taskDatetime:str, TIMEZONE):
    if not taskTimezone:
        taskTimezone = TIMEZONE
    local = pytz.timezone(taskTimezone)
    naive = datetime.strptime(taskDatetime, "%Y-%m-%dT%H:%M:%S")
    local_dt = local.localize(naive, is_dst=None)
    utc_dt = local_dt.astimezone(pytz.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%S")

def get_todoist_tasks(TODOIST_API_KEY, TIMEZONE) -> list[Task]:
    api = TodoistAPI(TODOIST_API_KEY)
    try:
        todoist_data = api.get_tasks(filter="due before: tomorrow")
        sorted_todoist_data = sorted(todoist_data, key=lambda task: (convertTaskTimeToUTC(taskTimezone=task.due.timezone, taskDatetime=task.due.datetime if task.due.datetime else f"{task.due.date}T23:59:59", TIMEZONE=TIMEZONE), (5-task.priority)))
        print(todoist_data)
        return sorted_todoist_data

    except Exception as e:
        print(f"Error occurred: {e}")
