#!/usr/bin/env python3
"""Guard the question index: the `questions:` frontmatter of every reference and playbook.

The index is the routing surface the connector's `query` parameter and the
entry points' fallback row search, so a drift here is a routing defect. The
rules are the ones docs/DESIGN.md ("Reference-file frontmatter") sets:

  1. Every reference and playbook carries `questions:` with 4 to 8 entries,
     each a plain string or a mapping with `q` and optional `persona`,
     `section` and `also`; no other key.
  2. A question is written in the user's words: no "playbook", "reference",
     "runbook", "finops-" or " skill"; no em or en dash; "percent" as a word
     is out, the % sign is in.
  3. No question is declared by two files (a duplicate is a routing
     ambiguity). Comparison is lower-case, accent-folded, punctuation-free.
  4. A `section` resolves to exactly one H2/H3 heading of its own file: an
     exact match, or a unique substring, both compared the way the connector's
     first tier for get_reference(section=) compares.
  5. `persona` is one of the README roles or Executive; an entry with a
     persona is what the README's "What you can ask, by role" block is
     generated from (scripts/render-questions-readme.py).
  6. `also` names other references or playbooks that exist (the README links
     them beside the owner).
  7. At least one question per file is in French.

Usage:
    python scripts/check-questions.py          Report every finding; exit 1 if any.

Needs PyYAML (installed with the MCP server's dev extras), so CI runs it after
the pip install, like check-skill-description and check-overlay.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / "plugins" / "cloud-finops" / "skills" / "cloud-finops"

MIN_QUESTIONS, MAX_QUESTIONS = 4, 8
ALLOWED_KEYS = {"q", "persona", "section", "also"}
PERSONAS = {
    "FinOps lead",
    "Finance and procurement",
    "Engineering and platform",
    "AI product owner",
    "Executive",
}
VOCABULARY = ("playbook", "reference", "runbook", "finops-", " skill")
FRENCH_RE = re.compile(
    r"[^\x00-\x7f]|\b(quels?|quelles?|comment|nos|notre|pourquoi|faut-il|peut-on|combien|lesquels)\b",
    re.IGNORECASE,
)
HEADING_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
TRAILING_COUNT_RE = re.compile(r"\s*\(\s*\d+\s*\)\s*$")
WORD_RE = re.compile(r"[a-z0-9]+")


def fail_run(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def key(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(WORD_RE.findall(TRAILING_COUNT_RE.sub("", text).lower()))


def split_frontmatter(text: str) -> tuple[str | None, str]:
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    body_start = text.find("\n", end + 4)
    return text[4:end], (text[body_start + 1 :] if body_start != -1 else "")


def headings_of(body: str) -> list[str]:
    out: list[str] = []
    fence: str | None = None
    for line in body.split("\n"):
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


def resolve(section: str, headings: list[str]) -> int:
    keys = [key(h) for h in headings]
    wanted = key(section)
    if wanted in keys:
        return 1
    return sum(1 for k in keys if wanted in k)


def main() -> int:
    try:
        import yaml
    except ImportError:
        fail_run("PyYAML is required (pip install pyyaml).")

    files = sorted((SKILL / "references").glob("*.md")) + sorted(
        p for p in (SKILL / "playbooks").glob("*.md") if p.name != "README.md"
    )
    names = {p.stem for p in files}
    errors: list[str] = []
    seen: dict[str, str] = {}
    total = 0
    for path in files:
        label = f"{path.parent.name}/{path.name}"
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        fm_text, body = split_frontmatter(text)
        if fm_text is None:
            errors.append(f"{label}: no frontmatter")
            continue
        try:
            fm = yaml.safe_load(fm_text) or {}
        except yaml.YAMLError as exc:
            errors.append(f"{label}: frontmatter is not valid YAML: {exc}")
            continue
        value = fm.get("questions")
        if not isinstance(value, list) or not value:
            errors.append(f"{label}: no `questions:` list (every reference and playbook carries one)")
            continue
        if not MIN_QUESTIONS <= len(value) <= MAX_QUESTIONS:
            errors.append(f"{label}: {len(value)} questions; the rule is {MIN_QUESTIONS} to {MAX_QUESTIONS}")
        headings = headings_of(body)
        texts: list[str] = []
        for entry in value:
            if isinstance(entry, str):
                texts.append(entry)
                continue
            if not isinstance(entry, dict) or not isinstance(entry.get("q"), str):
                errors.append(f"{label}: malformed entry {entry!r}")
                continue
            texts.append(entry["q"])
            extra = set(entry) - ALLOWED_KEYS
            if extra:
                errors.append(f"{label}: unknown key(s) {sorted(extra)} on {entry['q'][:50]!r}")
            persona = entry.get("persona")
            if persona is not None and persona not in PERSONAS:
                errors.append(f"{label}: persona {persona!r} is not one of {sorted(PERSONAS)}")
            section = entry.get("section")
            if section is not None:
                hits = resolve(str(section), headings)
                if hits != 1:
                    errors.append(
                        f"{label}: section {section!r} resolves to {hits} heading(s); cite one H2/H3 "
                        f"of the file. Headings: {'; '.join(headings)}"
                    )
            also = entry.get("also")
            if also is not None:
                if not isinstance(also, list):
                    errors.append(f"{label}: `also` must be a list of file names")
                else:
                    for other in also:
                        if other not in names:
                            errors.append(f"{label}: `also` names {other!r}, which is not a reference or playbook")
                        if other == path.stem:
                            errors.append(f"{label}: `also` names the file itself")
        for question in texts:
            total += 1
            low = question.lower()
            hits = [w for w in VOCABULARY if w in low]
            if hits:
                errors.append(f"{label}: repository vocabulary ({', '.join(hits)}) in: {question}")
            if "—" in question or "–" in question:
                errors.append(f"{label}: em or en dash in: {question}")
            if re.search(r"\bpercent\b", low):
                errors.append(f"{label}: 'percent' as a word in: {question}")
            k = key(question)
            if k in seen and seen[k] != label:
                errors.append(f"{label}: question already declared by {seen[k]}: {question}")
            seen.setdefault(k, label)
        if texts and not any(FRENCH_RE.search(t) for t in texts):
            errors.append(f"{label}: no French question")

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(
            f"FAIL: {len(errors)} finding(s) in the question index. Rules: docs/DESIGN.md, "
            "\"Reference-file frontmatter\".",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(files)} files, {total} questions, no duplicate, every section resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
