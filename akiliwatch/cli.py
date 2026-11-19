"""python -m akiliwatch conversations.jsonl --grid grids/secondary_en.txt --n 40 --dump-prompts out/"""

import argparse
import random
from datetime import datetime, timezone
from pathlib import Path

from . import data, metrics, judge, privacy, report, transcript


def sample(conversations, n, seed):
    ids = sorted(conversations)
    random.Random(seed).shuffle(ids)
    return ids[:n]


def main(argv=None):
    parser = argparse.ArgumentParser(prog="akiliwatch", description="Audit chat-tutor conversations.")
    parser.add_argument("conversations", help="JSONL file (see akiliwatch/data.py for the format)")
    parser.add_argument("--grid", default=str(Path(__file__).resolve().parent.parent / "grids" / "secondary_en.txt"))
    parser.add_argument("--n", type=int, default=20, help="conversations to review")
    parser.add_argument("--hours", type=int, help="only the last N hours")
    parser.add_argument("--since", help="ISO time (UTC): ignore older messages, e.g. before a deployment")
    parser.add_argument("--salt", default="", help="secret salt for student pseudonyms (keep it private)")
    parser.add_argument("--seed", default=None, help="sampling seed (default: today's date)")
    parser.add_argument("--backend", choices=["gemini-vertex", "gemini-key", "none"], default="none")
    parser.add_argument("--model", default="gemini-2.5-flash")
    parser.add_argument("--project", help="Google Cloud project (gemini-vertex)")
    parser.add_argument("--api-key", help="Gemini API key (gemini-key)")
    parser.add_argument("--dump-prompts", metavar="DIR", help="write one prompt file per conversation (any model)")
    parser.add_argument("--out", default="akiliwatch-report.md")
    args = parser.parse_args(argv)

    now = datetime.now(timezone.utc)
    messages = data.since(data.read_jsonl(args.conversations), args.hours, args.since, now)
    conversations = data.group(messages)
    chosen = sample(conversations, args.n, args.seed or now.strftime("%Y-%m-%d"))
    grid = Path(args.grid).read_text(encoding="utf-8")
    print(f"{len(messages)} messages, {len(conversations)} conversations with real work, {len(chosen)} selected.")

    call = None
    if args.backend == "gemini-vertex":
        call = judge.gemini_backend(args.model, project=args.project)
    elif args.backend == "gemini-key":
        call = judge.gemini_backend(args.model, api_key=args.api_key)

    if args.dump_prompts:
        Path(args.dump_prompts).mkdir(parents=True, exist_ok=True)

    results = []
    for student in chosen:
        items = conversations[student]
        pid = privacy.pseudonym(student, args.salt)
        profile = transcript.profile_of(items[-1])
        text = transcript.transcript(items, mask=privacy.mask_text)
        if args.dump_prompts:
            (Path(args.dump_prompts) / f"{pid}.txt").write_text(judge.build_prompt(grid, profile, text), encoding="utf-8")
        if call is None:
            continue
        result, error = judge.judge_conversation(call, grid, profile, text)
        if result is None:
            print(f"  {pid}: judge failed ({error})")
            continue
        result.update({"student": pid, "profile": profile})
        results.append(result)
        print(f"  {pid}: {result.get('score')}/5, {len(result['problems'])} problem(s)")

    letters = metrics.praised_letters(conversations)
    two = metrics.two_choice_quizzes(conversations)
    text = report.render(results, now.strftime("%Y-%m-%d"), metrics.summary(conversations), letters, two)
    Path(args.out).write_text(text, encoding="utf-8")
    print("\n" + text + f"\n\nReport written to {args.out}")


if __name__ == "__main__":
    main()
