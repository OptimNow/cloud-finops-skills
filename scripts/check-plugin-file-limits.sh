#!/usr/bin/env bash
#
# check-plugin-file-limits.sh - keep every tracked file inside the Claude plugin
# directory's per-file and file-count limits.
#
# The plugin folder is plugins/cloud-finops/ (it holds .claude-plugin/plugin.json),
# and the directory scans every file under it on each commit it picks up from
# `main`. Two of its checks do not block a submission but put every new version
# on hold for a reviewer, which is what would stop the twice-monthly content
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
# Usage: ./scripts/check-plugin-file-limits.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PLUGIN_DIR="plugins/cloud-finops"
MAX_FILE_BYTES=262144   # 256 KiB, the directory's per-file ceiling
MAX_FILES=480           # directory holds a version above 512; fail early

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
