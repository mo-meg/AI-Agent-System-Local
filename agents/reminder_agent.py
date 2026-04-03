"""
Reminder agent — parses a natural-language reminder request,
extracts the time and content, persists it, and returns confirmation.

Examples handled:
  "remind me in 30 minutes to call John"
  "set a reminder tomorrow at 9am to review PR"
  "remind me at 15:00 to take pills"
"""
import re
from datetime import datetime, timedelta
from loguru import logger
from tools.ollama_client import query_ollama
from memory.store import add_reminder


_EXTRACT_PROMPT = """
Extract the reminder details from this text. Reply ONLY in this exact format:
WHEN: <ISO 8601 datetime or relative like "+30m", "+1h", "+1d", "today 09:00", "tomorrow 09:00">
WHAT: <what to remind about>

Text: {text}
Current time: {now}
"""


def _parse_relative(when_str: str) -> datetime | None:
    now = datetime.now()
    when_str = when_str.strip().lower()

    # Relative offsets: +30m, +2h, +1d
    m = re.match(r'\+(\d+)(m|h|d)$', when_str)
    if m:
        n, unit = int(m.group(1)), m.group(2)
        delta = {"m": timedelta(minutes=n), "h": timedelta(hours=n), "d": timedelta(days=n)}[unit]
        return now + delta

    # "today HH:MM" or "tomorrow HH:MM"
    for prefix, base in [("today ", now), ("tomorrow ", now + timedelta(days=1))]:
        if when_str.startswith(prefix):
            time_part = when_str[len(prefix):]
            try:
                t = datetime.strptime(time_part, "%H:%M")
                return base.replace(hour=t.hour, minute=t.minute, second=0)
            except ValueError:
                pass

    # ISO 8601 fallback
    try:
        return datetime.fromisoformat(when_str)
    except ValueError:
        return None


def run(user_id: int, text: str) -> str:
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    raw = query_ollama(_EXTRACT_PROMPT.format(text=text, now=now_str))

    when_str, what = "", ""
    for line in raw.splitlines():
        if line.startswith("WHEN:"):
            when_str = line.split(":", 1)[1].strip()
        elif line.startswith("WHAT:"):
            what = line.split(":", 1)[1].strip()

    if not when_str or not what:
        return "⚠️ Couldn't understand the reminder. Try: 'remind me in 1 hour to call mom'"

    fire_at = _parse_relative(when_str)
    if not fire_at:
        return f"⚠️ Couldn't parse the time: '{when_str}'"

    reminder = add_reminder(user_id=user_id, content=what, fire_at=fire_at)
    formatted = fire_at.strftime("%a %d %b at %H:%M")
    return f"⏰ Reminder set for **{formatted}**:\n_{what}_"
