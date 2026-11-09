#!/usr/bin/env python3
"""Check a private overlay against the public skill it builds on.

An overlay (docs/OVERLAYS.md) is a private skill folder that cites the public
reference files by section heading and never restates a mechanic. This script
is the mechanical half of that convention:

  1. SKILL.md frontmatter: a `name` that shadows no public file, a
     `description` that names the cloud-finops skill, a non-empty `overlay_of`.
  2. Every `overlay_of` entry names a public reference or playbook that exists,
     and every listed section matches an H2 or H3 heading of that file the way
     the connector's first tier for get_reference(section=) does: lower-case,
     punctuation set aside, a substring of the heading. The connector is more
     tolerant still, so a citation that passes here always resolves there.
  3. `questions`: four to eight, none in repository vocabulary, none already
     declared by a public file (a duplicate is a routing ambiguity).
  4. No sentence of ten words or more, in the body of SKILL.md or in any other
     .md file of the overlay, appears verbatim in a public reference or
     playbook. Wrapped prose is re-flowed first, so splitting a copied
     sentence over two lines does not hide it. A cited heading is exempt.
  5. No em dash, since the house style is straight dashes.

docs/overlay-template/ is the only overlay in this repository and CI runs the
check on it, so a public heading cannot be renamed without the template
following. Real overlays live outside the repository; their owners run the
check after every public release.

Usage:
    python scripts/check-overlay.py <overlay-dir> [--public <skill-dir>]

Exit codes: 0 clean, 1 findings, 2 cannot run (bad arguments, PyYAML missing).
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUBLIC = REPO_ROOT / "plugins" / "cloud-finops" / "skills" / "cloud-finops"

MIN_QUESTIONS, MAX_QUESTIONS = 4, 8
MIN_SENTENCE_WORDS = 10
# Words a question in the user's voice never contains (docs/DESIGN.md,
# "Reference-file frontmatter").
QUESTION_VOCABULARY = ("playbook", "reference", "runbook", "finops-")
EM_DASH = "—"
HEADING_RE = re.compile(r"^#{2,3}\s+(.+?)\s*$")
LIST_ITEM_RE = re.compile(r"^(?:[-*]|\d+\.)\s+")
# Code fences the way metadata._atx_headings sees them: backticks or tildes,
# indented up to three spaces, closed by the same marker.
FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")
# The connector's first matching tier for get_reference(section=).
TRAILING_COUNT_RE = re.compile(r"\s*\(\s*\d+\s*\)\s*$")
HEADING_WORD_RE = re.compile(r"[a-z0-9]+")
PUBLIC_SKILL_NAME = "cloud-finops"
SENTENCE_SPLIT_RE = re.compile(r"[.?!;:|]+")
PUNCT_RE = re.compile(r"[^\w\s]")
WS_RE = re.compile(r"\s+")


def fail_run(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(2)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Return (frontmatter, body); frontmatter is None when the file has none."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end == -1:
        return None, text
    body_start = text.find("\n", end + 4)
    body = text[body_start + 1 :] if body_start != -1 else ""
    return text[4:end], body


def load_yaml(fm_text: str, label: str) -> dict:
    try:
        import yaml
    except ImportError:
        fail_run("PyYAML is required (pip install pyyaml).")
    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        fail_run(f"{label}: frontmatter is not valid YAML: {exc}")
    return data if isinstance(data, dict) else {}


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


def heading_key(text: str) -> str:
    """Lower-case, trailing "(n)" count dropped, punctuation out, words joined by one space."""
    return " ".join(HEADING_WORD_RE.findall(TRAILING_COUNT_RE.sub("", text).lower()))


def normalise(text: str) -> str:
    """Lower-case, accent-fold, drop punctuation, collapse whitespace.

    Applied identically to overlay sentences and to the public corpus, so a
    copied sentence matches whatever its quotes, dashes or line breaks became.
    """
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = PUNCT_RE.sub(" ", text.lower())
    return WS_RE.sub(" ", text).strip()


def units_of(text: str) -> list[str]:
    """Re-flow wrapped prose so a copied paragraph is one unit, not one line.

    Markdown wraps at about 90 characters, so a copied sentence split over two
    lines would fall under the word threshold line by line. Headings, table
    rows and fences stand alone; a list item starts a unit and its indented
    continuation lines join it; blank lines end a unit.
    """
    units: list[str] = []
    buf: list[str] = []

    def flush() -> None:
        if buf:
            units.append(" ".join(buf))
            buf.clear()

    for line in text.split("\n"):
        stripped = line.strip()
        if not stripped:
            flush()
        elif stripped.startswith(("#", "|", "```")):
            flush()
            units.append(stripped)
        elif LIST_ITEM_RE.match(stripped):
            flush()
            buf.append(stripped)
        else:
            buf.append(stripped)
    flush()
    return units


def sentences_of(text: str) -> list[str]:
    out: list[str] = []
    for unit in units_of(text):
        for raw in SENTENCE_SPLIT_RE.split(unit):
            norm = normalise(raw)
            if norm and len(norm.split()) >= MIN_SENTENCE_WORDS:
                out.append(norm)
    return out


def question_texts(value: object, label: str, errors: list[str]) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if not isinstance(value, list):
        errors.append(f"{label}: `questions` must be a list")
        return []
    out: list[str] = []
    for item in value:
        if isinstance(item, str):
            out.append(item)
        elif isinstance(item, dict) and isinstance(item.get("q"), str):
            out.append(item["q"])
        else:
            errors.append(f"{label}: malformed question entry {item!r}")
    return out


class PublicFile:
    __slots__ = ("name", "headings", "questions", "norm_text")

    def __init__(self, name: str, headings: list[str], questions: list[str], norm_text: str):
        self.name = name
        self.headings = headings
        self.questions = questions
        self.norm_text = norm_text


def load_public(public_dir: Path) -> dict[str, PublicFile]:
    files: dict[str, PublicFile] = {}
    for sub in ("references", "playbooks"):
        for path in sorted((public_dir / sub).glob("*.md")):
            if path.name == "README.md":
                continue
            text = read(path)
            fm_text, body = split_frontmatter(text)
            fm = load_yaml(fm_text, f"{sub}/{path.name}") if fm_text is not None else {}
            questions = question_texts(fm.get("questions"), f"{sub}/{path.name}", [])
            files[path.stem] = PublicFile(path.stem, headings_of(body), questions, normalise(text))
    return files


def usage() -> int:
    print(__doc__.split("Usage:")[1].split("Exit codes")[0].strip(), file=sys.stderr)
    return 2


def main(argv: list[str]) -> int:
    args = argv[1:]
    public_dir = DEFAULT_PUBLIC
    if "--public" in args:
        at = args.index("--public")
        if at + 1 >= len(args):
            return usage()
        public_dir = Path(args[at + 1]).expanduser().resolve()
        del args[at : at + 2]
    if len(args) != 1 or args[0].startswith("-"):
        return usage()

    overlay_dir = Path(args[0]).expanduser().resolve()
    skill_md = overlay_dir / "SKILL.md"
    if not skill_md.is_file():
        fail_run(f"{overlay_dir} has no SKILL.md")
    if not (public_dir / "references").is_dir():
        fail_run(f"{public_dir} is not the public skill folder (no references/)")

    public = load_public(public_dir)
    heading_set = {normalise(h) for f in public.values() for h in f.headings}
    public_questions = {normalise(q): f.name for f in public.values() for q in f.questions}

    errors: list[str] = []
    fm_text, _body = split_frontmatter(read(skill_md))
    if fm_text is None:
        errors.append("SKILL.md: no YAML frontmatter")
        fm: dict = {}
    else:
        fm = load_yaml(fm_text, "SKILL.md")

    name = fm.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("SKILL.md: `name` is missing")
    elif name in public or name == PUBLIC_SKILL_NAME:
        errors.append(f"SKILL.md: `name` {name} shadows a public file or the public skill itself")

    description = fm.get("description")
    if not isinstance(description, str) or "cloud-finops" not in description:
        errors.append(
            "SKILL.md: `description` must say the overlay is used together with the "
            "cloud-finops skill"
        )

    cited_files = cited_sections = 0
    overlay_of = fm.get("overlay_of")
    if not isinstance(overlay_of, list) or not overlay_of:
        errors.append(
            "SKILL.md: `overlay_of` must list at least one public file with the sections cited"
        )
    else:
        for entry in overlay_of:
            if not isinstance(entry, dict) or not isinstance(entry.get("reference"), str):
                errors.append(f"SKILL.md: overlay_of entry {entry!r} needs a `reference` name")
                continue
            ref = entry["reference"]
            target = public.get(ref)
            if target is None:
                errors.append(
                    f"SKILL.md: overlay_of cites {ref}, which is not a public reference or playbook"
                )
                continue
            cited_files += 1
            sections = entry.get("sections")
            if not isinstance(sections, list) or not sections:
                errors.append(
                    f"SKILL.md: overlay_of {ref} lists no sections; cite at least one H2 or H3"
                )
                continue
            for wanted in sections:
                if not isinstance(wanted, str) or not wanted.strip():
                    errors.append(f"SKILL.md: overlay_of {ref} has a blank section entry")
                    continue
                if any(heading_key(wanted) in heading_key(heading) for heading in target.headings):
                    cited_sections += 1
                else:
                    available = "; ".join(target.headings)
                    errors.append(
                        f'SKILL.md: overlay_of {ref} cites "{wanted}", which matches no H2/H3 '
                        f"heading. Available: {available}"
                    )

    questions = question_texts(fm.get("questions"), "SKILL.md", errors)
    if "questions" not in fm:
        errors.append("SKILL.md: `questions` is missing (four to eight, in the user's words)")
    elif not MIN_QUESTIONS <= len(questions) <= MAX_QUESTIONS:
        errors.append(
            f"SKILL.md: {len(questions)} questions; the rule is {MIN_QUESTIONS} to {MAX_QUESTIONS}"
        )
    for question in questions:
        hits = [word for word in QUESTION_VOCABULARY if word in question.lower()]
        if hits:
            errors.append(
                f"SKILL.md: question uses repository vocabulary ({', '.join(hits)}): {question}"
            )
        owner = public_questions.get(normalise(question))
        if owner:
            errors.append(
                f"SKILL.md: question already declared by public file {owner}, a routing "
                f"ambiguity: {question}"
            )

    for md in sorted(overlay_dir.glob("*.md")):
        text = read(md)
        for lineno, line in enumerate(text.split("\n"), 1):
            if EM_DASH in line:
                errors.append(f"{md.name}:{lineno}: em dash; the house style is straight dashes")
        # SKILL.md's frontmatter is covered above (cited headings are exempt,
        # questions have their own duplicate check), so scan its body only.
        scan = split_frontmatter(text)[1] if md.name == "SKILL.md" else text
        seen: set[str] = set()
        for sentence in sentences_of(scan):
            if sentence in heading_set or sentence in seen:
                continue
            seen.add(sentence)
            for pub in public.values():
                if sentence in pub.norm_text:
                    errors.append(f'{md.name}: copied from public {pub.name}: "{sentence[:90]}"')
                    break

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(
            f"FAIL: {len(errors)} finding(s) in {overlay_dir.name}. The convention is "
            "docs/OVERLAYS.md.",
            file=sys.stderr,
        )
        return 1
    print(
        f"OK: {overlay_dir.name} builds on {cited_sections} section(s) of {cited_files} public "
        f"file(s), {len(questions)} questions, no copied sentence, no em dash."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
