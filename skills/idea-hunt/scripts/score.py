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
    scores = candidate.get("scores", {})
    missing = [g for g in GATES if g not in scores]
    if missing:
        raise ValueError(f"{candidate.get('name', '?')}: missing gates {missing}")
    for g in GATES:
        if scores[g] not in (0, 1, 2):
            raise ValueError(f"{candidate.get('name', '?')}: {g} must be 0, 1 or 2")
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


def render(results: list) -> str:
    ranked = sorted(results, key=lambda r: (not r["survives"], -r["total"]))
    head = "| Candidate | " + " | ".join(GATES) + " | Total | Verdict |"
    sep = "|" + "---|" * (len(GATES) + 3)
    rows = []
    for r in ranked:
        cells = " | ".join(str(r["scores"][g]) for g in GATES)
        verdict = "SURVIVES" if r["survives"] else "REJECTED: " + "; ".join(r["reasons"])
        rows.append(f"| {r['name']} | {cells} | {r['total']}/12 | {verdict} |")
    n = sum(r["survives"] for r in results)
    return "\n".join([head, sep, *rows, "", f"{n} of {len(results)} survive."])


def main() -> int:
    if "-h" in sys.argv or "--help" in sys.argv:
        print(__doc__)
        return 0
    try:
        raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
        data = json.loads(raw)
        if not isinstance(data, list) or not data:
            raise ValueError("input must be a non-empty JSON list")
        print(render([evaluate(c) for c in data]))
    except (ValueError, OSError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
