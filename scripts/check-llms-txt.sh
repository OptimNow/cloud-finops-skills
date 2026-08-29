#!/usr/bin/env bash
#
# check-llms-txt.sh - Keep llms.txt's "Key files" list in sync with the actual
# reference files on disk. This is the drift guard that replaces the old
# hand-bumped "N references" counts (removed across the repo in 2026-07):
# instead of trusting a number, we assert the list itself is complete and has
# no stale paths.
#
# Two checks:
#   1. Every skills/cloud-finops/references/*.md is listed in llms.txt.
#   2. Every references/*.md path mentioned in llms.txt actually exists
#      (catches stale paths left after a rename or restructure).
#
# Usage:
#   ./scripts/check-llms-txt.sh    Report drift; exit 1 if any is found.
#
# Wired into CI (.github/workflows/ci.yml) so a PR that adds a reference
# without listing it in llms.txt fails with a clear message.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

REF_DIR="skills/cloud-finops/references"
LLMS="llms.txt"
errors=0

# Check 1: every reference file appears in llms.txt.
# -F because the needle is a filename: the dot before `md` is a regex wildcard
# otherwise, so `finops-aws.md` would also be satisfied by a listing of
# `finops-awsXmd`. Fixed-string matching is what was always meant here.
for f in "$REF_DIR"/*.md; do
  base="$(basename "$f")"
  if ! grep -qF "references/$base" "$LLMS"; then
    echo "MISSING: $base exists but is not listed in $LLMS" >&2
    errors=$((errors + 1))
  fi
done

# Check 2: every reference path in llms.txt points to a real file.
while IFS= read -r path; do
  [[ -f "$path" ]] || {
    echo "STALE: $LLMS lists $path which does not exist" >&2
    errors=$((errors + 1))
  }
done < <(grep -oE 'skills/cloud-finops/references/[A-Za-z0-9._-]+\.md' "$LLMS" | sort -u)

count="$(find "$REF_DIR" -maxdepth 1 -name '*.md' -type f | wc -l | tr -d ' ')"
if [[ $errors -gt 0 ]]; then
  echo "FAIL: $errors llms.txt sync error(s). Update the 'Key files' list in $LLMS." >&2
  exit 1
fi
echo "OK: llms.txt lists all $count references, no stale paths."
