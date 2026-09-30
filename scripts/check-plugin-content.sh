#!/usr/bin/env bash
#
# check-plugin-content.sh - the plugin folder holds markdown and a licence, and
# nothing the Claude directory's security scan reads as a risk.
#
# Background (2026-10-01): the first portal validation, with the repository
# root as the plugin folder, came back with 13 policy holds and 6 warnings. Not
# one came from the skill. They came from developer tooling next to it: image
# files named in CLAUDE.md, INSTALLATION.md and the guard scripts
# (UNREAD_ASSET_REFERENCED), a `$VAR` next to a URL in install.sh, CLAUDE.md
# and one playbook (MCP_FORWARDS_CREDENTIAL_ENV), curl-pipe-to-shell lines in
# the READMEs and the workflows (RUNTIME_FETCH_EXEC), and CLAUDE.md at the
# plugin root (ROOT_CLAUDE_MD). A hold does not block a submission, but every
# new version then waits for a human reviewer, which ends auto-publishing of
# the twice-monthly content releases. The plugin moved to plugins/cloud-finops/
# so the scanner sees only what a user installs; this guard keeps that folder
# free of the same patterns.
#
# Refused inside plugins/cloud-finops/:
#   1. any file that is not markdown, except the LICENSE, plugin.json, the
#      plugin README and the listing icon at .claude-plugin/icon.svg (an SVG
#      is a text file the scanner reads; the portal warns when no icon is
#      present). So: no raster image, no script, no font, no archive;
#   2. an uppercase `$NAME` or `${NAME}` shell variable on a line that also
#      carries a URL (the scan reads that as a credential forwarded to a host;
#      a runbook writes a placeholder such as `<ANTHROPIC_ADMIN_KEY>` instead).
#      Lowercase names are not matched: `$filter` and `$top` are OData query
#      parameters on Azure REST URLs, and `$(date ...)` is command substitution;
#      the root-folder scan of 2026-10-01 flagged neither;
#   3. a download-and-execute pattern: `curl ...| sh`, `wget ...| bash`;
#   4. a package launcher that fetches and runs code: `npx`, `bunx`, `uvx`,
#      `pipx run`, `uv run`, `pnpm dlx`, `yarn dlx` (recommend the tool, link
#      its repository, show the installed command).
#
# Usage: ./scripts/check-plugin-content.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

PLUGIN_DIR="plugins/cloud-finops"
errors=0

if [[ ! -d "$PLUGIN_DIR" ]]; then
  echo "FAIL: $PLUGIN_DIR does not exist." >&2
  exit 1
fi

# 1. File types.
while IFS= read -r -d '' path; do
  rel="${path#"$PLUGIN_DIR"/}"
  case "$rel" in
    LICENSE|README.md|.claude-plugin/plugin.json|.claude-plugin/icon.svg) continue ;;
    *.md) continue ;;
  esac
  echo "REFUSED: $path is not a markdown file; the plugin folder ships text content only" >&2
  errors=$((errors + 1))
done < <(git ls-files -z -- "$PLUGIN_DIR")

# 2 to 4. Line patterns, over every tracked text file in the folder.
while IFS= read -r -d '' path; do
  # A shell variable on a line that carries a URL.
  if hits="$(grep -nE '\$\{?[A-Z][A-Z0-9_]{2,}\}?' "$path" | grep -E 'https?://' || true)"; [[ -n "$hits" ]]; then
    while IFS= read -r line; do
      echo "REFUSED: $path:${line%%:*}: a \$VAR next to a URL reads as a forwarded credential; use a <PLACEHOLDER>" >&2
    done <<<"$hits"
    errors=$((errors + 1))
  fi
  # Download-and-execute.
  if hits="$(grep -nE '(curl|wget)[^|]*\|[[:space:]]*(sudo[[:space:]]+)?(ba|z|da)?sh\b' "$path" || true)"; [[ -n "$hits" ]]; then
    while IFS= read -r line; do
      echo "REFUSED: $path:${line%%:*}: curl-pipe-to-shell pattern" >&2
    done <<<"$hits"
    errors=$((errors + 1))
  fi
  # Package launchers.
  if hits="$(grep -nE '(^|[[:space:]`(])(npx|bunx|uvx|pnpm dlx|yarn dlx|pipx run|uv run)([[:space:]]|$)' "$path" || true)"; [[ -n "$hits" ]]; then
    while IFS= read -r line; do
      echo "REFUSED: $path:${line%%:*}: package launcher; link the tool's repository and show the installed command" >&2
    done <<<"$hits"
    errors=$((errors + 1))
  fi
done < <(git ls-files -z -- "$PLUGIN_DIR")

if (( errors > 0 )); then
  cat >&2 <<'MSG'

FAIL: the plugin folder carries a pattern the Claude directory scan holds
for a reviewer. See the header of this script for the four rules and
CLAUDE.md "Claude directory listing" for the decision behind them. Fix the
content; do not move developer tooling into plugins/cloud-finops/.
MSG
  exit 1
fi

echo "OK: $PLUGIN_DIR holds markdown, LICENSE, the manifest and the SVG icon only, with no credential variable beside a URL, no curl-pipe-to-shell and no package launcher."
