#!/usr/bin/env bash
#
# check-style.sh - Hold the line the 13 October 2026 brand review drew.
#
# That review found, across the reference files and playbooks, 98 filler
# intensifiers ("genuinely", "actually"), 15 corporate-register verbs
# ("leverage", "unlock"), five em-dash purge leftovers (" -word"), two
# "full stop" crutches and about 25 "the single most ..." superlatives. Three
# voice-pass PRs (#242, #243, #244) took every one of them out. Nothing stops
# the next content PR, or the weekly pipeline's applier, from putting them back
# one at a time, which is how the count got to 98 in the first place. This
# script fails CI when a new one appears, the same way check-footers.sh fails
# on a lost footer.
#
# What it checks, on prose only (fenced code blocks, inline code spans, HTML
# comments and YAML frontmatter are stripped first, so a KQL `summarize` or a maintainer note
# does not count):
#   - em dash or en dash (the repo rule is a straight dash)
#   - filler intensifiers: genuinely, actually, simply, truly, really
#   - "percent" as a word (write %), "full stop"
#   - corporate-register verbs: leverage, unlock, streamline, empower (the
#     noun in "negotiation leverage" and "highest-leverage" is allowed)
#   - " -word": the residue an em-dash purge leaves behind
#   - "the single most / biggest / largest / best / worst": the superlative
#     form the CLAUDE.md sourcing rule says to cite, scope or drop
#   - thought-leadership cliches and rhetorical crutches ("new era",
#     "game changer", "here's the thing")
#
# What it does NOT check: British spelling (the catalogue files keep their
# imported American spelling by decision, 2026-10-13), numbers written as
# words, landing-sentence density, or anything that needs judgement. Those
# stay a review-time job; see "Content rules" in CLAUDE.md.
#
# Allowlist: scripts/check-style-allow.txt, one substring per line. A prose
# line that contains an allowed substring is skipped. Use it for a quoted
# title or a provider's own wording, never to wave through new prose.
#
# Files covered:
#   plugins/cloud-finops/skills/cloud-finops/references/*.md
#   plugins/cloud-finops/skills/cloud-finops/playbooks/*.md (README included)
#   plugins/cloud-finops/skills/cloud-finops/SKILL.md and POWER.md
#
# Usage:
#   ./scripts/check-style.sh    Report every finding; exit 1 if any.
#
# Wired into CI (.github/workflows/ci.yml) alongside the other drift guards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SKILL_DIR="plugins/cloud-finops/skills/cloud-finops"
ALLOWLIST="scripts/check-style-allow.txt"

for d in "$SKILL_DIR/references" "$SKILL_DIR/playbooks"; do
  if [[ ! -d "$d" ]]; then
    echo "FAIL: $d does not exist - the repo layout changed, update this script." >&2
    exit 1
  fi
done

# The matching lives in Python for one reason: stripping fenced code blocks,
# HTML comments and frontmatter reliably is a state machine, and a state
# machine in awk is harder to read than the patterns it protects.
python3 - "$SKILL_DIR" "$ALLOWLIST" <<'PY'
import re
import sys
from pathlib import Path

skill_dir = Path(sys.argv[1])
allow_path = Path(sys.argv[2])

allow = []
if allow_path.exists():
    allow = [
        line.rstrip("\n")
        for line in allow_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

CHECKS = [
    ("em or en dash (use a straight dash)", re.compile(r"[—–]")),
    ("filler intensifier", re.compile(r"\b(genuinely|actually|simply|truly|really)\b", re.I)),
    ("'percent' as a word (write %)", re.compile(r"\bpercent\b", re.I)),
    ("'full stop' crutch", re.compile(r"\bfull stop\b", re.I)),
    (
        "corporate-register verb",
        re.compile(
            r"\b(leverages|leveraged|leveraging|unlocks?|unlocked|unlocking|"
            r"streamlines?|streamlined|streamlining|empowers?|empowered|empowering)\b"
            r"|(?:^|[-*:.]\s+|\bto\s+)[Ll]everage\b",
            re.I,
        ),
    ),
    ("dash residue ' -word' (missing space after the dash)", re.compile(r"[A-Za-z,] -[A-Za-z]")),
    (
        "'the single most ...' superlative (cite, scope or drop)",
        re.compile(r"\bthe single (most|biggest|largest|best|worst)\b", re.I),
    ),
    (
        "cliche or rhetorical crutch",
        re.compile(
            r"\b(new era|paradigm shift|game[- ]?changer|game[- ]?changing|"
            r"here's the thing|the truth is|let that sink in)\b",
            re.I,
        ),
    ),
]

files = sorted(skill_dir.glob("references/*.md")) + sorted(skill_dir.glob("playbooks/*.md"))
for name in ("SKILL.md", "POWER.md"):
    p = skill_dir / name
    if p.exists():
        files.append(p)

if not files:
    print(f"FAIL: no content files found under {skill_dir}", file=sys.stderr)
    sys.exit(1)

findings = 0
for path in files:
    text = path.read_text(encoding="utf-8")
    # Drop HTML comments first: they can span lines and hold maintainer notes.
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    lines = text.split("\n")
    in_code = False
    in_front = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if i == 1 and stripped == "---":
            in_front = True
            continue
        if in_front:
            if stripped == "---":
                in_front = False
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if any(a in line for a in allow):
            continue
        # Inline code (`az vm list -d`, `nvidia-smi -i 0`) is not prose: drop the
        # spans before matching, keep the original line for the snippet.
        prose = re.sub(r"`[^`]*`", "x", line)
        for label, rx in CHECKS:
            m = rx.search(prose)
            if m:
                findings += 1
                snippet = line.strip()
                if len(snippet) > 110:
                    start = max(0, m.start() - 40)
                    snippet = "..." + line[start:start + 100].strip() + "..."
                print(f"{path}:{i}: {label}: {snippet}", file=sys.stderr)

if findings:
    print("", file=sys.stderr)
    print(
        f"FAIL: {findings} style finding(s) in prose. Rewrite the sentence; add a line to\n"
        f"      {allow_path} only for a quoted title or a provider's own wording.\n"
        f"      Rules: CLAUDE.md, 'Content rules'.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"OK: {len(files)} content files, no style findings in prose.")
PY
