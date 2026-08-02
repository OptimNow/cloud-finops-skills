#!/usr/bin/env bash
#
# fcp-coverage.sh - Report which FinOps Framework Capabilities are covered by
# the reference files in this repo, and which remain as gaps.
#
# Reads fcp_domain + fcp_capability + fcp_capabilities_secondary from the YAML
# frontmatter of every reference file under skills/cloud-finops/references/ and
# compares against the canonical 22 Capabilities of the FinOps Foundation
# Framework (https://www.finops.org/framework/).
#
# Output: writes fcp-coverage.md at the repo root and prints a summary to
# stdout. Exit code is 0 if the matrix can be built, 1 if a reference declares
# a non-canonical Capability (typo / convention drift).
#
# Usage:
#   ./scripts/fcp-coverage.sh           Generate fcp-coverage.md
#   ./scripts/fcp-coverage.sh --check   Generate AND fail if a frontmatter is
#                                       missing or declares a non-canonical
#                                       capability (use in CI).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

CHECK_MODE=""
[[ "${1:-}" == "--check" ]] && CHECK_MODE=1

REF_DIR="skills/cloud-finops/references"
OUT_FILE="fcp-coverage.md"

# ---- Canonical FinOps Framework 2026 (4 Domains, 22 Capabilities) ----------
# Source: https://www.finops.org/framework/ (post-2026 update)
# Renames vs the 2024 framework, captured here for migration audits:
#   - Architecting for Cloud  -> Architecting & Workload Placement
#   - Workload Optimization   -> Usage Optimization
#   - Cloud Sustainability    -> Sustainability
#   - Benchmarking            -> KPIs & Benchmarking
#   - Policy & Governance     -> Governance, Policy & Risk
#   - FinOps Tools & Services -> Automation, Tools & Services
# Added in 2026:
#   - Executive Strategy Alignment (Manage the FinOps Practice)
# Removed in 2026:
#   - Onboarding Workloads (the workload-placement / sizing-at-intake angle is
#     now part of Architecting & Workload Placement; the practice-operations
#     angle of intake gates folds into FinOps Practice Operations).
declare -A CANONICAL
CANONICAL["Understand Usage & Cost"]="Data Ingestion|Allocation|Reporting & Analytics|Anomaly Management"
CANONICAL["Quantify Business Value"]="Planning & Estimating|Forecasting|Budgeting|KPIs & Benchmarking|Unit Economics"
CANONICAL["Optimize Usage & Cost"]="Architecting & Workload Placement|Usage Optimization|Rate Optimization|Licensing & SaaS|Sustainability"
CANONICAL["Manage the FinOps Practice"]="Executive Strategy Alignment|FinOps Practice Operations|Governance, Policy & Risk|FinOps Education & Enablement|Invoicing & Chargeback|FinOps Assessment|Automation, Tools & Services|Intersecting Disciplines"

DOMAIN_ORDER=("Understand Usage & Cost" "Quantify Business Value" "Optimize Usage & Cost" "Manage the FinOps Practice")

# Reverse map: capability -> domain (for secondary lookups)
declare -A CAP_TO_DOMAIN
for d in "${DOMAIN_ORDER[@]}"; do
  IFS='|' read -ra caps <<< "${CANONICAL[$d]}"
  for c in "${caps[@]}"; do
    CAP_TO_DOMAIN["$c"]="$d"
  done
done

# ---- Walk references and collect coverage ----------------------------------
declare -A PRIMARY    # "Domain||Capability" -> "ref1; ref2; ..."
declare -A SECONDARY  # same shape, secondary mentions only
ERRORS=0

# Strip surrounding quotes from a YAML scalar (single or double).
strip_quotes() {
  local s="$1"
  s="${s#\"}"; s="${s%\"}"
  s="${s#\'}"; s="${s%\'}"
  printf '%s' "$s"
}

while IFS= read -r f; do
  fname=$(basename "$f")

  # First two `---` markers delimit frontmatter
  in_fm=0
  fm_count=0
  domain=""
  capability=""
  secondary_line=""
  while IFS= read -r line; do
    # Strip trailing \r in case the file has CRLF line endings (common on
    # Windows checkouts).
    line="${line%$'\r'}"
    if [[ "$line" == "---" ]]; then
      fm_count=$((fm_count + 1))
      [[ $fm_count -ge 2 ]] && break
      in_fm=1
      continue
    fi
    [[ $in_fm -eq 1 ]] || continue
    case "$line" in
      "fcp_domain:"*)
        domain=$(strip_quotes "$(printf '%s' "${line#fcp_domain:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')")
        ;;
      "fcp_capability:"*)
        capability=$(strip_quotes "$(printf '%s' "${line#fcp_capability:}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')")
        ;;
      "fcp_capabilities_secondary:"*)
        secondary_line="${line#fcp_capabilities_secondary:}"
        ;;
    esac
  done < "$f"

  if [[ -z "$domain" || -z "$capability" ]]; then
    echo "WARN: $fname missing fcp_domain or fcp_capability" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi

  # Validate primary capability is canonical for the declared domain
  if [[ -z "${CANONICAL[$domain]:-}" ]]; then
    echo "ERROR: $fname declares non-canonical fcp_domain: $domain" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi
  if [[ "|${CANONICAL[$domain]}|" != *"|${capability}|"* ]]; then
    echo "ERROR: $fname declares fcp_capability=$capability not in canonical list for $domain" >&2
    ERRORS=$((ERRORS + 1))
    continue
  fi

  pkey="${domain}||${capability}"
  if [[ -n "${PRIMARY[$pkey]:-}" ]]; then
    PRIMARY[$pkey]="${PRIMARY[$pkey]}; ${fname}"
  else
    PRIMARY[$pkey]="${fname}"
  fi

  # Secondary capabilities (YAML inline list: ["Cap A", "Cap B"])
  if [[ -n "$secondary_line" ]]; then
    # Split YAML inline list ["A", "B, C", "D"] on `","` (quote-comma-quote)
    # rather than bare comma so capability names that contain commas
    # (e.g. "Governance, Policy & Risk") stay intact.
    sec=$(printf '%s' "$secondary_line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
      | sed 's/^\[//;s/\]$//' \
      | sed 's/"[[:space:]]*,[[:space:]]*"/"\n"/g' \
      | sed 's/^[[:space:]]*//;s/[[:space:]]*$//' \
      | sed 's/^"//;s/"$//' \
      | sed "s/^'//;s/'$//")
    while IFS= read -r cap; do
      [[ -z "$cap" ]] && continue
      sd="${CAP_TO_DOMAIN[$cap]:-}"
      if [[ -z "$sd" ]]; then
        echo "WARN: $fname secondary capability $cap not in canonical list" >&2
        continue
      fi
      skey="${sd}||${cap}"
      if [[ -n "${SECONDARY[$skey]:-}" ]]; then
        SECONDARY[$skey]="${SECONDARY[$skey]}; ${fname}"
      else
        SECONDARY[$skey]="${fname}"
      fi
    done <<< "$sec"
  fi
done < <(find "$REF_DIR" -maxdepth 1 -name "*.md" -type f | sort)

# ---- Render fcp-coverage.md -----------------------------------------------
total_caps=0
covered_caps=0
{
  echo "# FCP Framework Coverage Matrix"
  echo
  echo "Generated by \`scripts/fcp-coverage.sh\` from the YAML frontmatter of"
  echo "every reference file under \`skills/cloud-finops/references/\`. The canonical"
  echo "list is the 4 Domains / 22 Capabilities of the"
  echo "[FinOps Framework](https://www.finops.org/framework/)."
  echo
  echo "**Do not edit this file by hand** - re-run the script after changing a"
  echo "reference's frontmatter."
  echo
  echo "Marker legend:"
  echo "- \`[x]\` - capability has at least one reference declaring it as the primary \`fcp_capability\`"
  echo "- \`[~]\` - capability is only touched as a secondary (\`fcp_capabilities_secondary\`); no primary owner"
  echo "- \`[ ]\` - capability has no coverage at all (true gap)"
  echo

  secondary_only_caps=0
  gap_caps=0
  for d in "${DOMAIN_ORDER[@]}"; do
    echo "## $d"
    echo
    IFS='|' read -ra caps <<< "${CANONICAL[$d]}"
    for c in "${caps[@]}"; do
      total_caps=$((total_caps + 1))
      key="${d}||${c}"
      primary="${PRIMARY[$key]:-}"
      secondary="${SECONDARY[$key]:-}"
      mark=" "
      label_suffix=""
      if [[ -n "$primary" ]]; then
        mark="x"
        covered_caps=$((covered_caps + 1))
      elif [[ -n "$secondary" ]]; then
        # Secondary-only: not a primary owner, but the capability IS
        # touched. Render as `~` to distinguish from a true gap.
        mark="~"
        secondary_only_caps=$((secondary_only_caps + 1))
      else
        gap_caps=$((gap_caps + 1))
      fi
      line="- [$mark] **$c**"
      if [[ -n "$primary" ]]; then
        line="$line - $primary"
      fi
      if [[ -n "$secondary" ]]; then
        line="$line _(secondary: $secondary)_"
      fi
      if [[ -z "$primary" && -z "$secondary" ]]; then
        line="$line - **GAP** (see Roadmap in CLAUDE.md for deferred capabilities)"
      fi
      echo "$line"
    done
    echo
  done

  echo "---"
  echo
  pct_primary=$(( (covered_caps * 100) / total_caps ))
  pct_any=$(( ((covered_caps + secondary_only_caps) * 100) / total_caps ))
  echo "**Primary coverage**: ${covered_caps} / ${total_caps} (${pct_primary}%) - capabilities with at least one reference whose \`fcp_capability\` is the primary classification."
  echo
  echo "**Any-coverage** (primary OR secondary): $((covered_caps + secondary_only_caps)) / ${total_caps} (${pct_any}%) - includes ${secondary_only_caps} capabilities marked \`[~]\` that are touched by another reference's \`fcp_capabilities_secondary\` but have no primary owner yet."
  echo
  echo "**True gaps** (no primary AND no secondary): ${gap_caps}. These are tracked in the Roadmap section of CLAUDE.md with rationale and trigger-to-revisit."
  # Keep the legacy single-number for any caller that greps for it
  echo
  echo "_Legacy summary line (do not rely on this for scripting): **Coverage: ${covered_caps} / ${total_caps} Framework Capabilities (${pct_primary}%)**_"
} > "$OUT_FILE"

echo "Generated $OUT_FILE: ${covered_caps}/${total_caps} capabilities covered"

if [[ -n "$CHECK_MODE" && $ERRORS -gt 0 ]]; then
  echo "FAIL: $ERRORS frontmatter error(s) - see warnings above" >&2
  exit 1
fi
