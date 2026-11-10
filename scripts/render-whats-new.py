#!/usr/bin/env python3
"""Render the "what changed" digest from the list of provider changes.

`scripts/provider-changes.yaml` holds one entry per provider or vendor change the
library applied after reading it on the provider's own page: its date, who made it,
what it changes on the bill, and the guide and section that carry the mechanics.
This script validates every entry and rewrites the block between two HTML markers
in `references/finops-whats-new.md`: the changes already scheduled, then one table
per month for the last 90 days before the file's `as_of` date. Older entries stay
in the YAML as the archive and leave the rendered digest on their own.

The window is counted from `as_of`, never from today's date, so the output is the
same on every machine and CI does not go red because time passed: the digest is as
fresh as its `as_of`, which the file prints for the reader. Same pattern as
scripts/business-coverage.sh and scripts/render-questions-readme.py: the data file
is the source of truth, the markdown is generated, and CI fails on a stale block.

Usage:
    python scripts/render-whats-new.py           Rewrite the block in the reference
    python scripts/render-whats-new.py --check   Exit 1 if the block is stale

Exit code 2 means the data file itself is wrong (the message says which entry).
Needs PyYAML (installed with the MCP server's dev extras).
"""
from __future__ import annotations

import datetime as dt
import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "plugins" / "cloud-finops" / "skills" / "cloud-finops"
DATA = REPO_ROOT / "scripts" / "provider-changes.yaml"
DIGEST = SKILL / "references" / "finops-whats-new.md"
START = "<!-- whats-new:start -->"
END = "<!-- whats-new:end -->"
WINDOW_DAYS = 90
MAX_CHANGE_CHARS = 320

# The vendors and bodies an entry may name. A closed list, so a typo ("Azur",
# "Google cloud") fails here instead of becoming a second provider in the digest.
PROVIDERS = (
    "AWS",
    "Azure",
    "Google Cloud",
    "OCI",
    "Microsoft",
    "Microsoft Fabric",
    "Oracle",
    "Anthropic",
    "OpenAI",
    "Databricks",
    "Snowflake",
    "GitHub",
    "Cursor",
    "Cognition",
    "DeepSeek",
    "Alibaba Cloud",
    "Moonshot AI",
    "Zhipu AI",
    "FinOps Foundation",
    "European Union",
)

MONTHS = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)  # fmt: skip
DATE_RE = re.compile(r"^(\d{4})-(\d{2})(?:-(\d{2}))?$")
HEADING_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
TRAILING_COUNT_RE = re.compile(r"\s*\(\s*\d+\s*\)\s*$")
WORD_RE = re.compile(r"[a-z0-9]+")
ALLOWED_KEYS = {"date", "provider", "service", "change", "file", "section", "source"}


def fail_run(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def key(text: str) -> str:
    """Heading text reduced the way scripts/check-questions.py reduces it."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(WORD_RE.findall(TRAILING_COUNT_RE.sub("", text).lower()))


def headings_of(path: Path) -> list[str]:
    out: list[str] = []
    fence: str | None = None
    for line in path.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n"):
        fence_match = FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            fence = marker if fence is None else (None if fence == marker else fence)
            continue
        if fence is not None:
            continue
        match = HEADING_RE.match(line)
        if match:
            out.append(match.group(1).strip())
    return out


def resolves(section: str, headings: list[str]) -> int:
    keys = [key(h) for h in headings]
    wanted = key(section)
    if wanted in keys:
        return 1
    return sum(1 for k in keys if wanted in k)


class When:
    """An entry's date: a day, or a month when the source gives no day."""

    def __init__(self, raw: object, label: str) -> None:
        if isinstance(raw, dt.date):
            raw = raw.isoformat()
        match = DATE_RE.match(str(raw))
        if not match:
            fail_run(f"{label}: date {raw!r} is not YYYY-MM-DD or YYYY-MM")
        self.year, self.month = int(match.group(1)), int(match.group(2))
        self.day = int(match.group(3)) if match.group(3) else None
        try:
            self.first = dt.date(self.year, self.month, self.day or 1)
        except ValueError:
            fail_run(f"{label}: date {raw!r} is not a real date")

    def is_after(self, as_of: dt.date) -> bool:
        """Scheduled: a day after as_of, or a whole month that has not started."""
        return self.first > as_of

    def sort_key(self) -> tuple[int, int, int]:
        # A month-only date sorts after the dated days of its month when listing
        # ahead, and after them too when listing newest first (see render()).
        return (self.year, self.month, self.day or 0)

    def short(self, with_year: bool) -> str:
        month = MONTHS[self.month - 1][:3]
        text = f"{self.day} {month}" if self.day else month
        return f"{text} {self.year}" if with_year else text


def load() -> tuple[dt.date, list[dict]]:
    try:
        import yaml
    except ImportError:
        fail_run("PyYAML is required (pip install pyyaml).")
    try:
        data = yaml.safe_load(DATA.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail_run(f"{DATA.name} is not valid YAML: {exc}")
    if not isinstance(data, dict) or "as_of" not in data or "entries" not in data:
        fail_run(f"{DATA.name} needs a top-level `as_of` date and an `entries` list")
    as_of = When(data["as_of"], "as_of")
    if as_of.day is None:
        fail_run("as_of must be a full date, YYYY-MM-DD")

    known: dict[str, Path] = {}
    for kind in ("references", "playbooks"):
        for path in (SKILL / kind).glob("*.md"):
            if path.name != "README.md":
                known[path.stem] = path
    headings: dict[str, list[str]] = {}
    seen: set[tuple[str, str, str]] = set()
    entries: list[dict] = []
    for position, entry in enumerate(data["entries"] or [], 1):
        label = f"entry {position}"
        if not isinstance(entry, dict):
            fail_run(f"{label}: not a mapping")
        unknown = set(entry) - ALLOWED_KEYS
        if unknown:
            fail_run(f"{label}: unknown key(s) {sorted(unknown)}")
        for required in ("date", "provider", "change", "file"):
            if not entry.get(required):
                fail_run(f"{label}: `{required}` is missing")
        label = f"entry {position} ({entry['provider']}, {entry['date']})"
        when = When(entry["date"], label)
        if entry["provider"] not in PROVIDERS:
            fail_run(f"{label}: provider {entry['provider']!r} is not in the list in {Path(__file__).name}")
        change = " ".join(str(entry["change"]).split())
        if len(change) > MAX_CHANGE_CHARS:
            fail_run(f"{label}: `change` is {len(change)} characters, over {MAX_CHANGE_CHARS}")
        if not change.endswith((".", "?", ")")):
            fail_run(f"{label}: `change` must be a sentence ending with a full point")
        if re.search(r"[–—]", change):
            fail_run(f"{label}: `change` carries an em or en dash; use a straight hyphen")
        if re.search(r"\bpercent\b", change, re.IGNORECASE):
            fail_run(f"{label}: `change` says 'percent'; write %")
        name = str(entry["file"])
        if name == DIGEST.stem or name not in known:
            fail_run(f"{label}: file {name!r} is not a reference or a runbook")
        section = entry.get("section")
        if section:
            if name not in headings:
                headings[name] = headings_of(known[name])
            hits = resolves(str(section), headings[name])
            if hits != 1:
                fail_run(f"{label}: section {section!r} matches {hits} headings in {name}.md")
        source = entry.get("source") or ""
        if source and not str(source).startswith("https://"):
            fail_run(f"{label}: source {source!r} is not an https URL")
        fingerprint = (str(entry["date"]), entry["provider"], change.lower())
        if fingerprint in seen:
            fail_run(f"{label}: the same change is listed twice")
        seen.add(fingerprint)
        entries.append(
            {
                "when": when,
                "provider": entry["provider"],
                "service": " ".join(str(entry.get("service") or "").split()),
                "change": change,
                "file": name,
                "kind": known[name].parent.name,
                "section": " ".join(str(section).split()) if section else "",
                "source": str(source),
            }
        )
    return as_of.first, entries


def cell(text: str) -> str:
    return text.replace("|", "\\|")


def row(entry: dict, with_year: bool) -> str:
    who = entry["provider"] + (f" ({entry['service']})" if entry["service"] else "")
    where = f"`{entry['file']}.md`" if entry["kind"] == "references" else f"`playbooks/{entry['file']}.md`"
    if entry["section"]:
        where += f', "{entry["section"]}"'
    if entry["source"]:
        where += f" · [source]({entry['source']})"
    return f"| {entry['when'].short(with_year)} | {cell(who)} | {cell(entry['change'])} | {cell(where)} |"


def long_date(day: dt.date) -> str:
    return f"{day.day} {MONTHS[day.month - 1]} {day.year}"


def render() -> tuple[str, dict[str, int]]:
    as_of, entries = load()
    floor = as_of - dt.timedelta(days=WINDOW_DAYS)
    scheduled = sorted((e for e in entries if e["when"].is_after(as_of)), key=lambda e: (e["when"].year, e["when"].month, e["when"].day or 32))
    recent = [e for e in entries if not e["when"].is_after(as_of) and e["when"].first >= floor.replace(day=1) and (e["when"].day is None or e["when"].first >= floor)]
    older = len(entries) - len(scheduled) - len(recent)

    lines = [
        START,
        "",
        f"**Digest as of {long_date(as_of)}:** {len(recent)} verified changes dated since "
        f"{long_date(floor)}, and {len(scheduled)} already scheduled after that date. A provider "
        f"announcement made after {long_date(as_of)} is not in this file.",
        "",
        "## Scheduled changes",
        "",
    ]
    if scheduled:
        lines += [
            f"Dates ahead of {long_date(as_of)}, soonest first.",
            "",
            "| When | Who | What is scheduled | Read more |",
            "|---|---|---|---|",
            *(row(e, with_year=True) for e in scheduled),
        ]
    else:
        lines.append(f"No change scheduled after {long_date(as_of)} is recorded.")

    months: dict[tuple[int, int], list[dict]] = {}
    for entry in recent:
        months.setdefault((entry["when"].year, entry["when"].month), []).append(entry)
    for year, month in sorted(months, reverse=True):
        rows = sorted(months[(year, month)], key=lambda e: e["when"].sort_key(), reverse=True)
        lines += [
            "",
            f"## {MONTHS[month - 1]} {year}",
            "",
            f"Changes dated {MONTHS[month - 1]} {year}, newest first.",
            "",
            "| Date | Who | What changed for the bill | Read more |",
            "|---|---|---|---|",
            *(row(e, with_year=False) for e in rows),
        ]
    lines += ["", END]
    return "\n".join(lines), {"recent": len(recent), "scheduled": len(scheduled), "older": older}


def main(argv: list[str]) -> int:
    check = "--check" in argv[1:]
    text = DIGEST.read_text(encoding="utf-8").replace("\r\n", "\n")
    start, end = text.find(START), text.find(END)
    if start == -1 or end == -1 or end < start:
        fail_run(f"{DIGEST.name} has no {START} / {END} markers in order.")
    block, counts = render()
    new_text = text[:start] + block + text[end + len(END) :]
    summary = f"{counts['recent']} recent, {counts['scheduled']} scheduled, {counts['older']} past the {WINDOW_DAYS}-day window"
    if new_text == text:
        print(f"OK: {DIGEST.name} is in sync with {DATA.name} ({summary}).")
        return 0
    if check:
        print(
            f"FAIL: {DIGEST.name} is stale. Run `python scripts/render-whats-new.py` and "
            "commit the reference.",
            file=sys.stderr,
        )
        return 1
    DIGEST.write_text(new_text, encoding="utf-8", newline="\n")
    print(f"{DIGEST.name} rewritten from {DATA.name} ({summary}).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
