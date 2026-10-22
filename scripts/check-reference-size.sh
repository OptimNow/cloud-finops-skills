#!/usr/bin/env bash
#
# check-reference-size.sh - keep each file of the skill inside a token budget.
#
# The skill loads in stages: SKILL.md on every activation, then one reference
# or playbook per routed question. The cost a user pays per answer is therefore
# set by the size of the file a question lands on, not by the size of the
# library. A reference that keeps absorbing additions makes every question
# routed to it dearer, and makes the relevant paragraph harder to find.
#
# The library grew by about 20% between 10 and 22 October 2026 (1.33 MB to
# 1.60 MB of references and playbooks), mostly through additions to existing
# files, and nothing in CI showed which files were carrying it.
#
# Tokens are estimated as characters / 4, the same CHARS_PER_TOKEN the MCP
# server uses for the approx_tokens hint it serves (mcp_server/src/
# cloud_finops_mcp/metadata.py), so the two numbers agree.
#
# Budgets:
#   - references and playbooks: warn above 15,000 tokens, fail above 30,000;
#   - SKILL.md (loaded every session): warn above 6,000, fail above 8,000.
#
# A warning is the signal to split the file by question or prune it in the
# same PR; it does not block. The failure ceilings sit above the largest file
# at the time of writing (finops-aws-patterns.md, about 27,000 tokens), so they
# stop further growth without blocking the current library. Do not raise them
# to make a PR pass: split or prune the file instead.
#
# Usage: ./scripts/check-reference-size.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

python3 - "$REPO_ROOT" <<'PY'
import os
import sys
from pathlib import Path

root = Path(sys.argv[1])
skill = root / "plugins/cloud-finops/skills/cloud-finops"
CHARS_PER_TOKEN = 4

budgets = [
    ("SKILL.md", [skill / "SKILL.md"], 6_000, 8_000),
    ("reference", sorted((skill / "references").glob("*.md")), 15_000, 30_000),
    ("playbook", sorted((skill / "playbooks").glob("*.md")), 15_000, 30_000),
]

annotate = os.environ.get("GITHUB_ACTIONS") == "true"
warnings, failures, checked = [], [], 0

for kind, paths, warn, hard in budgets:
    for path in paths:
        checked += 1
        tokens = round(len(path.read_text(encoding="utf-8")) / CHARS_PER_TOKEN)
        rel = path.relative_to(root).as_posix()
        if tokens > hard:
            failures.append((rel, tokens, hard))
        elif tokens > warn:
            warnings.append((rel, tokens, warn))

for rel, tokens, warn in sorted(warnings, key=lambda w: -w[1]):
    msg = f"about {tokens:,} tokens, over the {warn:,} budget: split it by question or prune it"
    print(f"WARN: {rel} is {msg}")
    if annotate:
        print(f"::warning file={rel}::{msg}")

if failures:
    for rel, tokens, hard in failures:
        print(f"FAIL: {rel} is about {tokens:,} tokens, over the {hard:,} ceiling", file=sys.stderr)
    print(
        "\nEvery question routed to a file pays for the whole file. Split it into\n"
        "files a question can be routed to separately, or prune it; do not raise\n"
        "the ceiling. See CLAUDE.md \"Content rules\".",
        file=sys.stderr,
    )
    raise SystemExit(1)

print(f"OK: {checked} files checked, none over its ceiling ({len(warnings)} over budget).")
PY
