# AkiliWatch

*Built by [AFRJIGI](https://afrjigi.com), the team behind **Akili**, an AI tutor on WhatsApp for students preparing the BEPC and the Baccalauréat in Côte d'Ivoire.*

A small, dependency-free toolkit to **audit the quality of an AI tutor that talks to students in a chat app**
(WhatsApp, Telegram, SMS, web chat). It was extracted from the daily quality control we run on
[Akili](https://afrjigi.com), an AI tutor for Ivorian students preparing the BEPC and the Baccalauréat.

It does two things:

1. **Automatic checks that need no AI**: is the right answer of your multiple-choice questions always "a"?
   Do replies leak LaTeX that WhatsApp cannot display? Does the tutor repeat the same message to a student?
   Is it too long for a phone? These numbers are cheap, reproducible and good for tracking trends.
2. **An AI judge with a teacher's grid**: a model reads a random sample of conversations and reports
   problems by type and severity (wrong subject, content error, student stuck, tutor doing the student's work...).
   Teachers only need to read the conversations that were flagged.

## Why

Small teams building tutors for low-resource, low-bandwidth settings rarely have an evaluation team. A tutor
that is "mostly fine" can still teach a wrong formula, loop on a student who says "after" (meaning "I'm eating"),
or always put the right answer in position (a). Reading every conversation does not scale; reading a daily
sample with a good grid does. In our own deployment the daily audit has caught real bugs almost every day since we started it.

## Quick start

```bash
git clone <this repository> && cd akiliwatch
python3 -m akiliwatch examples/sample_conversations.jsonl --n 4        # automatic checks only, no model needed
python3 -m akiliwatch examples/sample_conversations.jsonl --dump-prompts prompts/   # prompts to paste in any model
pip install google-genai
python3 -m akiliwatch my_conversations.jsonl --backend gemini-key --api-key $GEMINI_API_KEY --n 40
python3 -m akiliwatch my_conversations.jsonl --backend gemini-vertex --project my-gcp-project --since 2026-01-12T09:00
```

The report is written to `akiliwatch-report.md`. Run the tests with `python3 -m pytest tests`.

## Input format

One JSON object per line (see `examples/sample_conversations.jsonl`, all fictional):

```json
{"student_id": "any-stable-id", "direction": "inbound", "text": "solve 2x + 3 = 11",
 "created_at": "2026-01-12T16:03:00Z", "subject": "Maths", "level": "Grade 9", "mode": "study"}
```

`direction` is `inbound` (student to tutor) or `outbound`. `subject`, `level`, `mode` are optional but let the
judge grade each answer against the profile the student had *at that moment*.

## Grids

`grids/secondary_en.txt` and `grids/secondary_fr.txt` are the review grids. Edit them: they are plain text.
The most important lines are the "NOT a problem" ones. They tell the judge what good tutoring looks like
(for example, giving the full solution after two wrong tries is fine), and they cut false alarms.
Judges are noisy: treat the score as a trend, and have a teacher read the serious problems.

## Privacy

Student messages are personal data, often about minors. This kit:

- pseudonymises student ids (`--salt` keeps pseudonyms private) and masks phone numbers and e-mail addresses
  in message text before anything is sent to a model or written to a report;
- does not store anything outside the report file you choose.

Masking is not anonymisation. Names, schools or addresses typed by students are not removed. Get consent, tell
users how their conversations are used, and review any report before you share it. Never commit real
conversations or reports to a public repository.

## Limits

- The AI judge can be wrong, and a judge from the same model family as your tutor may be too kind. Use a
  different model when you can, and spot-check with teachers.
- The automatic checks are heuristics tuned on French and English chats.
- It audits quality, not learning outcomes. Pair it with real assessments.

## Licence

Copyright 2026 AFRJIGI LLC (see `NOTICE`). Code: Apache-2.0 (`LICENSE`). Review grids in `grids/`: CC BY 4.0 (`grids/LICENSE.md`).
Contributions, new grids (other subjects, languages, levels) and bug reports are welcome.
