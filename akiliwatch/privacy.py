"""Pseudonymisation and masking. Nothing here is perfect: always review output before sharing it."""

import hashlib
import re

PHONE = re.compile(r"(?<!\w)\+?\d[\d .\-()]{7,}\d(?!\w)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def pseudonym(identifier, salt=""):
    """Stable short id for a student (the same student gets the same id for a given salt)."""
    digest = hashlib.sha256(f"{salt}:{identifier}".encode()).hexdigest()
    return "s_" + digest[:8]


def mask_text(text):
    """Replace phone numbers and e-mail addresses inside message text."""
    text = EMAIL.sub("[email]", str(text or ""))
    return PHONE.sub("[phone]", text)
