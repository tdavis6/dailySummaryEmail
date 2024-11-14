import logging
import datetime
import pytz
from get_todoist_tasks import get_todoist_tasks

def format_time(datetime_obj, time_system):
    if time_system.upper() == "12HR":
        return datetime_obj.strftime("%I:%M %p")
    else:  # default to 24hr
        return datetime_obj.strftime("%H:%M")

def get_todo_tasks(timezone, TIME_SYSTEM, TODOIST_API_KEY=None):
    text = ""
    if TODOIST_API_KEY:
        text += "\n\n# Tasks"

        # Fetch raw task data from Todoist
        raw_todoist_data = get_todoist_tasks(TODOIST_API_KEY)

        # Process and sort tasks
        tasks = []
        for task in raw_todoist_data:
            # Calculate due datetime and priority weight
            due_dt = None
            if task.due and task.due.datetime:
                due_dt = datetime.datetime.fromisoformat(task.due.datetime)
                if due_dt.tzinfo is None:
                    due_dt = timezone.localize(due_dt)
                due_dt = due_dt.astimezone(pytz.utc)
            elif task.due and task.due.date:
                due_dt = datetime.datetime.fromisoformat(f"{task.due.date}T23:59:59")
                if due_dt.tzinfo is None:
                    due_dt = timezone.localize(due_dt)
                due_dt = due_dt.astimezone(pytz.utc)

            tasks.append((task, due_dt, (5 - task.priority)))

        # Sort by due datetime and priority
        tasks.sort(key=lambda x: (x[1], x[2]))

        # Current date for overdue checks
        now = datetime.datetime.now(tz=timezone).date()

        # Format tasks for display
        for task, due_dt, _ in tasks:
            task_text = f"\n\n - [{task.content}]({task.url})"

            if due_dt:
                due_local = due_dt.astimezone(timezone).date()
                is_overdue = due_local < now

                if is_overdue:
                    if task.due.datetime:
                        due_time = format_time(due_dt.astimezone(timezone), TIME_SYSTEM)
                        task_text += f", due at {due_time} on {due_dt.astimezone(timezone).strftime('%A, %B %d, %Y')}"
                    else:
                        task_text += f", due on {due_dt.astimezone(timezone).strftime('%A, %B %d, %Y')}"
                else:
                    if task.due.datetime:
                        due_time = format_time(due_dt.astimezone(timezone), TIME_SYSTEM)
                        task_text += f", due at {due_time}"
            if task.priority != 1:
                task_text += f", priority {(5 - task.priority)}"

            text += task_text

    logging.debug(text)
    return text
