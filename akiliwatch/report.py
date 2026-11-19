from collections import Counter


def render(results, label, metrics=None, letters=None, two_choice=None):
    notes = [r["score"] for r in results if isinstance(r.get("score"), (int, float))]
    kinds = Counter(p.get("type") for r in results for p in r.get("problems", []))
    serious = [(r, p) for r in results for p in r.get("problems", []) if p.get("severity") == "serious"]
    lines = [f"# Tutor quality audit, {label}", "",
             f"Conversations reviewed: {len(results)}",
             f"Average score: {sum(notes) / len(notes):.1f} / 5" if notes else "Average score: -",
             f"Conversations without a problem: {sum(1 for r in results if not r.get('problems'))}", "",
             "## Problems by type"]
    lines += [f"- {k}: {v}" for k, v in kinds.most_common()] or ["- none"]
    lines += ["", f"## Serious problems to read ({len(serious)})"]
    for r, p in serious:
        lines.append(f"- {r['student']} ({r['profile']}) - {p.get('type')}: {p.get('explanation', '')}")
        if p.get("excerpt"):
            lines.append(f"  > {p['excerpt'][:300]}")
    lines += ["", "## All conversations"]
    for r in sorted(results, key=lambda r: r.get("score", 5)):
        lines.append(f"- {r.get('score', '?')}/5 {r['student']} ({r['profile']}): {r.get('summary', '')}")
    if metrics:
        lines += ["", "## Automatic checks (no AI judge)"]
        lines += [f"- {k}: {v}" for k, v in metrics.items()]
    if letters is not None:
        n = sum(letters.values())
        lines += ["", f"## Quiz answers: position of the correct option ({n} validated answers)"]
        lines += [f"- {x}: {letters[x]} ({100 * letters[x] / n:.0f} %)" for x in "abcd"] if n else ["- none"]
        if two_choice:
            lines.append(f"- quizzes with only 2 options: {two_choice[0]} of {two_choice[1]}")
    return "\n".join(lines)
