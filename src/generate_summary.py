import logging

from openai import OpenAI

OPENAI_MODEL = "gpt-6-luna"
DEFAULT_LOCAL_LLM_BASE_URL = "http://localhost:11434/v1"


def generate_summary(text, api_key, provider="OPENAI", local_base_url="", local_model=""):
    try:
        if str(provider).upper() == "LOCAL":
            # Local LLMs (e.g. Ollama) expose an OpenAI-compatible API, so the same client is reused.
            # The API key is ignored by Ollama but required by the client.
            if not local_model:
                raise ValueError("LOCAL_LLM_MODEL must be set when SUMMARY_PROVIDER is LOCAL.")
            client = OpenAI(
                base_url=local_base_url or DEFAULT_LOCAL_LLM_BASE_URL,
                api_key=api_key or "local",
            )
            model = local_model
        else:
            client = OpenAI(api_key=api_key)
            model = OPENAI_MODEL

        completion = client.chat.completions.create(
            model=model,
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
