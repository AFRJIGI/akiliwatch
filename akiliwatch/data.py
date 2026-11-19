"""Reading conversations from JSONL and grouping them into student conversations.

One JSON object per line:
  student_id   any stable identifier (phone number, user id...). Required.
  direction    "inbound" (student -> tutor) or "outbound" (tutor -> student). Required.
  text         message text ("[photo]", "[audio]" for media). Required.
  created_at   ISO 8601 timestamp. Required.
  subject, level, mode   optional: the profile chosen by the student at that moment.
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

REQUIRED = ("student_id", "direction", "text", "created_at")


def read_jsonl(path):
    messages = []
    with open(path, encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                message = json.loads(line)
            except ValueError as exc:
                raise ValueError(f"{path}:{number}: invalid JSON ({exc})") from exc
            missing = [key for key in REQUIRED if key not in message]
            if missing:
                raise ValueError(f"{path}:{number}: missing field(s) {', '.join(missing)}")
            if message["direction"] not in ("inbound", "outbound"):
                raise ValueError(f"{path}:{number}: direction must be inbound or outbound")
            messages.append(message)
    return messages


def since(messages, hours=None, start=None, now=None):
    """Keep messages from the last `hours`, and not older than `start` (ISO timestamp, UTC if no zone)."""
    now = now or datetime.now(timezone.utc)
    limit = None
    if hours:
        limit = now - timedelta(hours=hours)
    if start:
        parsed = datetime.fromisoformat(start)
        parsed = parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        limit = max(limit, parsed) if limit else parsed
    if not limit:
        return list(messages)
    kept = []
    for message in messages:
        stamp = datetime.fromisoformat(str(message["created_at"]).replace("Z", "+00:00"))
        stamp = stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
        if stamp >= limit:
            kept.append(message)
    return kept


def group(messages, min_student_messages=3, automatic_prefixes=()):
    """{student_id: [messages sorted by time]} for conversations with real work in them.
    Tutor messages that start with one of `automatic_prefixes` (welcome, onboarding...) do not count."""
    by_student = defaultdict(list)
    for message in messages:
        by_student[message["student_id"]].append(message)
    kept = {}
    for student, items in by_student.items():
        items.sort(key=lambda m: str(m["created_at"]))
        student_msgs = [m for m in items if m["direction"] == "inbound"]
        tutor_msgs = [m for m in items if m["direction"] == "outbound"
                      and not str(m["text"]).strip().startswith(tuple(automatic_prefixes) or ("\0",))]
        if len(student_msgs) >= min_student_messages and tutor_msgs:
            kept[student] = items
    return kept
