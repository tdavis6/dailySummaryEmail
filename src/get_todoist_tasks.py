import logging
from todoist_api_python.api import TodoistAPI

def get_todoist_tasks(TODOIST_API_KEY):
    api = TodoistAPI(TODOIST_API_KEY)
    try:
        # Fetch tasks that are due before tomorrow
        todoist_data = api.get_tasks(filter="due before: tomorrow & (assigned to: me | !assigned)")
        return todoist_data
    except Exception as e:
        logging.critical(f"Error occurred in get_todoist_tasks: {e}")
        return []
