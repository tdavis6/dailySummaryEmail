import logging
import requests

def get_vikunja_tasks(VIKUNJA_API_KEY, VIKUNJA_BASE_URL):
    headers = {
        "Authorization": f"Bearer {VIKUNJA_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(f"{VIKUNJA_BASE_URL}/api/v1/tasks/all", headers=headers)
        response.raise_for_status()
        vikunja_data = response.json()

        tasks = []
        for task in vikunja_data:
            if task.get("done"):
                continue

            due_raw = task.get("due_datetime") or task.get("due_date") or task.get("dueDate")

            project_name = (
                task.get("project", {}).get("title")
                or task.get("list", {}).get("title")
                or "Inbox"
            )

            # bucket = kanban column / section equivalent in Vikunja
            section_name = (
                task.get("bucket", {}).get("title")
                if task.get("bucket")
                else None
            )

            full_project_name = f"{project_name} › {section_name}" if section_name else project_name

            tasks.append({
                "id": task["id"],
                "title": task["title"],
                "due_date": due_raw,
                "priority": task.get("priority", 1),
                "project_name": full_project_name,
            })
        return tasks
    except Exception as e:
        logging.critical(f"Error occurred in get_vikunja_tasks: {e}")
        return []