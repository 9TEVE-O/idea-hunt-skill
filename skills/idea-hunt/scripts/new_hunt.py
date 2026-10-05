#!/usr/bin/env python3
"""Scaffold docs/idea-hunt-<slug>.md from the template (never overwrites)."""
import argparse
import datetime
import hashlib
import pathlib
import re
import sys
import unicodedata

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "templates" / "hunt-artifact.md"
MAX_SLUG_BYTES = 100  # keeps "idea-hunt-<slug>-<id>.md" far below the 255-byte filename limit
MARKER = "<!-- idea-hunt-title-id: {} -->"


def normalize_title(title: str) -> str:
    """Return the title in NFC form with whitespace runs collapsed to single spaces."""
    return " ".join(unicodedata.normalize("NFC", title).split())


def title_id(title: str) -> str:
    """Return a stable SHA-256 hex id for a normalized title."""
    return hashlib.sha256(title.encode("utf-8")).hexdigest()


def slugify(text: str) -> str:
    """Return a filesystem-safe slug of letters, digits and combining marks, bounded in length."""
    text = unicodedata.normalize("NFC", text).lower()
    kept = [c if c.isalnum() or unicodedata.category(c).startswith("M") else "-" for c in text]
    slug = re.sub(r"-+", "-", "".join(kept)).strip("-")
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
    if not slug:  # e.g. punctuation-only title: keep distinct titles on distinct files
        return "hunt-" + digest
    if len(slug.encode("utf-8")) > MAX_SLUG_BYTES:
        cut = slug.encode("utf-8")[:MAX_SLUG_BYTES].decode("utf-8", errors="ignore")
        return cut.strip("-") + "-" + digest
    return slug


def render(title: str, slug: str, tid: str) -> str:
    """Return the template with the title, slug, date and title id filled in."""
    return (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{TITLE}}", title)
        .replace("{{SLUG}}", slug)
        .replace("{{DATE}}", datetime.date.today().isoformat())
        .replace("{{TITLE_ID}}", tid)
    )


def create_exclusive(path: pathlib.Path, body: str) -> bool:
    """Create path with body; return False, leaving it untouched, if it already exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8") as f:
            f.write(body)
    except FileExistsError:
        return False
    return True


def belongs_to(path: pathlib.Path, tid: str) -> bool:
    """Return True if the artifact at path was scaffolded for the title with this id."""
    return MARKER.format(tid) in path.read_text(encoding="utf-8", errors="replace")


def scaffold(title: str, directory: str) -> str:
    """Create or resume the artifact for title and return a one-line status message."""
    title = normalize_title(title)
    tid = title_id(title)
    slug = slugify(title)
    body = render(title, slug, tid)
    out = pathlib.Path(directory) / f"idea-hunt-{slug}.md"
    if create_exclusive(out, body):
        return f"created: {out}"
    if belongs_to(out, tid):
        return f"exists, resuming: {out}"
    alt = out.with_name(f"idea-hunt-{slug}-{tid[:8]}.md")
    if create_exclusive(alt, body):
        return f"note: {out} belongs to a different title; created {alt} instead"
    if belongs_to(alt, tid):
        return f"exists, resuming: {alt}"
    raise OSError(f"{alt} exists and belongs to a different title")


def main() -> int:
    """Parse arguments, scaffold the artifact, and return the process exit code."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("title", help="niche or workflow being hunted")
    ap.add_argument("--dir", default="docs", help="output directory (default: docs)")
    args = ap.parse_args()
    try:
        print(scaffold(args.title, args.dir))
    except OSError as e:
        print("error: " + " ".join(str(e).split()), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
