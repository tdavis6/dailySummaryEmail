# Daily Summary Email
![Last commit](https://img.shields.io/gitea/last-commit/tyler/dailySummaryEmail?gitea_url=https%3A%2F%2Fgit.tylerdavis.net)
![Open issues](https://img.shields.io/gitea/issues/open/tyler/dailySummaryEmail?gitea_url=https%3A%2F%2Fgit.tylerdavis.net)
![Open PR's](https://img.shields.io/gitea/pull-requests/open/tyler/dailySummaryEmail?gitea_url=https%3A%2F%2Fgit.tylerdavis.net)

## Summary
A program that emails the user the weather, any tasks on their to-do list, their events, puzzles, a word of the day, a
quote of the day, and more at a designated time daily.
(Only Todoist and Vikunja are currently supported for tasks, but am open to adding more.
Feel free to request any todo app with an issue. Events can come from webcal/ICS links or CalDAV accounts.)

To change the time of day that the email is sent, use the MINUTE and HOUR environment variables. 
All times should be in 24hr (0-23 for hours, 0-59 for minutes) time.

At any time, you may trigger an email send through the Web UI or via the API (see `API_TOKEN` below).

If you have any specific questions or issues setting it up, please feel free to create an issue here.
While I will try my best to respond quickly, I can make no guarantees on time nor a guaranteed solution, 
but I will try my best.

Please note, I am a novice developer and LLM's were consulted for some of the inner workings (namely calendar parsing
and the web UI).

## Setup

Run this in Docker, using the provided `docker-compose.yml`. Use the `.env.example` as a guideline for the `.env` file.

The app will not start unless these are set in the `.env` file (or already saved in `data/config.json`):
- `ENCRYPTION_KEY`, `PASSWORD` and `SECRET_KEY`
- The mail settings: `RECIPIENT_EMAIL`, `RECIPIENT_NAME`, `SENDER_EMAIL`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `SMTP_HOST` and `SMTP_PORT`
- A location (`ADDRESS`, or `LATITUDE` and `LONGITUDE`) or a `TIMEZONE`

Everything else is optional and can be added later in the web UI, which you log into with `PASSWORD`. Settings saved in
the web UI are stored in `data/config.json` (mounted from `./data` in `docker-compose.yml`) and take precedence over the
`.env` file on later starts. Once a setting is saved there, you may remove it from `.env`. Passwords and API keys are
encrypted in that file, and the web UI only ever shows them as `********`; leave that placeholder as-is to keep the
saved value.

The package tagged `latest` contains the latest stable release, while the package tagged `latest-dev` contains the latest development release, ignoring all stable releases.

The branch `stable` is the stable branch, while all development occurs on `dev`. Therefore, `dev` is considered the default branch.

## Environment Variables
See .env.example for an example .env file.

- RECIPIENT_EMAIL: The recipient's email
- RECIPIENT_NAME: The name that the email is addressed to
- SENDER_EMAIL: The sending email
- SMTP_USERNAME: The username of the sending account on the SMTP server
- SMTP_PASSWORD: The password of the sending account on the SMTP server
- SMTP_HOST: The host of the SMTP server (e.g. smtp.gmail.com)
- SMTP_PORT: The port of the SMTP server. Use 465 (SSL); this is currently the only supported port.
- OPENAI_API_KEY: Your OpenAI API key. Used to generate a short summary of the email. Not required when using a local LLM.
- SUMMARY_PROVIDER: OPENAI or LOCAL. Which LLM generates the summary. LOCAL uses a self-hosted, OpenAI-compatible server such as Ollama. (defaults to OPENAI)
- LOCAL_LLM_BASE_URL: The OpenAI-compatible base URL of your local LLM server. Only used when SUMMARY_PROVIDER is LOCAL. (defaults to http://localhost:11434/v1, Ollama's default)
- LOCAL_LLM_MODEL: The model name to use on your local LLM server (e.g. llama3.2). Required when SUMMARY_PROVIDER is LOCAL.
- ENABLE_SUMMARY: True or False. Toggle for if a summary should be generated. (defaults to False)
- ENABLE_EMOJIS: True or False. Toggle for if the summary should have emojis interpolated within it. (defaults to False)
- UNIT_SYSTEM: METRIC or IMPERIAL. (defaults to metric)
- TIME_SYSTEM: 24HR or 12HR. (defaults to 24HR)
- LATITUDE: The latitude you wish to use for the weather and timezone.
- LONGITUDE: The longitude you wish to use for the weather and timezone.
- ADDRESS: The address of which the weather and timezone should be used. (Use quotes). Ignored if LATITUDE and LONGITUDE are set.
- WEATHER: True or False. Enables weather. (defaults to false)
- TODOIST_API_KEY: Your Todoist API key
- VIKUNJA_API_KEY: Your Vikunja API key
- VIKUNJA_BASE_URL: Your Vikunja base url
- WEBCAL_LINKS: Link(s) for webcal or ics calendars of which the events should appear in the email. Use one string,
  separated by commas. Do not use quotes. Only events happening today are included.
- CALDAV_ACCOUNTS: CalDAV accounts (iCloud, Google, Microsoft, or any generic WebDAV server such as Nextcloud) whose
  events should appear in the email. This is easiest to manage in the web UI, which can list each account's calendars so
  you can choose which to include. If set through `.env`, it is a JSON array on one line, for example
  `[{"type": "icloud", "username": "you@icloud.com", "password": "app-specific-password"}]`. `type` is one of `icloud`,
  `google`, `microsoft` or `webdav`; `webdav` also needs a `url`. For iCloud and Google, use an app-specific password.
  For Google Workspace and Microsoft 365 accounts that no longer allow passwords, put an OAuth2 access token in
  `password` and add `"auth_type": "bearer"`.
- RSS_LINKS: Link(s) for rss feeds of which the entries should appear in the email. Use one string, separated by commas.
  Do not use quotes. Only entries published in the last 24 hours are included.
- PUZZLES: True or False. Enables puzzles. (defaults to false)
- PUZZLES_ANSWERS: True or False. Enables puzzle answers. Overridden by False on PUZZLES. (defaults to false)
- WOTD: True or False. Enables the Word of the Day. (defaults to false)
- QOTD: True or False. Enables the Quote of the Day. (defaults to false)
- HOUR: The hour to send the email, 0-23. (defaults to 6)
- MINUTE: The minute to send the email, 0-59. (defaults to 0)
- DISABLE_SCHEDULE: True or False. Disables the automatic scheduled send. Useful when triggering via the API instead. (defaults to False)
- TIMEZONE: Timezone as a string, e.g. `America/New_York`. Only used when no latitude and longitude or address is given;
  otherwise the timezone is worked out from the location. Ensure that it is spelt correctly.
- LOGGING_LEVEL: Level for logging (defaults to INFO). Options: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'.
- ENCRYPTION_KEY: Fernet encryption key for passwords and API keys. One way to generate them could be ```python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"```
- PASSWORD: Web UI password. After 5 failed login attempts in 5 minutes, further attempts from that address are blocked until the window passes.
- SECRET_KEY: Random string. Used to sign the session cookies of the Web UI.
- API_TOKEN: Secret token that enables the `POST /api/trigger-email` and `POST /api/trigger-email-with-location` endpoints. When set, email sends can be triggered externally with `Authorization: Bearer <token>` — no web session required. If unset, the endpoints return 403.
  `trigger-email-with-location` takes a JSON body with numeric `latitude` and `longitude` and builds that email (weather, timezone, events) for that location instead of the configured one.

NOTE: Weather needs either a coordinate pair or an address. Without a location, `TIMEZONE` is used for dates and times.

## OpenAI Integration
The OpenAI Integration allows a 2-3 sentence summary of the email near the top.

The summary uses the model named by `OPENAI_MODEL` in `src/generate_summary.py` (currently `gpt-6-luna`). It is not
configurable through environment variables. Output is limited to 120 tokens per day, and the input is the day's weather,
tasks and events, so it is typically around 1,400 tokens per day and more for very full days. Only the weather, tasks and
events are sent to OpenAI; the other sections are not part of the summary.

Prices change, so this README does not quote a figure. You can estimate your cost from the
[OpenAI pricing page](https://openai.com/api/pricing/) using this formula:

$\text{Cost per year} = 365 \times \left(\frac{\text{input tokens per day}}{1{,}000{,}000} \times P_{in} + \frac{\text{output tokens per day}}{1{,}000{,}000} \times P_{out}\right)$

where $P_{in}$ and $P_{out}$ are the model's prices in USD per 1M input and output tokens. For example, 1,400 input
tokens and 120 output tokens per day is 511,000 input and 43,800 output tokens per year.

### Setup Instructions
To set this up, make an account with OpenAI, or log in with one, and get your API key. Note: The OpenAI API is a different
product that ChatGPT, ChatGPT Plus does not grant access to the OpenAI API.

## Local LLM Integration (Ollama)
Instead of OpenAI, the summary can be generated by a self-hosted LLM. This is free to run and keeps your email
content on your own hardware. Any server with an OpenAI-compatible API works (Ollama, LM Studio, llama.cpp server,
vLLM, LocalAI, etc.), but Ollama is the easiest to set up.

### Setup Instructions
1. Install [Ollama](https://ollama.com/) and pull a model, e.g. `ollama pull llama3.2`.
2. Set `SUMMARY_PROVIDER=LOCAL` and `LOCAL_LLM_MODEL=llama3.2` (or whichever model you pulled).
3. Set `LOCAL_LLM_BASE_URL` to your server's OpenAI-compatible endpoint (for Ollama, this ends in `/v1`):
   - Ollama on the Docker host: `http://host.docker.internal:11434/v1`. On Linux, also add the following to the
     service in `docker-compose.yml`, and make sure Ollama listens on more than localhost (`OLLAMA_HOST=0.0.0.0`):
     ```yaml
     extra_hosts:
       - "host.docker.internal:host-gateway"
     ```
   - Ollama in another container on the same Docker network: `http://ollama:11434/v1`
   - Ollama on another machine: `http://<ip-address>:11434/v1`

`OPENAI_API_KEY` is not needed for Ollama. If your local server requires an API key, put it in `OPENAI_API_KEY` and it
will be sent to the local server instead.

Summary quality depends on the model. Small models (3B parameters or less) can produce shorter or less accurate
summaries than OpenAI. Output is limited to 120 tokens, so "thinking" models may get cut off before they answer.

## Attribution
- Geocoding provided by [Nominatim](https://nominatim.org/).
- Weather data provided by [Open-Meteo](https://open-meteo.com/)
- Weather alerts provided by the [NWS API](https://www.weather.gov/documentation/services-web-api) (United States) and [MeteoAlarm](https://feeds.meteoalarm.org/) (Europe)
- Quotes provided by [ZenQuotes API](https://zenquotes.io/).
- Word of the Day provided by [Merriam-Webster](https://www.merriam-webster.com/word-of-the-day).

## Other Notes
- Versioning follows [semver](https://semver.org).
- If you want news articles, add their RSS feed as a feed. For example, the Wall Street Journal supplies RSS feeds, and 
other newspapers likely do too ([WSJ World News Feed](https://feeds.content.dowjones.io/public/rss/RSSWorldNews)).
  - I do not claim responsibility for any content in this feed. I do not support any particular newspaper, nor wish to make any
political comments on any work. This feed was chosen because it was shown to be potentially [close to the center of the political spectrum](https://www.allsides.com/news-source/wall-street-journal-media-bias). It is simply here as an example.