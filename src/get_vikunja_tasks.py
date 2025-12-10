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
            # Skip completed tasks
            if task.get("done"):
                continue

            # Prefer full datetime if present, else date-only
            due_raw = task.get("due_datetime") or task.get("due_date") or task.get("dueDate")
            tasks.append(
                {
                    "id": task["id"],
                    "title": task["title"],
                    "due_date": due_raw,           # always a string or None
                    "priority": task.get("priority", 1),
                }
            )
        return tasks
    except Exception as e:
        logging.critical(f"Error occurred in get_vikunja_tasks: {e}")
        return []
