import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from akiliwatch import data, judge, metrics, privacy, report, transcript
from akiliwatch.cli import main

SAMPLE = os.path.join(os.path.dirname(__file__), "..", "examples", "sample_conversations.jsonl")


def convs():
    return data.group(data.read_jsonl(SAMPLE))


def test_sample_loads_and_groups():
    assert len(convs()) == 4


def test_bad_jsonl_is_rejected():
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
        f.write('{"student_id": "x"}\n')
    try:
        data.read_jsonl(f.name)
        assert False
    except ValueError as exc:
        assert "missing" in str(exc)


def test_privacy():
    assert privacy.mask_text("call +1 555 010 0199 or a@b.com") == "call [phone] or [email]"
    assert privacy.pseudonym("+225 01", "s1") == privacy.pseudonym("+225 01", "s1")
    assert privacy.pseudonym("+225 01", "s1") != privacy.pseudonym("+225 01", "s2")


def test_metrics_find_planted_defects():
    c = convs()
    letters = metrics.praised_letters(c)
    assert letters["a"] >= 4 and letters["b"] == 0       # the right answer is always "a"
    two, total = metrics.two_choice_quizzes(c)
    assert total >= 3 and two >= 2
    m = metrics.summary(c)
    assert m["latex_pct"] > 0 and m["formal_address_pct"] > 0 and m["duplicate_pct"] > 0


def test_transcript_marks_profile_changes():
    items = convs()["student-01"]
    assert transcript.transcript(items).count("--- profile from here") == 1


def test_parse_result_variants():
    assert judge.parse_result('```json\n{"score": 4}\n```')["problems"] == []
    assert judge.parse_result("not json") is None


def test_cli_with_fake_judge(monkeypatch=None):
    out = os.path.join(tempfile.mkdtemp(), "r.md")
    fake = lambda prompt: json.dumps({"score": 3, "summary": "ok", "problems": [
        {"type": "pedagogy", "severity": "serious", "excerpt": "x", "explanation": "y"}]})
    original = judge.gemini_backend
    judge.gemini_backend = lambda *a, **k: fake
    try:
        main([SAMPLE, "--backend", "gemini-key", "--api-key", "x", "--n", "4", "--out", out, "--seed", "1"])
    finally:
        judge.gemini_backend = original
    text = open(out, encoding="utf-8").read()
    assert "Average score: 3.0" in text and "Serious problems to read (4)" in text


def test_dump_prompts_needs_no_model():
    d = tempfile.mkdtemp()
    main([SAMPLE, "--dump-prompts", d, "--n", "4", "--out", os.path.join(d, "r.md")])
    files = [f for f in os.listdir(d) if f.endswith(".txt")]
    assert len(files) == 4
    assert "+1 555" not in open(os.path.join(d, files[0]), encoding="utf-8").read()
