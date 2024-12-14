import logging

from openai import OpenAI


def generate_summary(text, api_key):
    try:
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Write a 2-3 sentence summary of the user's inputted text. Do not include info"
                               "about the user's name or email address. Do not include info about the puzzle, "
                               "word of the day, or quote of the day. Only include the most important information."
                               "Only include weather information if it is abnormal for the location, or if there is a "
                               "severe weather warning. Focus on important tasks and events."
                               "Generate this summary in a way that the user can get a good grasp of their "
                               "day by only reading these 2-3 sentences. Ensure to use the same timing system as the content,"
                               "12hr or 24hr. ALso make sure to use imperial or metric, as seen in the content."
                               "Make sure that all events and tasks are in the correct timezone."
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            max_tokens=120,
        )

        return f"# Summary\n\n{completion.choices[0].message.content}\n\n"

    except Exception as e:
        logging.critical(f"Error occurred while generating summary: {e}")
        return None
