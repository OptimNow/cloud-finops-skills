#!/usr/bin/env bash
#
# build-llms-full.sh - generate llms-full.txt, the whole content library in one file.
#
# llms.txt lists where the content lives; llms-full.txt IS the content. The
# llmstxt.org convention pairs the two so an agent or crawler can take the whole
# library in a single fetch instead of following three dozen links. For this repo
# that is the difference between one request and 67.
#
# The output is deterministic: files are emitted in a fixed order (entry point,
# then references sorted by name, then playbooks sorted by name) and nothing
# time-varying is written into it. That is what lets --check byte-compare a fresh
# render against the committed file, the same contract fcp-coverage.md and
# playbook-coverage.md are held to.
#
# YAML frontmatter is stripped from each file and its discriminating facets are
# re-emitted as a plain-text metadata line, so a reader gets the routing
# information without a stray `---` fence every few hundred lines confusing the
# document structure.
#
# Usage:
#   ./scripts/build-llms-full.sh            # write llms-full.txt
#   ./scripts/build-llms-full.sh --check    # fail if the committed file is stale
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_DIR="$REPO_ROOT/skills/cloud-finops"
OUTPUT="$REPO_ROOT/llms-full.txt"

CHECK_MODE=0
if [[ "${1:-}" == "--check" ]]; then
  CHECK_MODE=1
elif [[ $# -gt 0 ]]; then
  echo "ERROR: unknown option: $1" >&2
  echo "Usage: $0 [--check]" >&2
  exit 1
fi

# Strip a leading YAML frontmatter block. Tolerates CRLF: a Windows checkout
# stores these files with \r\n and a bare /^---$/ never matches `---\r`, which
# is the bug that once shipped an installer artefact with the entire body
# missing. Only a fence on the very first line counts, so a markdown horizontal
# rule further down the file is left alone.
strip_frontmatter() {
  awk '
    { sub(/\r$/, "") }
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---"   { in_fm = 0; body = 1; next }
    in_fm { next }
    { if (body || NR > 1) print }
  ' "$1"
}

# Pull one scalar out of the frontmatter, unquoted. Returns empty if absent.
frontmatter_value() {
  awk -v key="$2" '
    { sub(/\r$/, "") }
    NR == 1 && $0 == "---" { in_fm = 1; next }
    in_fm && $0 == "---"   { exit }
    in_fm {
      idx = index($0, ":")
      if (idx == 0) next
      k = substr($0, 1, idx - 1)
      gsub(/^[ \t]+|[ \t]+$/, "", k)
      if (k != key) next
      v = substr($0, idx + 1)
      gsub(/^[ \t]+|[ \t]+$/, "", v)
      gsub(/^"|"$/, "", v)
      print v
      exit
    }
  ' "$1"
}

emit_file() {
  local path="$1" kind="$2" facets="$3"
  local base
  base="$(basename "$path")"

  printf '\n\n---\n\n'
  printf '## %s: %s\n\n' "$kind" "$base"
  printf 'Source: skills/cloud-finops/%s\n' "${path#"$SKILL_DIR"/}"
  if [[ -n "$facets" ]]; then
    printf '%s\n' "$facets"
  fi
  printf '\n'
  strip_frontmatter "$path"
}

render() {
  cat <<'HEADER'
# Cloud FinOps Skill & MCP - complete content

> The entire OptimNow Cloud FinOps knowledge library in one file: cloud cost
> optimisation across AWS, Azure, GCP and OCI, AI cost management and inference
> economics, Kubernetes, data platforms, allocation, chargeback, anomaly
> management, and named-pattern waste detection playbooks.

This is the llms-full.txt companion to llms.txt. llms.txt lists where each file
lives; this file inlines all of them, so an agent can ingest the whole library in
a single fetch. Content is licensed CC BY-SA 4.0 by OptimNow (https://optimnow.io).

GENERATED FILE - do not edit by hand. Produced by scripts/build-llms-full.sh from
the files under skills/cloud-finops/, and byte-compared against a fresh render in
CI. Edit the source files instead.

How to read it: an entry point first, then the long-form reference files (billing
mechanics, commitment strategy, allocation methodology), then the named-pattern
playbooks (one specific waste pattern each, in a Problem / Symptoms / Detection /
Fix / Anti-pattern / See also format). Each section names its source path.

A note on figures: these files carry billing MECHANICS, not current prices. Any
absolute figure inside is illustrative and dated inline. For a current price, use
a live pricing tool if one is available, otherwise see the OptimNow AI Pricing Hub
at https://optimtoken.optimnow.io - never quote an undated figure from this file.
HEADER

  emit_file "$SKILL_DIR/SKILL.md" "Entry point" ""

  local f name domain capability phases maturity facets
  while IFS= read -r f; do
    name="$(frontmatter_value "$f" name)"
    domain="$(frontmatter_value "$f" fcp_domain)"
    capability="$(frontmatter_value "$f" fcp_capability)"
    phases="$(frontmatter_value "$f" fcp_phases)"
    maturity="$(frontmatter_value "$f" fcp_maturity_entry)"
    facets="FinOps Framework: domain ${domain:-unspecified}; capability ${capability:-unspecified}; phases ${phases:-unspecified}; maturity entry ${maturity:-unspecified}"
    emit_file "$f" "Reference" "$facets"
  done < <(find "$SKILL_DIR/references" -name '*.md' -type f | LC_ALL=C sort)

  local scope service category confidence
  while IFS= read -r f; do
    [[ "$(basename "$f")" == "README.md" ]] && continue
    scope="$(frontmatter_value "$f" scope)"
    service="$(frontmatter_value "$f" service)"
    category="$(frontmatter_value "$f" waste_category)"
    confidence="$(frontmatter_value "$f" confidence)"
    facets="Pattern facets: scope ${scope:-unspecified}; service ${service:-unspecified}; waste category ${category:-unspecified}; classification confidence ${confidence:-unspecified}"
    emit_file "$f" "Playbook" "$facets"
  done < <(find "$SKILL_DIR/playbooks" -name '*.md' -type f | LC_ALL=C sort)

  printf '\n\n---\n\n'
  printf '> *Cloud FinOps Skill by [OptimNow](https://optimnow.io) - licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).*\n'
}

if [[ ! -d "$SKILL_DIR/references" || ! -d "$SKILL_DIR/playbooks" ]]; then
  echo "ERROR: expected content directories under $SKILL_DIR." >&2
  exit 1
fi

TMP_OUT="$(mktemp)"
trap 'rm -f "$TMP_OUT"' EXIT
render > "$TMP_OUT"

# An empty or near-empty render means the globs found nothing. Fail loudly
# rather than committing a hollow file - the same failure mode the MCP server's
# content gate guards against.
bytes="$(wc -c < "$TMP_OUT" | tr -d '[:space:]')"
if (( bytes < 200000 )); then
  echo "ERROR: rendered llms-full.txt is only $bytes bytes - the content globs found too little." >&2
  exit 1
fi

if (( CHECK_MODE )); then
  if [[ ! -f "$OUTPUT" ]]; then
    echo "FAIL: llms-full.txt does not exist. Run ./scripts/build-llms-full.sh." >&2
    exit 1
  fi
  if diff -u "$OUTPUT" "$TMP_OUT" > /dev/null 2>&1; then
    files="$(grep -cE "^## (Entry point|Reference|Playbook): " "$TMP_OUT" || true)"
    echo "OK: llms-full.txt matches the content library ($files files, $bytes bytes)."
    exit 0
  fi
  echo "FAIL: llms-full.txt is stale. Run ./scripts/build-llms-full.sh and commit." >&2
  diff -u "$OUTPUT" "$TMP_OUT" | head -40 >&2
  exit 1
fi

cp "$TMP_OUT" "$OUTPUT"
files="$(grep -cE "^## (Entry point|Reference|Playbook): " "$OUTPUT" || true)"
echo "Wrote llms-full.txt ($files files, $bytes bytes)."
