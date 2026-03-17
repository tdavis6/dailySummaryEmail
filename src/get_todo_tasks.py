import logging
import datetime
import pytz
from get_todoist_tasks import get_todoist_tasks
from get_vikunja_tasks import get_vikunja_tasks


def format_time(datetime_obj, time_system):
    if time_system.upper() == "12HR":
        return datetime_obj.strftime("%I:%M %p")
    else:
        return datetime_obj.strftime("%H:%M")


def get_todo_tasks(
        timezone,
        TIME_SYSTEM,
        TODOIST_API_KEY=None,
        VIKUNJA_API_KEY=None,
        VIKUNJA_BASE_URL=None,
):
    html_text = ""
    plain_text = ""

    if TODOIST_API_KEY or VIKUNJA_API_KEY:
        html_text += "\n\n# Tasks"
        plain_text += "\n\n# Tasks"

    if TODOIST_API_KEY:
        raw_todoist_data = get_todoist_tasks(TODOIST_API_KEY)
        h, p = process_tasks(raw_todoist_data, timezone, TIME_SYSTEM, source="todoist")
        html_text += h
        plain_text += p

    if VIKUNJA_API_KEY and VIKUNJA_BASE_URL:
        raw_vikunja_data = get_vikunja_tasks(VIKUNJA_API_KEY, VIKUNJA_BASE_URL)
        h, p = process_tasks(
            raw_vikunja_data,
            timezone,
            TIME_SYSTEM,
            source="vikunja",
            VIKUNJA_BASE_URL=VIKUNJA_BASE_URL,
        )
        html_text += h
        plain_text += p

    logging.debug(html_text)
    return parse_task_sections(html_text), parse_task_sections(plain_text, plain=True)


def process_tasks(
        raw_tasks_data,
        timezone,
        TIME_SYSTEM,
        source="todoist",
        VIKUNJA_BASE_URL=None,
):
    tasks = []

    for task in raw_tasks_data:
        due_dt = None
        if source.lower() == "todoist":
            if task.due:
                due_val = task.due.date
                if isinstance(due_val, datetime.datetime):
                    due_dt = due_val
                    if due_dt.tzinfo is None:
                        due_dt = timezone.localize(due_dt)
                    due_dt = due_dt.astimezone(timezone)
                else:
                    due_dt = datetime.datetime.combine(due_val, datetime.time(23, 59, 59))
                    due_dt = timezone.localize(due_dt)
            tasks.append((task, due_dt, task.priority))

        elif source.lower() == "vikunja":
            due_date = task.get("due_date")
            if due_date:
                if "T" in due_date:
                    due_dt = datetime.datetime.fromisoformat(due_date)
                else:
                    due_dt = datetime.datetime.fromisoformat(f"{due_date}T23:59:59")
                if due_dt.tzinfo is None:
                    due_dt = timezone.localize(due_dt)
                due_dt = due_dt.astimezone(timezone)

            priority = task.get("priority", 5)
            tasks.append((task, due_dt, priority))

    tasks.sort(key=lambda x: (x[1] or datetime.datetime.max.replace(tzinfo=timezone), -x[2]))

    now = datetime.datetime.now(tz=timezone).date()

    html_tasks_text = ""
    plain_tasks_text = ""

    for task, due_dt, priority in tasks:
        if source == "todoist":
            project_name = getattr(task, "_project_name", "Inbox")
            html_title = f"[{task.content}]({task.url})"
            plain_title = f"{task.content} ({task.url})"
        elif source == "vikunja":
            project_name = task.get("project_name", "Inbox")
            url = f"{VIKUNJA_BASE_URL}/tasks/{task['id']}"
            html_title = f"[{task['title']}]({url})"
            plain_title = f"{task['title']} ({url})"

        # Build shared metadata parts
        meta_parts = [project_name]

        deadline_date = None
        deadline_overdue = False
        if source == "todoist" and getattr(task, "deadline", None):
            try:
                d = task.deadline.date
                if isinstance(d, str):
                    deadline_date = datetime.date.fromisoformat(d)
                elif isinstance(d, datetime.datetime):
                    deadline_date = d.date()
                elif isinstance(d, datetime.date):
                    deadline_date = d
                if deadline_date is not None:
                    deadline_overdue = deadline_date < now
            except (ValueError, AttributeError):
                pass

        if due_dt:
            due_local = due_dt.date()
            is_overdue = due_local < now
            has_explicit_time = due_dt.time() != datetime.time(23, 59, 59)

            if is_overdue:
                if has_explicit_time:
                    due_time = format_time(due_dt, TIME_SYSTEM)
                    meta_parts.append(f"⚠️ Overdue · {due_dt.strftime('%b %-d')} at {due_time}")
                else:
                    meta_parts.append(f"⚠️ Overdue · {due_dt.strftime('%b %-d')}")
            elif has_explicit_time:
                due_time = format_time(due_dt, TIME_SYSTEM)
                meta_parts.append(f"Due at {due_time}")

        if deadline_date is not None:
            if deadline_overdue:
                meta_parts.append(f"🚨 Deadline passed · {deadline_date.strftime('%b %-d')}")
            else:
                meta_parts.append(f"Deadline: {deadline_date.strftime('%b %-d')}")

        if source == "todoist" and 5 - task.priority != 4:
            meta_parts.append(f"Priority {5 - task.priority}")
        if source == "vikunja" and task["priority"] != 0:
            meta_parts.append(f"Priority {6 - task['priority']}")

        meta_html = (
            f'<small style="color: #888; font-size: 0.8em; display: block; margin-top: 2px; white-space: normal; word-break: break-word;">'
            f'{" &nbsp;·&nbsp; ".join(meta_parts)}'
            f'</small>'
        )
        meta_plain = "  " + " · ".join(meta_parts)

        html_tasks_text += f"\n\n - {html_title}<br>{meta_html}"
        plain_tasks_text += f"\n\n - {plain_title}\n{meta_plain}"

    return html_tasks_text, plain_tasks_text


def parse_task_sections(tasks_text, plain=False):
    sections = {
        "Overdue": [],
        "Morning": [],
        "Afternoon": [],
        "Evening": [],
        "General": [],
    }

    task_lines = tasks_text.splitlines()
    output_text = ""
    if any(line.strip() for line in task_lines if line.strip() != "# Tasks"):
        output_text = "# Tasks"

    for line in task_lines:
        stripped = line.strip()
        if not stripped or stripped == "# Tasks":
            continue

        if "⚠️ Overdue" in line or "🚨 Deadline passed" in line:
            sections["Overdue"].append(stripped)
        elif "🕐 Due at" in line:
            time_part = line.split("🕐 Due at ")[-1].split("&")[0].split("<")[0].strip()
            try:
                if "AM" in time_part or "PM" in time_part:
                    due_time = datetime.datetime.strptime(time_part, "%I:%M %p")
                    formatted = due_time.strftime("%-I:%M %p")
                    stripped = line.replace(time_part, formatted).strip()
                else:
                    due_time = datetime.datetime.strptime(time_part, "%H:%M")

                if due_time.hour < 12:
                    sections["Morning"].append(stripped)
                elif 12 <= due_time.hour < 17:
                    sections["Afternoon"].append(stripped)
                else:
                    sections["Evening"].append(stripped)
            except ValueError:
                sections["General"].append(stripped)
        else:
            sections["General"].append(stripped)

    for section, tasks in sections.items():
        if tasks:
            output_text += f"\n\n## {section} Tasks"
            output_text += "\n" + "\n".join(tasks)

    return output_text