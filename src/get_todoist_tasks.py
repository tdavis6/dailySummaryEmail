import logging
from todoist_api_python.api import TodoistAPI

def get_todoist_tasks(TODOIST_API_KEY):
    api = TodoistAPI(TODOIST_API_KEY)
    try:
        projects = {}
        for page in api.get_projects():
            for project in page:
                projects[project.id] = project.name

        sections = {}
        for page in api.get_sections():
            for section in page:
                sections[section.id] = section.name

        tasks = []
        for page in api.filter_tasks(query="(due before: tomorrow | deadline before: tomorrow) & (assigned to: me | !assigned)"):
            for task in page:
                project_name = projects.get(task.project_id, "Inbox")
                section_name = sections.get(task.section_id) if task.section_id else None
                task._project_name = f"{project_name} › {section_name}" if section_name else project_name
                tasks.append(task)
        return tasks
    except Exception as e:
        logging.critical(f"Error occurred in get_todoist_tasks: {e}")
        return []