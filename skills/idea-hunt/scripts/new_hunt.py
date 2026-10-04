#!/usr/bin/env python3
"""Scaffold docs/idea-hunt-<slug>.md from the template (never overwrites)."""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "hunt-artifact.md"


def slugify(text: str) -> str:
    slug = re.sub(r"[\W_]+", "-", text.lower()).strip("-")
    if not slug:  # e.g. punctuation-only title: keep distinct titles on distinct files
        slug = "hunt-" + hashlib.sha1(text.encode()).hexdigest()[:8]
    return slug


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
