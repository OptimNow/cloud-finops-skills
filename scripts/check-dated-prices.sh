#!/usr/bin/env bash
#
# check-dated-prices.sh - A price in a playbook carries its date in the same paragraph.
#
# The 9 November 2026 probe smoke showed the model relaying a playbook's illustrative
# figures ("$32/month per NAT gateway, $0.045/GB") without the date, which sat in a
# trailing sentence of the same playbook. The dated-price pass of the same day moved
# every date next to its figure; this script keeps it there: in a playbook, any prose
# paragraph (a run of non-blank lines) that carries a currency figure must also carry
# a year. Fenced code blocks and the YAML frontmatter are skipped.
#
# Scope is the playbooks only. References carry scale examples ("a $50K/month
# anomaly") that are not prices, and the content rule lets one framing sentence at
# the top of a section date every figure under it, so the same rule there would flag
# paragraphs that are fine; see "Content rules" in docs/DESIGN.md.
#
# Usage:
#   ./scripts/check-dated-prices.sh            Report every undated paragraph; exit 1 if any.
#   ./scripts/check-dated-prices.sh <dir>      Same, over another folder of markdown files.
#
# Wired into CI (.github/workflows/ci.yml) alongside the other drift guards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PB_DIR="${1:-plugins/cloud-finops/skills/cloud-finops/playbooks}"

if [[ ! -d "$PB_DIR" ]]; then
  echo "FAIL: $PB_DIR does not exist - the repo layout changed, update this script." >&2
  exit 1
fi

python3 - "$PB_DIR" <<'PY'
import re
import sys
from pathlib import Path

pb_dir = Path(sys.argv[1])

# A currency figure: a $, € or £ followed by a digit, or a number followed by a
# three-letter currency code. "$VAR" in prose and "the $ amount" do not match.
FIG = re.compile(r"(?:\$|€|£)\s?\d|\d\s?(?:USD|EUR|GBP)\b")
YEAR = re.compile(r"\b(?:19|20)\d\d\b")
FENCE = re.compile(r"^[ \t]{0,3}(?:`{3,}|~{3,})")

files = sorted(p for p in pb_dir.glob("*.md") if p.name != "README.md")
findings = 0

for path in files:
    lines = path.read_text(encoding="utf-8").splitlines()

    # Skip the YAML frontmatter: an opening --- on line 1 up to the closing ---.
    start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start = i + 1
                break

    in_fence = False
    para: list[str] = []
    para_start = 0

    def flush() -> None:
        global findings
        if not para:
            return
        text = "\n".join(para)
        if FIG.search(text) and not YEAR.search(text):
            findings += 1
            first = next(l for l in para if FIG.search(l)).strip()
            print(f"{path}:{para_start}: price without a year in its paragraph: {first[:110]}", file=sys.stderr)

    for idx in range(start, len(lines)):
        line = lines[idx]
        if FENCE.match(line):
            flush(); para = []
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not line.strip():
            flush(); para = []
            continue
        if not para:
            para_start = idx + 1
        para.append(line)
    flush()

if findings:
    print("", file=sys.stderr)
    print(
        f"FAIL: {findings} paragraph(s) carry a price and no year. Put the date beside the\n"
        f"      figure (\"us-east-1 list rate read in November 2026\"), or drop the figure\n"
        f"      for the mechanic. Rule: docs/DESIGN.md, 'Content rules', 'Write mechanics,\n"
        f"      not price figures'.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"OK: {len(files)} playbooks, every paragraph that carries a price carries its year.")
PY
