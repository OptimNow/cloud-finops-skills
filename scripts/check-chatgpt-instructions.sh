#!/usr/bin/env bash
#
# check-chatgpt-instructions.sh - keep the ChatGPT instructions under the GPT
# editor's Instructions limit.
#
# ChatGPT's Custom GPT Instructions field holds about 8000 characters. The
# installer builds instructions.md from a routing table that grows with every
# new reference, and the build only printed a warning when it crossed the
# limit. Nothing in CI built the chatgpt target, so by 2026-10-20 the default
# build stood at 9671 characters: a pasted configuration lost its last rows,
# the price-figure rule among them. This check builds both variants (default
# and --grouped) and fails above the limit, so the overflow cannot return
# unnoticed.
#
# Usage: ./scripts/check-chatgpt-instructions.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# The GPT editor's limit. Fail above it.
HARD_LIMIT=8000
# Warn above this, so the ceiling is visible a row or two before it is hit.
WARN_LIMIT=7400

errors=0
for variant in default grouped; do
  workdir="$(mktemp -d)"
  if [[ "$variant" == "grouped" ]]; then
    bash install.sh --tool chatgpt --grouped --dest "$workdir" >/dev/null 2>&1
  else
    bash install.sh --tool chatgpt --dest "$workdir" >/dev/null 2>&1
  fi
  path="$workdir/dist/chatgpt/instructions.md"
  if [[ ! -f "$path" ]]; then
    echo "MISSING: the $variant build produced no instructions.md" >&2
    errors=$((errors + 1))
    rm -rf "$workdir"
    continue
  fi
  size="$(wc -m < "$path" | tr -d ' ')"
  rm -rf "$workdir"
  if (( size > HARD_LIMIT )); then
    echo "TOO LONG: $variant instructions are $size characters (limit $HARD_LIMIT)" >&2
    errors=$((errors + 1))
  elif (( size > WARN_LIMIT )); then
    echo "WARN: $variant instructions are $size of $HARD_LIMIT characters. Tighten a routing row before adding another."
  else
    printf 'OK: %-8s instructions %5s of %s characters\n' "$variant" "$size" "$HARD_LIMIT"
  fi
done

if (( errors > 0 )); then
  cat >&2 <<'MSG'

FAIL: the ChatGPT instructions exceed the GPT editor's ~8000-character limit.

Shorten routing rows in build_chatgpt_instructions (or build_grouped_instructions)
in install.sh. The default build lists representative named waste patterns only;
do not add each new playbook to that row.
MSG
  exit 1
fi
