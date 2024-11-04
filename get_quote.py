import requests

def get_quote():
    url = "https://zenquotes.io/api/today"
    text = ""

    response = requests.get(url).json()

    text += "\n\n# Quote"
    text += f"\n{response[0]['q']}"
    text += f"\n- *{response[0]['a']}*"

    return text
