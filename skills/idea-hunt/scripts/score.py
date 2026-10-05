#!/usr/bin/env python3
"""Apply the idea-hunt Stage 3 kill-gates to a candidate slate.

Input JSON (file or stdin): a list of
  {"name": "...", "scores": {"painkiller": 0-2, "ai_native": 0-2, "reachable_owner": 0-2,
                             "urgency": 0-2, "buildable": 0-2, "moat": 0-2},
   "evidence": "optional note"}
Rule: any gate scored 0 rejects the candidate; total < 8/12 rejects it.
Exit code 0 always when input is valid; 2 on invalid input.
"""
import json
import sys

GATES = ["painkiller", "ai_native", "reachable_owner", "urgency", "buildable", "moat"]
MIN_TOTAL = 8


def evaluate(candidate: dict) -> dict:
    """Score one candidate against the gates, raising ValueError on malformed input."""
    if not isinstance(candidate, dict) or not isinstance(candidate.get("name"), str):
        raise ValueError(f"each candidate must be an object with a string 'name', got {candidate!r}")
    name = repr(candidate["name"])  # repr keeps every error message on one line
    scores = candidate.get("scores")
    if not isinstance(scores, dict):
        raise ValueError(f"{name}: 'scores' must be an object")
    missing = [g for g in GATES if g not in scores]
    if missing:
        raise ValueError(f"{name}: missing gates {missing}")
    for g in GATES:
        v = scores[g]
        if type(v) is not int or v not in (0, 1, 2):
            raise ValueError(f"{name}: {g} must be the integer 0, 1 or 2")
    total = sum(scores[g] for g in GATES)
    reasons = [f"hard-fail on {g}" for g in GATES if scores[g] == 0]
    if total < MIN_TOTAL:
        reasons.append(f"total {total}/12 below {MIN_TOTAL}")
    return {
        "name": candidate["name"],
        "total": total,
        "scores": scores,
        "survives": not reasons,
        "reasons": reasons,
    }


def evaluate_all(data: object) -> list:
    """Evaluate a non-empty JSON list of candidates, rejecting duplicate names."""
    if not isinstance(data, list) or not data:
        raise ValueError("input must be a non-empty JSON list")
    results = [evaluate(c) for c in data]
    seen = set()
    for r in results:
        if r["name"] in seen:
            raise ValueError(f"duplicate candidate name {r['name']!r}")
        seen.add(r["name"])
    return results


def render(results: list) -> str:
    """Render evaluated candidates as a ranked Markdown table with a survivor count."""
    ranked = sorted(results, key=lambda r: (not r["survives"], -r["total"]))
    head = "| Candidate | " + " | ".join(GATES) + " | Total | Verdict |"
    sep = "|" + "---|" * (len(GATES) + 3)
    rows = []
    for r in ranked:
        cells = " | ".join(str(r["scores"][g]) for g in GATES)
        verdict = "SURVIVES" if r["survives"] else "REJECTED: " + "; ".join(r["reasons"])
        name = r["name"].replace("\\", "\\\\").replace("|", "\\|")
        name = name.replace("\r", " ").replace("\n", " ")
        rows.append(f"| {name} | {cells} | {r['total']}/12 | {verdict} |")
    n = sum(r["survives"] for r in results)
    return "\n".join([head, sep, *rows, "", f"{n} of {len(results)} survive."])


def main() -> int:
    """Read candidates from a file or stdin, print the scored table, and return the exit code."""
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0
    try:
        if len(sys.argv) > 1:
            with open(sys.argv[1], encoding="utf-8") as f:
                raw = f.read()
        else:
            raw = sys.stdin.buffer.read().decode("utf-8")
        print(render(evaluate_all(json.loads(raw))))
    except (ValueError, OSError) as e:
        print("error: " + " ".join(str(e).split()), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
