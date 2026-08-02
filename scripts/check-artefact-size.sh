#!/usr/bin/env bash
#
# check-artefact-size.sh - keep the single-file installer artefacts small
# enough to actually load.
#
# The 2026-08 review (F5) found cursor / windsurf / codex emitting ~1MB files
# (~250K tokens) and aider ~445KB. They had grown with the reference library
# and nothing measured them, so the regression was invisible: the installer
# reported success and the artefact silently overflowed or dominated the
# target tool's context window.
#
# The default build is now a routing file plus an index. This check builds
# every single-file target into a scratch directory and fails if one crosses
# the ceiling, so the inlining regression cannot come back unnoticed.
#
# `--inline` artefacts are intentionally huge and are not checked here.
#
# Usage: ./scripts/check-artefact-size.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Roughly 4 chars per token, so 200000 bytes is ~50K tokens - comfortably
# loadable by every target tool while leaving room for the library to grow.
# Raise deliberately if the routing file legitimately grows; do not raise to
# accommodate re-inlining the reference bodies.
MAX_BYTES=200000

WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "Building single-file targets into $WORKDIR ..."
bash install.sh --tool cursor   --dest "$WORKDIR" >/dev/null
bash install.sh --tool windsurf --dest "$WORKDIR" >/dev/null
bash install.sh --tool codex    --dest "$WORKDIR" >/dev/null
bash install.sh --tool aider    --dest "$WORKDIR" >/dev/null
bash install.sh --tool copilot  --dest "$WORKDIR" >/dev/null

ARTEFACTS=(
  ".cursor/rules/cloud-finops.mdc"
  ".windsurf/rules/cloud-finops.md"
  "AGENTS.md"
  "CONVENTIONS.md"
  ".github/copilot-instructions.md"
)

errors=0
for rel in "${ARTEFACTS[@]}"; do
  path="$WORKDIR/$rel"
  if [[ ! -f "$path" ]]; then
    echo "MISSING: expected artefact $rel was not produced" >&2
    errors=$((errors + 1))
    continue
  fi
  size="$(wc -c < "$path" | tr -d ' ')"
  if (( size > MAX_BYTES )); then
    echo "TOO BIG: $rel is $size bytes (ceiling $MAX_BYTES)" >&2
    errors=$((errors + 1))
  else
    printf 'OK: %-38s %8s bytes\n' "$rel" "$size"
  fi
done

if (( errors > 0 )); then
  cat >&2 <<'MSG'

FAIL: one or more installer artefacts exceed the size ceiling.

The single-file targets are meant to emit a routing file (SKILL.md plus a
reference/playbook index) and point retrieval at the cloud-finops MCP server
or a local checkout. If a build is inlining reference bodies again, fix the
builder rather than raising MAX_BYTES.
MSG
  exit 1
fi

echo "OK: all single-file artefacts under $MAX_BYTES bytes."
