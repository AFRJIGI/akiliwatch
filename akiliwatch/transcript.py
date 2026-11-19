import re

MAX_MESSAGES = 30
MAX_CHARS = 1500


def profile_of(message):
    return ", ".join(str(message.get(key) or "") for key in ("level", "subject", "mode") if message.get(key))


def transcript(items, mask=None, max_messages=MAX_MESSAGES, max_chars=MAX_CHARS):
    """Readable transcript. A '--- profile from here ---' line appears whenever the profile changes, so the
    judge never grades an early subject against the final profile."""
    lines, shown = [], None
    for message in items[-max_messages:]:
        profile = profile_of(message)
        if profile and profile != shown:
            lines.append(f"--- profile from here: {profile} ---")
            shown = profile
        who = "STUDENT" if message["direction"] == "inbound" else "TUTOR"
        text = re.sub(r"\s+", " ", str(message.get("text") or ""))
        if mask:
            text = mask(text)
        if len(text) > max_chars:
            text = text[:max_chars] + " [rest not copied for review]"
        lines.append(f"[{str(message.get('created_at', ''))[11:16]}] {who}: {text}")
    return "\n".join(lines)
