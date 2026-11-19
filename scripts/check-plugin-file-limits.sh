#!/usr/bin/env bash
#
# check-plugin-file-limits.sh - keep every tracked file inside the Claude plugin
# directory's per-file and file-count limits.
#
# The plugin folder is plugins/cloud-finops/ (it holds .claude-plugin/plugin.json),
# and the directory scans every file under it on each commit it picks up from
# `main`. Two of its checks do not block a submission but put every new version
# on hold for a reviewer, which is what would stop the regular content
# releases from auto-publishing:
#
#   - any file that is not an image or a font over 256 KiB;
#   - more than 512 files in the plugin folder.
#
# Source: https://claude.com/docs/plugins/pre-submission-checklist, "Files in
# the plugin folder", read on 2026-09-30. The count ceiling here is 480, not
# 512, so a content batch that adds a few playbooks fails in CI with room to
# spare rather than tripping the hold on the directory side first.
#
# What counts as an image or a font follows the checklist's own list (PNG, JPEG,
# GIF, WebP images; font files). SVG is listed there as a text file, so it is
# NOT exempt here and must stay under the ceiling like any other text.
#
# The file that used to trip the size check, llms-full.txt (~1.2 MB), is no
# longer committed: scripts/build-llms-full.sh builds it in the release
# workflows and it ships as a GitHub Release asset.
#
# A third limit, on the total size of the folder, is reported but never fails.
# From 16 November 2026 the directory held every new version with "Files the
# policy review couldn't cover" ("didn't read some of its files, for example
# because they're too large or there are too many"), while the folder had 106
# files, none over 62 KB. No page of Anthropic's documentation gives a total
# size. The first held commit (d1eaf17, PR 378) took the folder to 2,109,903
# bytes; the commit before it, at 2,080,926 bytes, went live. So the budget
# used here, 2 MiB, is inferred from one crossing, not read anywhere. The
# script warns when the folder is above 95% of it and when it is over, and
# names the largest files. It does not fail: the folder is over the budget
# already, and whether to slim it, split the plugin or accept a review of each
# version waits on Anthropic's answer. The total counts the files as git
# stores them (LF line endings), which is what the directory reads from
# GitHub; a Windows checkout with CRLF line endings reads larger on disk.
#
# Usage: ./scripts/check-plugin-file-limits.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PLUGIN_DIR="plugins/cloud-finops"
MAX_FILE_BYTES=262144   # 256 KiB, the directory's per-file ceiling
MAX_FILES=480           # directory holds a version above 512; fail early
REVIEW_BUDGET_BYTES=2097152                         # 2 MiB, inferred (see header)
REVIEW_WARN_BYTES=$((REVIEW_BUDGET_BYTES * 95 / 100))

errors=0
count=0
while IFS= read -r -d '' path; do
  count=$((count + 1))
  # A path that is tracked but absent on disk (a deletion staged but the
  # check run before commit) has no size to measure; skip it.
  [[ -f "$path" ]] || continue
  ext="${path##*.}"
  ext="$(printf '%s' "$ext" | tr '[:upper:]' '[:lower:]')"
  case "$ext" in
    png|jpg|jpeg|gif|webp|ttf|otf|woff|woff2|eot)
      continue
      ;;
  esac
  size="$(wc -c < "$path" | tr -d '[:space:]')"
  if (( size > MAX_FILE_BYTES )); then
    echo "TOO BIG: $path is $size bytes (ceiling $MAX_FILE_BYTES); the directory holds every version carrying it for a reviewer" >&2
    errors=$((errors + 1))
  fi
done < <(git ls-files -z -- "$PLUGIN_DIR")

if (( count > MAX_FILES )); then
  echo "TOO MANY: $count tracked files (ceiling $MAX_FILES; the directory holds a version above 512)" >&2
  errors=$((errors + 1))
fi

# Total size, as git stores the files (see header). Sizes come from the
# index, so a local run before `git add` measures the staged content; CI
# checks out a commit, where the index is that commit.
sizes="$(git ls-files -s -- "$PLUGIN_DIR" \
  | awk -F'\t' '{ split($1, meta, " "); print meta[2] " " $2 }' \
  | git cat-file --batch-check='%(objectsize) %(rest)')"
total="$(printf '%s\n' "$sizes" | awk '{ t += $1 } END { print t + 0 }')"
mib() { awk -v b="$1" 'BEGIN { printf "%.2f", b / 1048576 }'; }

if (( total > REVIEW_BUDGET_BYTES )); then
  size_state="over"
  size_line="TOTAL: $total bytes ($(mib "$total") MiB), $((total - REVIEW_BUDGET_BYTES)) bytes over the inferred 2 MiB budget of the directory's policy review, which then holds each version for a reviewer."
elif (( total > REVIEW_WARN_BYTES )); then
  size_state="near"
  size_line="TOTAL: $total bytes ($(mib "$total") MiB), $((REVIEW_BUDGET_BYTES - total)) bytes left under the inferred 2 MiB budget of the directory's policy review."
else
  size_state="ok"
  size_line="TOTAL: $total bytes ($(mib "$total") MiB), $((REVIEW_BUDGET_BYTES - total)) bytes left under the inferred 2 MiB review budget."
fi
echo "$size_line"
if [[ "$size_state" != "ok" ]]; then
  echo "Largest files:"
  printf '%s\n' "$sizes" | sort -rn | head -5 | awk '{ printf "  %8d  %s\n", $1, $2 }'
  if [[ -n "${GITHUB_ACTIONS:-}" ]]; then
    echo "::warning title=Plugin folder size::$size_line"
  fi
fi
if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  echo "Plugin folder size: ${size_line#TOTAL: }" >> "$GITHUB_STEP_SUMMARY"
fi

if (( errors > 0 )); then
  cat >&2 <<'MSG'

FAIL: the plugin folder breaks a Claude directory file limit.

Every tracked file under plugins/cloud-finops/ is part of the plugin. A
non-image, non-font file over 256 KiB, or more than 512 files, puts each new
directory version on hold for a reviewer and stops auto-publishing. Move a
generated artefact out of the folder (build it in the release workflow, as
llms-full.txt is), split a reference, or prune files; do not raise the
ceilings. See CLAUDE.md "Claude directory listing".
MSG
  exit 1
fi

echo "OK: $count tracked files under $PLUGIN_DIR (ceiling $MAX_FILES), none over $MAX_FILE_BYTES bytes outside images and fonts."
