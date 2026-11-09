#!/usr/bin/env bash
#
# check-dated-prices.sh - A price in the library carries its date in the same paragraph.
#
# The 9 November 2026 probe smoke showed the model relaying a playbook's illustrative
# figures ("$32/month per NAT gateway, $0.045/GB") without the date, which sat in a
# trailing sentence of the same playbook. The dated-price pass of the same day moved
# every date next to its figure, first in the playbooks and then in the references;
# this script keeps it there: any prose paragraph (a run of non-blank lines) that
# carries a currency figure must also carry a year. Fenced code blocks and the YAML
# frontmatter are skipped.
#
# Three readings follow the content rule (docs/DESIGN.md, "Write mechanics, not price
# figures" and the provenance rule after it):
#   - A table is dated by the prose paragraph directly above it: the framing sentence
#     the content rule allows ("us-east-1 list rates read 9 November 2026:") dates every
#     row under it. A heading between the two does not count, so a table straight under
#     a heading needs its own framing line.
#   - A rounded magnitude ($50K, $3M, EUR 750M, "$1 million") is a scale, never a list
#     rate, and does not count as a price.
#   - A worked-example figure that reads like a rate ("a 20% increase on $50,000 is
#     $10,000") sits in scripts/check-dated-prices-allow.txt, one substring per line;
#     a paragraph that contains an allowed substring is not checked. A list price is
#     dated, never allowed.
#
# Usage:
#   ./scripts/check-dated-prices.sh                       Both folders; exit 1 on any finding.
#   ./scripts/check-dated-prices.sh --scope playbooks     One folder (or "references").
#   ./scripts/check-dated-prices.sh <dir> [<dir> ...]     Any folders of markdown files.
#
# Wired into CI (.github/workflows/ci.yml) alongside the other drift guards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SKILL_DIR="plugins/cloud-finops/skills/cloud-finops"
ALLOWLIST="scripts/check-dated-prices-allow.txt"

dirs=()
if [[ $# -eq 0 ]]; then
  dirs=("$SKILL_DIR/playbooks" "$SKILL_DIR/references")
elif [[ "$1" == "--scope" ]]; then
  case "${2:-}" in
    playbooks|references) dirs=("$SKILL_DIR/$2") ;;
    all) dirs=("$SKILL_DIR/playbooks" "$SKILL_DIR/references") ;;
    *) echo "usage: $0 [--scope playbooks|references|all] [<dir> ...]" >&2; exit 2 ;;
  esac
else
  dirs=("$@")
fi

for d in "${dirs[@]}"; do
  if [[ ! -d "$d" ]]; then
    echo "FAIL: $d does not exist - the repo layout changed, update this script." >&2
    exit 1
  fi
done

python3 - "$ALLOWLIST" "${dirs[@]}" <<'PY'
import re
import sys
from pathlib import Path

allow_path = Path(sys.argv[1])
dirs = [Path(d) for d in sys.argv[2:]]

allow = []
if allow_path.exists():
    allow = [
        line.rstrip("\n")
        for line in allow_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

# A currency figure: a $, EUR or GBP sign followed by a digit, or a number followed by a
# three-letter currency code. "$VAR" in prose and "the $ amount" do not match.
FIG = re.compile(r"(?:\$|€|£)\s?\d|\d\s?(?:USD|EUR|GBP)\b")
# A rounded magnitude is a scale, not a price: "$50K", "$3M", "EUR 750M", "$1 million".
MAG = re.compile(
    r"(?:\$|€|£)\s?\d[\d,.]*\s?(?:[kKMB]\b|bn\b|thousand\b|million\b|billion\b)"
)
YEAR = re.compile(r"\b(?:19|20)\d\d\b")
FENCE = re.compile(r"^[ \t]{0,3}(?:`{3,}|~{3,})")

files = []
for d in dirs:
    files += sorted(p for p in d.glob("*.md") if p.name != "README.md")
findings = 0


def is_table(para: list[str]) -> bool:
    return all(l.lstrip().startswith("|") for l in para)


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
    prev_text: str | None = None  # the paragraph flushed just before this one

    def flush() -> None:
        global findings, prev_text
        if not para:
            return
        text = "\n".join(para)
        stripped = MAG.sub(" ", text)
        if FIG.search(stripped) and not YEAR.search(text):
            dated_above = is_table(para) and prev_text is not None and YEAR.search(prev_text)
            allowed = any(a in text for a in allow)
            if not dated_above and not allowed:
                findings += 1
                first = next(l for l in para if FIG.search(MAG.sub(" ", l))).strip()
                print(
                    f"{path}:{para_start}: price without a year in its paragraph: {first[:110]}",
                    file=sys.stderr,
                )
        prev_text = text

    for idx in range(start, len(lines)):
        line = lines[idx]
        if FENCE.match(line):
            flush(); para = []
            prev_text = None
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
        f"      figure (\"us-east-1 list rate read in November 2026\"), in the sentence right\n"
        f"      above a table, or drop the figure for the mechanic. A worked example that is\n"
        f"      not a price goes in {allow_path}. Rule: docs/DESIGN.md, 'Content rules',\n"
        f"      'Write mechanics, not price figures'.",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"OK: {len(files)} files, every paragraph that carries a price carries its year.")
PY
