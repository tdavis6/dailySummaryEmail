import logging

from get_todoist_tasks import get_todoist_tasks

def get_todo_tasks(TIMEZONE, TIME_SYSTEM, TODOIST_API_KEY = None):
    text = """"""
    if TODOIST_API_KEY:
        text += "\n\n# Tasks"
        text += get_todoist_tasks(TODOIST_API_KEY, TIMEZONE, TIME_SYSTEM)

    logging.debug(text)
    return text
