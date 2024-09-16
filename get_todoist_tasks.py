from datetime import datetime
from todoist_api_python.api import TodoistAPI
from todoist_api_python.models import Task


def get_todoist_tasks(TODOIST_API_KEY) -> list[Task]:
    api = TodoistAPI(TODOIST_API_KEY)

    try:
        todoist_data = api.get_tasks(filter="due before: tomorrow")
        sorted_todoist_data = sorted(todoist_data,key=lambda task: (datetime.strptime(task.due.date, "%Y-%m-%d"), (5-task.priority)),)
        return sorted_todoist_data

    except Exception as e:
        print(f"Error occurred: {e}")
