#!/usr/bin/env python3
"""Scaffold docs/idea-hunt-<slug>.md from the template (never overwrites)."""
import argparse
import datetime
import pathlib
import re
import sys

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "hunt-artifact.md"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "hunt"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("title", help="niche or workflow being hunted")
    ap.add_argument("--dir", default="docs", help="output directory (default: docs)")
    args = ap.parse_args()

    slug = slugify(args.title)
    out = pathlib.Path(args.dir) / f"idea-hunt-{slug}.md"
    if out.exists():
        print(f"exists, resuming: {out}")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    body = (
        TEMPLATE.read_text()
        .replace("{{TITLE}}", args.title)
        .replace("{{SLUG}}", slug)
        .replace("{{DATE}}", datetime.date.today().isoformat())
    )
    out.write_text(body)
    print(f"created: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
