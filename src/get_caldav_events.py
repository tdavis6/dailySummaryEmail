import json
import logging
from datetime import datetime, timedelta

from get_ical_events import parse_icalendar, is_event_today, convert_all_day_event

# Known CalDAV principal URLs for common providers.
# Notes per provider:
#
# icloud  – Use full Apple ID email as username.  Password must be an
#           App-Specific Password (Settings → Passwords & Security).
#           The base URL triggers a PROPFIND redirect to the user's
#           actual server (pXX-caldav.icloud.com); the caldav library
#           follows this automatically.
#
# google  – Endpoint updated to the current v2 API path.  Google still
#           supports HTTP Basic auth against this endpoint when the
#           account has 2FA disabled *or* via an App Password.  If the
#           account uses OAuth-only (Workspace enforce-OAuth policy),
#           supply an OAuth2 bearer token in the "password" field and
#           set "auth_type": "bearer" — the caldav library will use it.
#
# microsoft – Office 365 / Outlook.com.  Basic auth was fully deprecated
#             by Microsoft in October 2022 for consumer accounts and is
#             being phased out for M365 tenants.  Provide an OAuth2
#             access token in the "password" field and set
#             "auth_type": "bearer".  The principal URL below is the
#             correct RFC 6764 discovery base.
#
# webdav  – Generic / self-hosted (SOGo, Nextcloud, Radicale, …).
#           Provide "url" pointing at the user's principal or calendar
#           collection.  HTTP Basic auth is used by default.
_PROVIDER_URLS = {
    "icloud": "https://caldav.icloud.com",
    "google": "https://apidata.googleusercontent.com/caldav/v2/{username}/user/",
    "microsoft": "https://outlook.office365.com/dav/{username}/",
}


def _resolve_url(account_type, username, url_override):
    if url_override:
        return url_override
    template = _PROVIDER_URLS.get(account_type)
    if template:
        return template.format(username=username)
    return None


def _connect(account):
    """Return a list of calendars for the account, or raise on failure.

    Supports two auth modes via the optional "auth_type" account field:
      "basic"  (default) – HTTP Basic auth with username + password.
      "bearer"           – OAuth2 bearer token supplied in the "password"
                           field.  Required for Google Workspace accounts
                           with OAuth enforcement and Microsoft 365 after
                           basic-auth deprecation.
    """
    try:
        import caldav
    except ImportError:
        raise RuntimeError("caldav library is not installed. Add 'caldav' to requirements.txt.")

    account_type = account.get("type", "webdav").lower()
    username = account.get("username", "")
    password = account.get("password", "")
    auth_type = account.get("auth_type", "basic").lower()
    url = _resolve_url(account_type, username, account.get("url", ""))

    if not url:
        raise ValueError(
            f"No URL configured for CalDAV account type '{account_type}'. "
            "Provide a 'url' field for generic WebDAV accounts."
        )

    if auth_type == "bearer":
        headers = {"Authorization": f"Bearer {password}"}
        client = caldav.DAVClient(url=url, headers=headers)
    else:
        client = caldav.DAVClient(url=url, username=username, password=password)

    principal = client.principal()
    return principal.calendars()


def list_caldav_calendars(account):
    """Return [{url, name}, …] for every calendar in the account.

    Raises on connection/auth failure so the caller can surface the error.
    """
    calendars = _connect(account)
    return [
        {"url": str(cal.url), "name": cal.name or str(cal.url)}
        for cal in calendars
    ]


def _fetch_account_events(account, timezone):
    account_type = account.get("type", "webdav").lower()
    username = account.get("username", "")

    try:
        calendars = _connect(account)
    except Exception as e:
        logging.error(f"Could not connect to CalDAV account ({account_type}, {username}): {e}")
        return []

    # Determine which calendar URLs are enabled.
    # If account["calendars"] is present and non-empty, only include those marked enabled.
    configured = account.get("calendars")
    if isinstance(configured, list) and configured:
        enabled_urls = {c["url"] for c in configured if c.get("enabled", True)}
        if not enabled_urls:
            return []  # Everything explicitly disabled
    else:
        enabled_urls = None  # No filter — include all

    today = datetime.now(timezone).date()
    search_start = timezone.localize(datetime.combine(today, datetime.min.time()))
    search_end = search_start + timedelta(days=1)

    events = []
    for cal in calendars:
        if enabled_urls is not None and str(cal.url) not in enabled_urls:
            continue
        try:
            cal_events = cal.date_search(start=search_start, end=search_end, expand=False)
            cal_event_data = [e for event in cal_events for e in parse_icalendar(event.data)]
            logging.info(f"CalDAV calendar '{cal.name}' ({account_type}): {len(cal_event_data)} events fetched")
            events.extend(cal_event_data)
        except Exception as e:
            logging.warning(f"Error reading calendar from {account_type} account: {e}")

    result = []
    for event in events:
        try:
            event = convert_all_day_event(event, timezone)
            if is_event_today(event["start"], event["end"], timezone):
                result.append(event)
        except Exception as e:
            logging.warning(f"Error processing CalDAV event: {e}")

    return result


def get_caldav_events(caldav_accounts_json, timezone):
    """Fetch today's events from all authenticated CalDAV accounts.

    caldav_accounts_json: JSON string containing a list of account dicts:
        [
          {"type": "icloud",    "username": "user@icloud.com", "password": "app-password"},
          {"type": "google",    "username": "user@gmail.com",  "password": "app-password"},
          {"type": "microsoft", "username": "user@outlook.com","password": "password"},
          {"type": "webdav",    "url": "https://…/dav/calendars/user/",
                                "username": "user", "password": "pass"}
        ]
    """
    if not caldav_accounts_json:
        return []

    try:
        accounts = json.loads(caldav_accounts_json)
    except (json.JSONDecodeError, TypeError) as e:
        logging.error(f"CALDAV_ACCOUNTS is not valid JSON: {e}")
        return []

    if not isinstance(accounts, list):
        logging.error("CALDAV_ACCOUNTS must be a JSON array of account objects.")
        return []

    events = []
    for account in accounts:
        if not isinstance(account, dict):
            logging.warning(f"Skipping non-dict CalDAV account entry: {account}")
            continue
        events.extend(_fetch_account_events(account, timezone))

    return events
