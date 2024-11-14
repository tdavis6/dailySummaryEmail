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
        "priority": "❗",
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
        "important": "⭐",
        "urgent": "⚠️",
        "focus": "🔍",
        "celebrate": "🎉",
        "relax": "🌴",
        "self-care": "💆",
        "therapy": "🧠",
        "gratitude": "🙏",
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

    # Separate header from tasks, skipping any initial blank lines
    lines = text.strip().splitlines()
    header = None

    # Find the first non-blank line to use as the header
    for i, line in enumerate(lines):
        if line.strip():  # Non-blank line found
            header = line
            tasks = lines[i+1:]  # Remaining lines are tasks
            break

    # Helper function to replace keywords with corresponding emojis
    def replace_with_emoji(match):
        word = match.group()
        key = match.group().lower()
        emoji = emoji_map.get(key, emoji_map.get(key.rstrip('s'), ''))  # Handle plurals
        if key.endswith('s') and not emoji:
            emoji = emoji_map.get(key[:-1], '')
        logging.debug(f"Replacing '{word}' with '{emoji}' emoji.")
        return f"{word} {emoji}"

    # Apply emoji replacements for keywords
    for keyword in list(emoji_map.keys()) + [k + 's' for k in emoji_map.keys()]:
        tasks = [re.sub(rf"\b{keyword}\b", replace_with_emoji, task, flags=re.IGNORECASE) for task in tasks]

    updated_tasks = []

    # Define the regex to capture due date information in each task
    date_pattern = (
        r"due at (\d{1,2}:\d{2} (?:AM|PM)) on ([A-Za-z]+, [A-Za-z]+ \d{1,2}, \d{4})"
        r"|due on ([A-Za-z]+, [A-Za-z]+ \d{1,2}, \d{4})"
        r"|due at (\d{1,2}:\d{2} (?:AM|PM))"
    )

    for task in tasks:
        if task.isupper() or "conditions:" in task.lower():
            logging.info("Skipping header or line with 'Conditions:'.")
            continue

        match = re.search(date_pattern, task)
        due_date = datetime.now() if not match else datetime.strptime(match.group(2) or match.group(3), "%A, %B %d, %Y")

        days_late = (datetime.now() - due_date).days
        if days_late > 0:
            task += " ⚠️" if days_late <= 7 else " 🔥"

        updated_tasks.append(task)

    # Combine header and updated tasks into final output
    final_text = "\n".join([header] + updated_tasks) if header else "\n".join(updated_tasks)
    logging.debug("Completed add_emojis function.")
    return final_text
