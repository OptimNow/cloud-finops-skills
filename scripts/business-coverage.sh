#!/usr/bin/env bash
#
# business-coverage.sh - Render the "providers x business needs" coverage
# matrix shown in README.md from the reference-file frontmatter, and fail CI
# when the committed README block no longer matches the files.
#
# Third generator in the family (after fcp-coverage.sh for the Framework
# capabilities and playbook-coverage.sh for the runbooks). The first two read
# fields that already existed; this one reads a field added in October 2026:
#
#   business_coverage: ["aws:commitments:deep", "gcp:commitments:partial"]
#
# Each token is <provider>:<need>:<depth>. A reference declares the cells it
# serves and how deeply. The matrix cell is the deepest declaration across all
# references; a cell nobody declares renders as "not covered". A reference
# with no business_coverage line is allowed (practice-level files such as
# finops-framework.md serve no provider x need cell) and contributes nothing.
#
# Depth is declared, not measured. The frontmatter is the reviewable record of
# that judgement: a PR that adds a section to a file also edits its
# declaration, the diff shows the cell moving, and CI holds the README in step.
#
# Vocabulary (keep in step with the README legend and the two tables):
#   providers  aws azure gcp oci on-prem | ai-platforms data-platforms saas
#   needs      bill budget commitments contracts waste ai data saas carbon
#   depths     deep partial
# Only the inline YAML list form is read, like fcp_capabilities_secondary.
#
# Output: rewrites the block between
#   <!-- business-coverage:start -->  and  <!-- business-coverage:end -->
# in the target file (README.md by default). Exit 1 on a frontmatter error
# (unknown provider, need or depth; malformed token; block-style list).
#
# Usage:
#   ./scripts/business-coverage.sh                    Rewrite the README block
#   ./scripts/business-coverage.sh --target docs/x.md Rewrite another file's block
#   ./scripts/business-coverage.sh --check            Fail if the frontmatter is
#                                                     invalid OR the committed
#                                                     block differs from a fresh
#                                                     render. Never writes.
#   ./scripts/business-coverage.sh --print            Print the rendered block
#
# BUSINESS_COVERAGE_REF_DIR overrides the references directory (tests).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

REF_DIR="${BUSINESS_COVERAGE_REF_DIR:-plugins/cloud-finops/skills/cloud-finops/references}"
TARGET="README.md"
MODE="write"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --print) MODE="print"; shift ;;
    --target) TARGET="$2"; shift 2 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

START_MARK="<!-- business-coverage:start -->"
END_MARK="<!-- business-coverage:end -->"

# ---- Vocabulary --------------------------------------------------------------
# Three tables rather than one, so that each fits a 375 px phone screen
# without horizontal scrolling (GitHub pads every cell by 13 px a side, so a
# 9-column table overflows there). The column groups are also how a reader
# thinks: the three hyperscalers, the other estates, the platforms on top.
HYPERSCALERS=(aws azure gcp)
OTHER_ESTATES=(oci on-prem)
PLATFORMS=(ai-platforms data-platforms saas)
CLOUDS=("${HYPERSCALERS[@]}" "${OTHER_ESTATES[@]}")
NEEDS=(bill budget commitments contracts waste ai data saas carbon)
DEPTHS=(deep partial)

# Short column labels on purpose (phone width); the README sentence under the
# tables spells out what each platform column contains.
declare -A PROVIDER_LABEL=(
  [aws]="AWS" [azure]="Azure" [gcp]="GCP" [oci]="OCI" [on-prem]="On-prem"
  [ai-platforms]="AI" [data-platforms]="Data" [saas]="SaaS"
)
declare -A NEED_LABEL=(
  [bill]="Understand and allocate the bill"
  [budget]="Budget and forecast"
  [commitments]="Commitments and discounts"
  [contracts]="Contract negotiation and renewal"
  [waste]="Reduce waste"
  [ai]="AI and GenAI spend"
  [data]="Data platforms"
  [saas]="SaaS and licences"
  [carbon]="Carbon footprint"
)
# Combinations that do not exist: a data-platform row for the AI-platform and
# SaaS columns. Rendered as n/a, never as a gap.
declare -A NOT_APPLICABLE=( ["data|ai-platforms"]=1 ["data|saas"]=1 )

declare -A SYMBOL=( [deep]="●" [partial]="◐" [none]="–" [na]="n/a" )
declare -A RANK=( [deep]=2 [partial]=1 )

in_list() {
  local needle="$1"; shift
  local x
  for x in "$@"; do [[ "$x" == "$needle" ]] && return 0; done
  return 1
}

# ---- Walk references and collect the deepest declaration per cell ----------
declare -A CELL      # "need|provider" -> deep | partial
declare -A SOURCES   # "need|provider" -> "file (depth); ..."
ERRORS=0
DECLARED_FILES=0

while IFS= read -r f; do
  fname="$(basename "$f")"
  line_value=""
  present=0
  fence=0
  while IFS= read -r line; do
    line="${line%$'\r'}"
    if [[ "$line" == "---" ]]; then
      fence=$((fence + 1))
      [[ $fence -ge 2 ]] && break
      continue
    fi
    [[ $fence -eq 1 ]] || continue
    case "$line" in
      "business_coverage:"*)
        present=1
        line_value="${line#business_coverage:}"
        ;;
    esac
  done < "$f"

  [[ $present -eq 1 ]] || continue
  DECLARED_FILES=$((DECLARED_FILES + 1))

  trimmed="$(printf '%s' "$line_value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
  if [[ -z "$trimmed" ]]; then
    echo "ERROR: $fname declares business_coverage with no value on the same line." >&2
    echo "       Use the inline form: business_coverage: [\"aws:waste:deep\", ...]" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi
  if [[ "$trimmed" != \[*\] ]]; then
    echo "ERROR: $fname business_coverage must be an inline list in square brackets." >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi

  tokens="$(printf '%s' "$trimmed" | sed 's/^\[//;s/\]$//' | tr ',' '\n' \
    | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//")"
  while IFS= read -r tok; do
    [[ -z "$tok" ]] && continue
    IFS=':' read -r provider need depth <<< "$tok"
    if [[ -z "${provider:-}" || -z "${need:-}" || -z "${depth:-}" ]]; then
      echo "ERROR: $fname token '$tok' is not <provider>:<need>:<depth>" >&2
      ERRORS=$((ERRORS + 1)); continue
    fi
    if ! in_list "$provider" "${CLOUDS[@]}" "${PLATFORMS[@]}"; then
      echo "ERROR: $fname token '$tok': unknown provider '$provider'" >&2
      ERRORS=$((ERRORS + 1)); continue
    fi
    if ! in_list "$need" "${NEEDS[@]}"; then
      echo "ERROR: $fname token '$tok': unknown need '$need'" >&2
      ERRORS=$((ERRORS + 1)); continue
    fi
    if ! in_list "$depth" "${DEPTHS[@]}"; then
      echo "ERROR: $fname token '$tok': unknown depth '$depth' (deep | partial)" >&2
      ERRORS=$((ERRORS + 1)); continue
    fi
    key="$need|$provider"
    if [[ -n "${NOT_APPLICABLE[$key]:-}" ]]; then
      echo "ERROR: $fname token '$tok' targets a cell marked not applicable" >&2
      ERRORS=$((ERRORS + 1)); continue
    fi
    current="${CELL[$key]:-}"
    if [[ -z "$current" || ${RANK[$depth]} -gt ${RANK[$current]} ]]; then
      CELL[$key]="$depth"
    fi
    SOURCES[$key]="${SOURCES[$key]:+${SOURCES[$key]}; }$fname ($depth)"
  done <<< "$tokens"
done < <(find "$REF_DIR" -maxdepth 1 -name "*.md" -type f | LC_ALL=C sort)

if [[ $ERRORS -gt 0 ]]; then
  echo "business-coverage: $ERRORS frontmatter error(s); nothing rendered." >&2
  exit 1
fi
if [[ $DECLARED_FILES -eq 0 ]]; then
  echo "business-coverage: no reference declares business_coverage; nothing to render." >&2
  exit 1
fi

# ---- Render the block --------------------------------------------------------
render_table() {
  local title="$1"; shift
  local providers=("$@")
  local header="| Business need |"
  local divider="|---|"
  local p
  for p in "${providers[@]}"; do
    header+=" ${PROVIDER_LABEL[$p]} |"
    divider+=":-:|"
  done
  echo "**$title**"
  echo
  echo "$header"
  echo "$divider"
  local n
  for n in "${NEEDS[@]}"; do
    local row="| ${NEED_LABEL[$n]} |"
    for p in "${providers[@]}"; do
      local key="$n|$p"
      if [[ -n "${NOT_APPLICABLE[$key]:-}" ]]; then
        row+=" ${SYMBOL[na]} |"
      else
        row+=" ${SYMBOL[${CELL[$key]:-none}]} |"
      fi
    done
    echo "$row"
  done
}

RENDER="$(
  echo "$START_MARK"
  render_table "Hyperscalers" "${HYPERSCALERS[@]}"
  echo
  render_table "Other estates" "${OTHER_ESTATES[@]}"
  echo
  render_table "Platforms" "${PLATFORMS[@]}"
  echo "$END_MARK"
)"

if [[ "$MODE" == "print" ]]; then
  printf '%s\n' "$RENDER"
  exit 0
fi

if [[ ! -f "$TARGET" ]]; then
  echo "business-coverage: target $TARGET not found" >&2
  exit 1
fi
if ! grep -qF "$START_MARK" "$TARGET" || ! grep -qF "$END_MARK" "$TARGET"; then
  echo "business-coverage: $TARGET has no $START_MARK / $END_MARK block" >&2
  exit 1
fi

CURRENT="$(awk -v s="$START_MARK" -v e="$END_MARK" '
  $0 == s { on = 1 }
  on { print }
  $0 == e { on = 0 }
' "$TARGET")"

if [[ "$MODE" == "check" ]]; then
  if [[ "$CURRENT" == "$RENDER" ]]; then
    echo "OK: business-coverage block in $TARGET matches the reference frontmatter ($DECLARED_FILES files declare cells)."
    exit 0
  fi
  diff -u <(printf '%s\n' "$CURRENT") <(printf '%s\n' "$RENDER") \
    --label "$TARGET (committed)" --label "$TARGET (regenerated)" || true
  echo "" >&2
  echo "FAIL: the business-coverage block in $TARGET is stale. Run" >&2
  echo "      ./scripts/business-coverage.sh and commit the result." >&2
  exit 1
fi

TMP="$(mktemp "${TMPDIR:-/tmp}/business-coverage.XXXXXX")"
trap 'rm -f "$TMP"' EXIT
awk -v s="$START_MARK" -v e="$END_MARK" -v block="$RENDER" '
  $0 == s { print block; skip = 1; next }
  $0 == e { skip = 0; next }
  !skip { print }
' "$TARGET" > "$TMP"
mv "$TMP" "$TARGET"
trap - EXIT
echo "Wrote the business-coverage block into $TARGET ($DECLARED_FILES files declare cells)."
