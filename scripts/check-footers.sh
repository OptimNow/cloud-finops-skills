#!/usr/bin/env bash
#
# check-footers.sh - Assert every shipped content file still ends with its
# OptimNow / CC BY-SA attribution footer.
#
# This is the truncation tripwire. The April-May 2026 pipeline incident
# truncated 8 reference files across two runs, and the recovery notes are blunt
# about why it went unnoticed for 16 days: a truncated file looks valid in
# `git diff` (the diff simply stops where the file stops), and the only signal
# was the missing footer at the end - which nothing checked. The pipeline's own
# `validate_post_apply` guard now checks exactly this before writing a file;
# this script is the same assertion applied to the committed tree, so a
# truncation that arrives by any other route (a bad merge, a hand edit, a
# future tool) still fails loudly at PR time.
#
# What it checks: the last 300 bytes of each file must contain BOTH the string
# "OptimNow" AND the string "CC BY-SA". Deliberately a substring test on the
# tail rather than an exact-line match - the footer noun differs by surface
# ("Cloud FinOps Skill" / "Playbook" / "Power") and the attribution string is
# what third-party reusers carry, so it must not be tightened into something
# that would push contributors to edit it.
#
# Files covered:
#   skills/cloud-finops/references/*.md   (all)
#   skills/cloud-finops/playbooks/*.md    (all, README.md included - it carries
#                                          the same Playbook footer)
#   skills/cloud-finops/SKILL.md          (entry point, same footer shape)
#   skills/cloud-finops/POWER.md          (ditto)
#
# What it does NOT check: that the footer text is byte-identical across files,
# that the licence URL resolves, or anything about the body above the footer.
# A file could still be truncated in the middle and keep its footer; this
# catches the tail-loss failure mode that actually happened.
#
# Usage:
#   ./scripts/check-footers.sh    Report every offending file; exit 1 if any.
#
# Wired into CI (.github/workflows/ci.yml) alongside the other drift guards.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

SKILL_DIR="skills/cloud-finops"
TAIL_BYTES=300
errors=0
checked=0

# Collect the files to check. Globs are expanded here rather than inside the
# loop so a missing directory fails loudly instead of silently checking zero
# files and reporting OK.
files=()
for d in "$SKILL_DIR/references" "$SKILL_DIR/playbooks"; do
  if [[ ! -d "$d" ]]; then
    echo "FAIL: $d does not exist - the repo layout changed, update this script." >&2
    exit 1
  fi
  while IFS= read -r f; do
    files+=("$f")
  done < <(find "$d" -maxdepth 1 -name '*.md' -type f | LC_ALL=C sort)
done
for f in "$SKILL_DIR/SKILL.md" "$SKILL_DIR/POWER.md"; do
  [[ -f "$f" ]] && files+=("$f")
done

if [[ ${#files[@]} -eq 0 ]]; then
  echo "FAIL: no content files found under $SKILL_DIR - update this script." >&2
  exit 1
fi

for f in "${files[@]}"; do
  checked=$((checked + 1))
  # `tail -c` on the raw bytes: works the same on a CRLF checkout, and avoids
  # any assumption about how many lines the footer block occupies.
  tail_text="$(tail -c "$TAIL_BYTES" "$f" 2>/dev/null || true)"

  missing=""
  case "$tail_text" in *OptimNow*) ;; *) missing="OptimNow" ;; esac
  case "$tail_text" in
    *"CC BY-SA"*) ;;
    *) missing="${missing:+$missing and }CC BY-SA" ;;
  esac

  if [[ -n "$missing" ]]; then
    echo "TRUNCATED?: $f - last $TAIL_BYTES bytes are missing $missing" >&2
    errors=$((errors + 1))
  fi
done

if [[ $errors -gt 0 ]]; then
  echo "" >&2
  echo "FAIL: $errors file(s) do not end with the OptimNow / CC BY-SA footer." >&2
  echo "      This is the signature of a truncated file - check the tail of each" >&2
  echo "      one before assuming the footer was merely forgotten. See the" >&2
  echo "      'Pipeline applier truncated 8 reference files' entry in CLAUDE.md." >&2
  exit 1
fi

echo "OK: all $checked content files end with the OptimNow / CC BY-SA footer."
