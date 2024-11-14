import re
import logging
from datetime import datetime, timedelta

def add_emojis(text):
    """Adds emojis to individual tasks in the text based on lateness, with a default due date of today if not specified."""
    emoji_map = {
        # Meals
        "breakfast": "🍳",
        "lunch": "🍽️",
        "dinner": "🍽️",
        "snack": "🍿",
        "coffee": "☕",
        "tea": "🍵",
        "water": "💧",

        # Academic & Work
        "class": "📚",
        "study": "📖",
        "exam": "📝",
        "project": "🚀",
        "assignment": "📄",
        "homework": "📝",
        "presentation": "📊",
        "meeting": "📅",
        "deadline": "⏰",
        "work": "💼",
        "task": "✅",
        "priority": "⭐",
        "schedule": "🗓️",
        "appointment": "📅",
        "research": "🔍",
        "lecture": "🎓",
        "lab": "🔬",
        "experiment": "⚗️",
        "training": "📈",
        "goal": "🎯",

        # Personal Care & Health
        "exercise": "🏋️",
        "workout": "💪",
        "yoga": "🧘",
        "meditation": "🧘",
        "run": "🏃",
        "walk": "🚶",
        "doctor": "👨‍⚕️",
        "medicine": "💊",
        "pill": "💊",
        "vitamins": "💊",
        "dentist": "🦷",
        "shower": "🚿",
        "bath": "🛁",
        "sleep": "💤",
        "rest": "😴",

        # Events & Social
        "birthday": "🎂",
        "party": "🎉",
        "celebration": "🎊",
        "anniversary": "💍",
        "holiday": "🎈",
        "vacation": "🏖️",
        "travel": "✈️",
        "trip": "🌍",
        "concert": "🎵",
        "movie": "🎬",
        "dinner party": "🍲",

        # Daily & Household
        "cleaning": "🧹",
        "laundry": "🧺",
        "grocery": "🛒",
        "shopping": "🛍️",
        "cook": "👩‍🍳",
        "bake": "🍪",
        "garden": "🌱",
        "repair": "🔧",
        "maintenance": "🛠️",
        "bill": "💵",
        "pay": "💳",
        "organize": "📂",
        "declutter": "🗑️",
        "car": "🚗",
        "fuel": "⛽",

        # Technology & Communication
        "email": "📧",
        "message": "💬",
        "call": "📞",
        "phone": "📱",
        "zoom": "💻",
        "computer": "💻",
        "update": "🔄",
        "backup": "💾",
        "upload": "⬆️",
        "download": "⬇️",
        "wifi": "📶",
        "internet": "🌐",
        "website": "🔗",
        "link": "🔗",
        "password": "🔒",

        # Leisure & Entertainment
        "reading": "📖",
        "book": "📚",
        "puzzle": "🧩",
        "game": "🎮",
        "sports": "🏅",
        "hiking": "🥾",
        "cycling": "🚴",
        "swimming": "🏊",
        "photography": "📸",
        "painting": "🎨",
        "write": "✍️",
        "journal": "📓",
        "music": "🎶",
        "dance": "💃",

        # Emotions & Well-being
        "important": "❗",
        "urgent": "⚠️",
        "focus": "🔍",
        "celebrate": "🎉",
        "relax": "🌴",
        "self-care": "💆",
        "therapy": "🧠",
        "gratitude": "🙏",
        "goal": "🎯",
        "achievement": "🏆",
        "success": "🏆",
        "love": "❤️",
        "friend": "👫",
        "family": "👨‍👩‍👧‍👦",

        # Miscellaneous
        "question": "❓",
        "idea": "💡",
        "reminder": "🔔",
        "new": "🆕",
        "save": "💾",
        "charge": "🔋",
        "gift": "🎁",
        "list": "📝",
        "complete": "✅",
        "incomplete": "❌",
        "check": "✔️",
        "location": "📍",

        # Weather Conditions
        "sunny": "☀️",
        "clear": "🌞",
        "cloudy": "☁️",
        "overcast": "🌥️",
        "rain": "🌧️",
        "showers": "🌦️",
        "storm": "🌩️",
        "thunderstorm": "⛈️",
        "snow": "❄️",
        "hail": "🌨️",
        "windy": "💨",
        "fog": "🌫️",
        "mist": "🌫️",
        "drizzle": "🌦️",
        "frost": "❄️",
        "hot": "🔥",
        "cold": "🥶",
        "tornado": "🌪️",
        "hurricane": "🌀",
    }

    logging.debug("Starting add_emojis function.")

    # Helper function to replace keywords with corresponding emojis
    def replace_with_emoji(match):
        word = match.group()
        key = match.group().lower()
        emoji = emoji_map.get(key, emoji_map.get(key.rstrip('s'), ''))  # Handle plurals
        logging.debug(f"Replacing '{word}' with '{emoji}' emoji.")
        return f"{word} {emoji}"

    # Apply emoji replacements for keywords
    for keyword in list(emoji_map.keys()) + [k + 's' for k in emoji_map.keys()]:
        text = re.sub(rf"\b{keyword}\b", replace_with_emoji, text, flags=re.IGNORECASE)

    # Split the text into individual tasks (assuming tasks are separated by newlines)
    tasks = text.splitlines()
    updated_tasks = []

    # Define the regex to capture due date information in each task
    date_pattern = (
        r"due at (\d{1,2}:\d{2} (?:AM|PM)) on ([A-Za-z]+, [A-Za-z]+ \d{1,2}, \d{4})"  # "due at 3:00 PM on Wednesday, November 13, 2024"
        r"|due on ([A-Za-z]+, [A-Za-z]+ \d{1,2}, \d{4})"  # "due on Wednesday, November 13, 2024"
        r"|due at (\d{1,2}:\d{2} (?:AM|PM))"  # "due at 3:00 PM"
    )

    for task in tasks:
        # Skip lines that are headers or contain "Conditions:"
        if task.isupper() or task.endswith(':') or "conditions:" in task.lower():
            logging.info("Skipping header or line with 'Conditions:'.")
            continue

        match = re.search(date_pattern, task)

        # Parse due date if found; default to today otherwise
        if match:
            if match.group(2):  # Full date and time
                due_date_str = match.group(2)
                due_date = datetime.strptime(due_date_str, "%A, %B %d, %Y")
                logging.debug(f"Parsed due date with date and time for task: {due_date}")
            elif match.group(3):  # Date only
                due_date_str = match.group(3)
                due_date = datetime.strptime(due_date_str, "%A, %B %d, %Y")
                logging.debug(f"Parsed due date with date only for task: {due_date}")
            else:
                due_date = datetime.now()
                logging.debug("No specific due date found. Defaulting to today's date.")
        else:
            due_date = datetime.now()
            logging.debug("No date match found in task. Defaulting to today's date.")

        # Calculate days late
        days_late = (datetime.now() - due_date).days
        logging.debug(f"Days late calculated for task: {days_late}")

        # Append caution or fire emoji to overdue tasks only
        if days_late > 0:
            if days_late <= 7:
                task += " ⚠️"  # Up to 1 week late
                logging.info("Task is overdue by up to 1 week. Adding caution emoji.")
            else:
                task += " 🔥"  # More than 1 week late
                logging.info("Task is overdue by more than 1 week. Adding fire emoji.")

        # Append the processed task to the list of updated tasks
        updated_tasks.append(task)

    # Join all tasks back together into a single text with newlines
    final_text = "\n".join(updated_tasks)
    logging.debug("Completed add_emojis function.")
    return final_text
