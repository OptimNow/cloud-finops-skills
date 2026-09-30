#!/usr/bin/env bash
#
# check-plugin-skill-only.sh - the plugin ships the skill only, never the MCP
# server.
#
# Decision taken 2026-09-30 for the Claude directory submission: the plugin
# bundle (this repository) contains the skill, and the hosted MCP connector
# (https://cloud-finops-mcp.fly.dev/mcp) is listed in the directory separately
# and added by the user if they want the retrieval tools. The two serve the
# same library, so a plugin that also declared the server would load the six
# tool definitions into every session next to the skill and pay for the same
# content twice in context. README.md "Plugin and connector" is the
# user-facing statement; CLAUDE.md "Claude directory listing" is the
# maintainer rule.
#
# Two ways a plugin declares an MCP server, both refused here:
#   1. a `.mcp.json` file anywhere in the tree (Claude Code loads the one at
#      the plugin root; a stray copy deeper down is a mistake waiting to move);
#   2. an `mcpServers` key in .claude-plugin/plugin.json.
#
# The plugin.json check is a plain text match on the key, on purpose: it needs
# no jq or python, and the key is wrong wherever it appears in the manifest
# (the directory also blocks it inside `experimental`).
#
# Usage: ./scripts/check-plugin-skill-only.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

MANIFEST=".claude-plugin/plugin.json"
errors=0

# 1. No .mcp.json, tracked or sitting untracked at the root.
tracked="$(git ls-files -z | tr '\0' '\n' | grep -E '(^|/)\.mcp\.json$' || true)"
if [[ -n "$tracked" ]]; then
  while IFS= read -r p; do
    echo "REFUSED: $p is tracked; the plugin must not declare an MCP server" >&2
  done <<<"$tracked"
  errors=$((errors + 1))
fi
if [[ -e ".mcp.json" ]] && ! grep -qxF ".mcp.json" <<<"$tracked"; then
  echo "REFUSED: .mcp.json exists at the repository root (untracked); the plugin must not declare an MCP server" >&2
  errors=$((errors + 1))
fi

# 2. No mcpServers key in the manifest.
if [[ ! -f "$MANIFEST" ]]; then
  echo "FAIL: $MANIFEST not found; the plugin manifest must exist at the repository root." >&2
  exit 1
fi
if grep -q '"mcpServers"' "$MANIFEST"; then
  echo "REFUSED: $MANIFEST declares mcpServers; the plugin must not declare an MCP server" >&2
  errors=$((errors + 1))
fi

if (( errors > 0 )); then
  cat >&2 <<'MSG'

FAIL: the plugin would bundle the MCP server.

Decision (2026-09-30): the plugin ships the skill only. The hosted connector
is listed in the Claude directory on its own and users add it separately.
Bundling both loads the MCP tool definitions in every session beside the
skill and duplicates the same library in context. Remove .mcp.json and the
mcpServers key; point people at the "MCP hosted" row of the README install
table instead. See README.md "Plugin and connector" and CLAUDE.md "Claude
directory listing".
MSG
  exit 1
fi

echo "OK: no .mcp.json in the tree and no mcpServers key in $MANIFEST; the plugin is skill-only."
