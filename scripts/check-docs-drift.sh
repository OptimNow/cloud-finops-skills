#!/usr/bin/env bash
#
# check-docs-drift.sh - keep the hand-maintained doc listings in step with the
# reference files on disk.
#
# `check-llms-txt.sh` already gates llms.txt. The 2026-08 review (F24) noted
# that the rest of the PR checklist's doc-sync items rely on a human reading
# the checklist. This closes the one that actually enumerates every reference:
# the CLAUDE.md "Repository structure" tree.
#
# AGENTS.md deliberately does NOT enumerate references - it shows a truncated
# tree and points at CLAUDE.md for the full listing - so there is nothing there
# to drift, and it is intentionally not checked. If AGENTS.md ever starts
# listing individual reference files, extend this script to cover it.
#
# Three checks, the first two mirroring check-llms-txt.sh:
#   1. Every skills/cloud-finops/references/*.md appears in the CLAUDE.md tree.
#   2. Every reference filename in that tree block exists on disk.
#   3. Every skills/cloud-finops/playbooks/*.md appears in the catalogue table
#      of playbooks/README.md, and every catalogue entry exists on disk.
#
# Check 3 exists because SKILL.md and POWER.md carry representative examples
# only and defer to playbooks/README.md "for the full list". That deferral was
# dangling until August 2026 - the README had no list at all - so the catalogue
# is now gated the same way the CLAUDE.md tree is.
#
# Usage:
#   ./scripts/check-docs-drift.sh    Report drift; exit 1 if any is found.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

REF_DIR="skills/cloud-finops/references"
CLAUDE_MD="CLAUDE.md"
errors=0

# The reference entries in the CLAUDE.md tree are the lines indented under
# `└── references/`, i.e. they start with the tree prefix at that depth.
# Scoping to that block keeps top-level entries (fcp-coverage.md, README.md)
# from being mistaken for references.
# Match on the indent only. Two mawk (the Ubuntu default awk) constraints shape
# this: it does not support regex interval expressions, so `│ {7}` matches
# nothing; and it is byte-oriented, so a bracket expression over multibyte tree
# glyphs like `[├└]` becomes a set of stray bytes rather than a set of
# characters. A literal prefix of `│` plus seven spaces avoids both.
listed="$(awk '
  /└── references\/ / { inblock = 1; next }
  inblock && /^│       / { print; next }
  inblock { inblock = 0 }
' "$CLAUDE_MD" | grep -oE '[a-z0-9-]+\.md' | sort -u)"

if [[ -z "$listed" ]]; then
  echo "FAIL: could not find the references block in the $CLAUDE_MD tree." >&2
  echo "      The tree format changed - update this script to match." >&2
  exit 1
fi

# Check 1: every reference file appears in the tree.
for f in "$REF_DIR"/*.md; do
  base="$(basename "$f")"
  if ! grep -qx "$base" <<<"$listed"; then
    echo "MISSING: $base exists but is not in the $CLAUDE_MD structure tree" >&2
    errors=$((errors + 1))
  fi
done

# Check 2: every filename in the tree block points at a real file.
while IFS= read -r base; do
  [[ -f "$REF_DIR/$base" ]] || {
    echo "STALE: $CLAUDE_MD lists $base which does not exist in $REF_DIR" >&2
    errors=$((errors + 1))
  }
done <<<"$listed"

count="$(find "$REF_DIR" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' ')"
if [[ $errors -gt 0 ]]; then
  echo "FAIL: $errors CLAUDE.md sync error(s). Update the 'Repository structure' tree." >&2
  exit 1
fi
echo "OK: CLAUDE.md structure tree lists all $count references, no stale entries."

# ---- Check 3: playbooks/README.md catalogue ---------------------------------
PB_DIR="skills/cloud-finops/playbooks"
PB_README="$PB_DIR/README.md"

# Catalogue rows are markdown links of the form [slug](slug.md) in a table.
# Anchoring on the link target rather than the row shape keeps this tolerant of
# column changes while still requiring a real, clickable link per playbook.
catalogued="$(grep -oE '\]\([a-z0-9-]+\.md\)' "$PB_README" \
  | sed 's/^](//;s/)$//' | sort -u)"

if [[ -z "$catalogued" ]]; then
  echo "FAIL: no playbook links found in $PB_README." >&2
  echo "      SKILL.md and POWER.md defer to it for the full list, so the" >&2
  echo "      catalogue table must exist. Update this script if the format changed." >&2
  exit 1
fi

for f in "$PB_DIR"/*.md; do
  base="$(basename "$f")"
  [[ "$base" == "README.md" ]] && continue
  if ! grep -qx "$base" <<<"$catalogued"; then
    echo "MISSING: $base exists but is not in the $PB_README catalogue" >&2
    errors=$((errors + 1))
  fi
done

while IFS= read -r base; do
  [[ -f "$PB_DIR/$base" ]] || {
    echo "STALE: $PB_README lists $base which does not exist in $PB_DIR" >&2
    errors=$((errors + 1))
  }
done <<<"$catalogued"

pb_count="$(find "$PB_DIR" -maxdepth 1 -name '*.md' -type f -not -name 'README.md' | wc -l | tr -d ' ')"
if [[ $errors -gt 0 ]]; then
  echo "FAIL: $errors playbook catalogue sync error(s). Update $PB_README." >&2
  exit 1
fi
echo "OK: $PB_README catalogues all $pb_count playbooks, no stale entries."
