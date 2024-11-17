import requests
import logging


def get_vikunja_tasks(VIKUNJA_API_KEY, VIKUNJA_BASE_URL):
    headers = {
        "Authorization": f"Bearer {VIKUNJA_API_KEY}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.get(f"{VIKUNJA_BASE_URL}/api/v1/tasks/all", headers=headers)
        if response.status_code == 200:
            vikunja_data = response.json()
            # Structure the data to be similar to Todoist API response
            tasks = []
            for task in vikunja_data:
                # Extract and prefer full datetime when available
                due_datetime = task.get("due_datetime") or task.get("due_date")
                tasks.append(
                    {
                        "id": task["id"],
                        "title": task["title"],
                        "due_date": due_datetime,
                        "priority": task.get("priority", 1),
                        "url": f"{VIKUNJA_BASE_URL}/tasks/{task['id']}",
                    }
                )
            return tasks
        else:
            response.raise_for_status()
    except Exception as e:
        logging.critical(f"Error occurred in get_vikunja_tasks: {e}")
        return []