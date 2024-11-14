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
    tasks_text = ""
    if TODOIST_API_KEY:  # Make it easier to add support for additional to-do list apps
        tasks_text += "\n\n# Tasks"  # Main header

    if TODOIST_API_KEY:
        # Fetch raw task data from Todoist
        raw_todoist_data = get_todoist_tasks(TODOIST_API_KEY)

        # Process and sort tasks
        tasks = []
        for task in raw_todoist_data:
            due_dt = None
            if task.due and task.due.datetime:
                due_dt = datetime.datetime.fromisoformat(task.due.datetime)
                if due_dt.tzinfo is None:
                    due_dt = timezone.localize(due_dt)
                due_dt = due_dt.astimezone(timezone)
            elif task.due and task.due.date:
                due_dt = datetime.datetime.fromisoformat(f"{task.due.date}T23:59:59")
                if due_dt.tzinfo is None:
                    due_dt = timezone.localize(due_dt)
                due_dt = due_dt.astimezone(timezone)

            tasks.append((task, due_dt, (5 - task.priority)))

        # Sort by due datetime and priority
        tasks.sort(key=lambda x: (x[1], x[2]))

        # Current date for overdue checks
        now = datetime.datetime.now(tz=timezone).date()

        # Format tasks for display
        for task, due_dt, _ in tasks:
            task_text = f"\n\n - [{task.content}]({task.url})"

            if due_dt:
                due_local = due_dt.date()
                is_overdue = due_local < now

                if is_overdue:
                    if task.due.datetime:
                        due_time = format_time(due_dt, TIME_SYSTEM)
                        task_text += f", due at {due_time} on {due_dt.strftime('%A, %B %d, %Y')}"
                    else:
                        task_text += f", due on {due_dt.strftime('%A, %B %d, %Y')}"
                else:
                    if task.due.datetime:
                        due_time = format_time(due_dt, TIME_SYSTEM)
                        task_text += f", due at {due_time}"
            if task.priority != 1:
                task_text += f", priority {(5 - task.priority)}"

            tasks_text += task_text

    logging.debug(tasks_text)
    return parse_task_sections(tasks_text)  # Call parse_task_sections to categorize tasks

def parse_task_sections(tasks_text):
    sections = {
        "Overdue": [],
        "Morning": [],
        "Afternoon": [],
        "Evening": [],
        "General": []
    }

    # Initialize output_text with the "# Tasks" header only if tasks_text starts with it
    output_text = "# Tasks" if tasks_text.strip().startswith("# Tasks") else ""

    # Split tasks text into individual task lines
    task_lines = tasks_text.splitlines()

    for line in task_lines:
        line = line.strip()
        if not line or line == "# Tasks":
            continue  # Skip empty lines or the header itself

        # Check if task is overdue
        if "overdue" in line or "due on" in line:
            sections["Overdue"].append(line)

        # Check if the task has a due time and categorize by time of day
        elif "due at" in line:
            time_part = line.split("due at ")[-1].split(",")[0].strip()
            try:
                due_time = datetime.datetime.strptime(time_part, "%I:%M %p") if "AM" in time_part or "PM" in time_part else datetime.datetime.strptime(time_part, "%H:%M")

                # Categorize by time
                if due_time.hour < 12:
                    sections["Morning"].append(line)
                elif 12 <= due_time.hour < 17:
                    sections["Afternoon"].append(line)
                else:
                    sections["Evening"].append(line)
            except ValueError:
                sections["General"].append(line)
        else:
            # If no specific due time, categorize as General
            sections["General"].append(line)

    # Append each section with its formatted header and tasks
    for section, tasks in sections.items():
        if tasks:
            output_text += f"\n\n## {section} Tasks"
            output_text += "\n" + "\n".join(tasks)

    return output_text
