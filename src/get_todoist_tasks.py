import logging
from todoist_api_python.api import TodoistAPI

def get_todoist_tasks(TODOIST_API_KEY):
    api = TodoistAPI(TODOIST_API_KEY)
    try:
        tasks = []
        for page in api.filter_tasks(query="due before: tomorrow & (assigned to: me | !assigned)"):
            tasks.extend(page)
        return tasks
    except Exception as e:
        logging.critical(f"Error occurred in get_todoist_tasks: {e}")
        return []