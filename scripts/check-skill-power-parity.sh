#!/usr/bin/env bash
#
# check-skill-power-parity.sh - Keep SKILL.md (Claude Code / generic agents)
# and POWER.md (Kiro IDE) saying the same thing.
#
# The two entry points route to the same reference files and deliberately share
# a near-identical body: everything from "## How to use this skill/power" to the
# licence footer. Only the frontmatter above that line differs by design (POWER
# carries displayName + a keywords list and an "## Onboarding" section Kiro
# needs; SKILL carries the claude.ai description field).
#
# It has already drifted once. The `references/finops-aws.md` routing row grew
# a set of governance keywords (cost-preventive SCPs, sandbox guardrails) in
# SKILL.md and not in POWER.md, so a Kiro user asking about deny-high-cost SCPs
# got no route to the file that answers it. Nothing caught that, because the
# two files are edited by hand in two places and a reviewer sees one diff.
#
# ---- What this checks ------------------------------------------------------
#
#   The shared body of both files, from the "## How to use this <skill|power>"
#   heading to end of file, must be identical after these deliberate,
#   documented differences are normalised away:
#
#     1. "this skill" / "this power"          -> compared as "this skill"
#        (both cases: sentence-initial "This power" too)
#     2. "Cloud FinOps Skill" / "... Power"   -> compared as "... Skill"
#        (the attribution footer noun)
#     3. Whole-line HTML comments             -> dropped from both sides
#     4. Trailing CR (CRLF checkouts)         -> stripped
#
#   Because the domain-routing table lives inside that body, every routing row
#   is compared too - which is the drift this exists to catch.
#
# ---- What this does NOT check ----------------------------------------------
#
#   - The YAML frontmatter of either file. They are legitimately different
#     shapes for two different loaders. SKILL.md's description length is gated
#     separately by scripts/check-skill-description.sh.
#   - POWER.md's "## Onboarding" section, which sits above the shared body and
#     has no SKILL.md counterpart.
#   - That either file routes to a reference that exists. check-llms-txt.sh and
#     check-docs-drift.sh gate the reference catalogue; nothing gates the
#     routing tables against the files on disk (a known, accepted gap).
#   - Semantic equivalence. This is a byte comparison after normalisation: a
#     reworded-but-equivalent row still fails, which is intended - the two
#     files are meant to be edited together, not independently.
#
# Usage:
#   ./scripts/check-skill-power-parity.sh    Print the drift; exit 1 if any.
#
# Wired into CI (.github/workflows/ci.yml) with the other drift guards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SKILL="skills/cloud-finops/SKILL.md"
POWER="skills/cloud-finops/POWER.md"

for f in "$SKILL" "$POWER"; do
  if [[ ! -f "$f" ]]; then
    echo "FAIL: $f does not exist - update this script for the new layout." >&2
    exit 1
  fi
done

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/skill-power-parity.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

# Print from the "## How to use this ..." heading to end of file, normalising
# the deliberate differences. awk rather than sed ranges so the "did we find
# the anchor at all" case can be reported instead of silently emitting nothing.
extract_body() {
  awk '
    { sub(/\r$/, "") }
    /^## How to use this (skill|power)[[:space:]]*$/ { started = 1 }
    !started { next }
    # Whole-line HTML comments are dropped on both sides: they are markers and
    # build annotations, not routing content, and one file legitimately carries
    # ones the other does not.
    /^[[:space:]]*<!--.*-->[[:space:]]*$/ { next }
    {
      gsub(/this power/, "this skill")
      gsub(/This power/, "This skill")
      gsub(/Cloud FinOps Power/, "Cloud FinOps Skill")
      print
    }
    END { if (!started) exit 3 }
  ' "$1"
}

if ! extract_body "$SKILL" > "$WORK_DIR/skill.txt"; then
  echo "FAIL: could not find the '## How to use this skill' anchor in $SKILL." >&2
  echo "      The shared-body boundary moved - update this script." >&2
  exit 1
fi
if ! extract_body "$POWER" > "$WORK_DIR/power.txt"; then
  echo "FAIL: could not find the '## How to use this power' anchor in $POWER." >&2
  echo "      The shared-body boundary moved - update this script." >&2
  exit 1
fi

if diff -u "$WORK_DIR/skill.txt" "$WORK_DIR/power.txt" \
     --label "$SKILL (shared body)" --label "$POWER (shared body)"; then
  lines="$(wc -l < "$WORK_DIR/skill.txt" | tr -d ' ')"
  echo "OK: SKILL.md and POWER.md share an identical body ($lines lines)."
  exit 0
fi

echo "" >&2
echo "FAIL: SKILL.md and POWER.md have drifted." >&2
echo "      They are two entry points onto the same content and must be edited" >&2
echo "      together - a routing row added to one and not the other silently" >&2
echo "      removes a domain from the other tool. Apply the change to both," >&2
echo "      or, if the difference is genuinely deliberate, add it to the" >&2
echo "      normalisation list in the header of this script." >&2
exit 1
