import requests


def get_qotd():
    response = requests.get("https://zenquotes.io/api/today", timeout=10)
    response.raise_for_status()
    quote = response.json()[0]

    text = "\n\n# Quote of the Day"
    text += f"\n{quote['q']}"
    text += f"\n- *{quote['a']}*"

    return text
