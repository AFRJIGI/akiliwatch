"""Deterministic checks that need no AI judge: cheap, reproducible, and good for trends over time."""

import re
from collections import Counter

ANSWER_LETTER = re.compile(r"^\s*\(?([a-dA-D])\)?\s*[.!]?\s*$")
PRAISE = ("c'est exact", "exact", "bravo", "c'est juste", "c'est correct", "très bien", "tres bien", "excellent",
          "parfait", "bonne réponse", "correct", "that's right", "that is correct", "well done", "yes")
LATEX = re.compile(r"\\(?:frac|sqrt|times|cdot|left|right|begin|end)\b|\$[^$\n]{1,80}\$")
# "tu" is the expected register in most tutoring chats; flag formal address when the grid asks for informal.
FORMAL = re.compile(r"\b(?:vous|votre|vos)\b", re.I)


def option_offered(text, letter):
    return bool(re.search(rf"(^|\s)\(?{letter}[.)]\s", str(text or ""), flags=re.I | re.M))


def praised_letters(conversations):
    """Counter of the letters the tutor validated: the student answered with a single letter that was offered
    in the previous tutor message, and the next tutor message starts with praise. If one letter is the right
    answer most of the time, students learn to guess it."""
    counts = Counter()
    for items in conversations.values():
        for i, message in enumerate(items):
            match = ANSWER_LETTER.match(str(message["text"])) if message["direction"] == "inbound" else None
            if not match:
                continue
            letter = match.group(1).lower()
            before = next((m for m in reversed(items[:i]) if m["direction"] == "outbound"), None)
            after = next((m for m in items[i + 1:] if m["direction"] == "outbound"), None)
            if not before or not after or not option_offered(before["text"], letter):
                continue
            if str(after["text"]).strip().lower().lstrip("*_ ").startswith(PRAISE):
                counts[letter] += 1
    return counts


def two_choice_quizzes(conversations):
    """(quizzes with only a and b, quizzes offered)."""
    two = total = 0
    for items in conversations.values():
        for message in items:
            text = message["text"] if message["direction"] == "outbound" else ""
            if text and option_offered(text, "a") and option_offered(text, "b"):
                total += 1
                two += not option_offered(text, "c")
    return two, total


def tutor_messages(conversations):
    return [str(m["text"]) for items in conversations.values() for m in items if m["direction"] == "outbound"]


def summary(conversations, long_chars=850):
    """Share of tutor messages that are long, contain LaTeX, use formal address, are exact duplicates of the
    previous tutor message to the same student, or end without a question."""
    long_n = latex_n = formal_n = duplicate_n = no_question_n = total = 0
    for items in conversations.values():
        previous = None
        for message in items:
            if message["direction"] != "outbound":
                continue
            text = str(message["text"])
            total += 1
            long_n += len(text) > long_chars
            latex_n += bool(LATEX.search(text))
            formal_n += bool(FORMAL.search(text))
            duplicate_n += (previous is not None and text.strip() == previous)
            no_question_n += not text.rstrip().endswith("?")
            previous = text.strip()
    def pct(n):
        return round(100 * n / total, 1) if total else 0.0
    return {"tutor_messages": total, "long_pct": pct(long_n), "latex_pct": pct(latex_n), "formal_address_pct": pct(formal_n),
            "duplicate_pct": pct(duplicate_n), "no_question_pct": pct(no_question_n)}
