import logging
import datetime
import pytz
from get_todoist_tasks import get_todoist_tasks
from get_vikunja_tasks import get_vikunja_tasks


def format_time(datetime_obj, time_system):
    if time_system.upper() == "12HR":
        return datetime_obj.strftime("%I:%M %p")
    else:  # default to 24hr
        return datetime_obj.strftime("%H:%M")


def get_todo_tasks(
        timezone,
        TIME_SYSTEM,
        TODOIST_API_KEY=None,
        VIKUNJA_API_KEY=None,
        VIKUNJA_BASE_URL=None,
):

    tasks_text = ""
    if TODOIST_API_KEY or VIKUNJA_API_KEY:
        tasks_text += "\n\n# Tasks"  # Main header

    if TODOIST_API_KEY:
        # Fetch raw task data from Todoist
        raw_todoist_data = get_todoist_tasks(TODOIST_API_KEY)
        tasks_text += process_tasks(
            tasks_text, raw_todoist_data, timezone, TIME_SYSTEM, source="todoist"
        )

    if VIKUNJA_API_KEY and VIKUNJA_BASE_URL:
        # Fetch raw task data from Vikunja
        raw_vikunja_data = get_vikunja_tasks(VIKUNJA_API_KEY, VIKUNJA_BASE_URL)

        tasks_text += process_tasks(
            tasks_text,
            raw_vikunja_data,
            timezone,
            TIME_SYSTEM,
            source="vikunja",
            VIKUNJA_BASE_URL=VIKUNJA_BASE_URL,
        )

    logging.debug(tasks_text)
    return parse_task_sections(tasks_text)


def process_tasks(
        tasks_text,
        raw_tasks_data,
        timezone,
        TIME_SYSTEM,
        source="todoist",
        VIKUNJA_BASE_URL=None,
) -> str:
    tasks = []

    for task in raw_tasks_data:
        due_dt = None
        if source.lower() == "todoist":
            # Todoist tasks handling
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
            tasks.append((task, due_dt, task.priority))

        elif source.lower() == "vikunja":
            # Vikunja tasks handling
            due_date = task.get("due_date")
            if due_date:
                if "T" in due_date:  # Full datetime
                    due_dt = datetime.datetime.fromisoformat(due_date)
                else:  # Only date part
                    due_dt = datetime.datetime.fromisoformat(f"{due_date}T23:59:59")

                if due_dt.tzinfo is None:
                    due_dt = timezone.localize(due_dt)
                due_dt = due_dt.astimezone(timezone)

            priority = task.get("priority", 5)
            tasks.append((task, due_dt, priority))

    # Sort by due datetime and priority
    tasks.sort(key=lambda x: (x[1] or datetime.datetime.max.replace(tzinfo=timezone), -x[2]))

    now = datetime.datetime.now(tz=timezone).date()

    tasks_text = ""
    for task, due_dt, priority in tasks:
        if source == "todoist":
            task_text = f"\n\n - [{task.content}]({task.url})"
        elif source == "vikunja":
            task_text = (
                f"\n\n - [{task['title']}]({VIKUNJA_BASE_URL}/tasks/{task['id']})"
            )

        if due_dt:
            due_local = due_dt.date()
            is_overdue = due_local < now
            has_explicit_time = due_dt.time() != datetime.time(23, 59, 59)

            if is_overdue:
                if has_explicit_time:
                    due_time = format_time(due_dt, TIME_SYSTEM)
                    task_text += (
                        f", overdue, due at {due_time} on {due_dt.strftime('%A, %B %d, %Y')}"
                    )
                else:
                    task_text += f", overdue, due on {due_dt.strftime('%A, %B %d, %Y')}"
            elif has_explicit_time:
                due_time = format_time(due_dt, TIME_SYSTEM)
                task_text += f", due at {due_time}"


        # Include priority only if it's not 4 for Todoist or 0 for Vikunja
        if source == "todoist" and 5-task.priority != 4:
            task_text += f", priority {5-task.priority}"

        if source == "vikunja" and task["priority"] != 0:
            task_text += f", priority {6-task['priority']}"

        tasks_text += task_text

    return tasks_text


def parse_task_sections(tasks_text):
    sections = {
        "Overdue": [],
        "Morning": [],
        "Afternoon": [],
        "Evening": [],
        "General": [],
    }

    # Don't include the header if tasks_text is empty or doesn't contain tasks
    task_lines = tasks_text.splitlines()
    output_text = ""
    if any(line.strip() for line in task_lines if line.strip() != "# Tasks"):
        output_text = "# Tasks"

    for line in task_lines:
        line = line.strip()
        if not line or line == "# Tasks":
            continue

        if "overdue" in line or "due on" in line:
            sections["Overdue"].append(line)
        elif "due at" in line:
            time_part = line.split("due at ")[-1].split(",")[0].strip()
            try:
                if "AM" in time_part or "PM" in time_part:
                    # Parse using %I (allowing leading zero or not)
                    due_time = datetime.datetime.strptime(time_part, "%I:%M %p")
                    # Re‐format with %-I to drop any leading zero
                    formatted = due_time.strftime("%-I:%M %p")
                    line = line.replace(time_part, formatted)
                else:
                    due_time = datetime.datetime.strptime(time_part, "%H:%M")

                if due_time.hour < 12:
                    sections["Morning"].append(line)
                elif 12 <= due_time.hour < 17:
                    sections["Afternoon"].append(line)
                else:
                    sections["Evening"].append(line)
            except ValueError:
                sections["General"].append(line)
        else:
            sections["General"].append(line)

    for section, tasks in sections.items():
        if tasks:
            output_text += f"\n\n## {section} Tasks"
            output_text += "\n" + "\n".join(tasks)

    return output_text