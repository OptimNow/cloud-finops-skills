#!/usr/bin/env bash
#
# check-marketplace-version.sh - Keep .claude-plugin/marketplace.json's
# metadata.version in sync with .claude-plugin/plugin.json's version. The
# marketplace catalogue must advertise the same version the plugin ships.
#
# Why this is a guard and not an auto-fixer: the marketplace version silently
# drifted three releases behind plugin.json (1.23.1 vs 1.26.x) because nothing
# bumps it - the release automation (auto-tag-on-plugin-bump.yml) only reads
# plugin.json. A workflow cannot auto-commit the fix to main either, because the
# "Protect main" ruleset requires a reviewed PR (a bot push to main is blocked).
# So enforcement at PR time is the robust equivalent: the marketplace bump rides
# the same PR that bumps plugin.json, and CI stays red until it does.
#
# Usage:
#   ./scripts/check-marketplace-version.sh    Report drift; exit 1 if found.
#
# Wired into CI (.github/workflows/marketplace-version-check.yml) so a PR that
# bumps plugin.json without bumping marketplace.json fails with a clear message.
# Same spirit as scripts/check-llms-txt.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

PLUGIN=".claude-plugin/plugin.json"
MARKET=".claude-plugin/marketplace.json"

plugin_ver="$(python3 -c "import json; print(json.load(open('$PLUGIN'))['version'])")"
market_ver="$(python3 -c "import json; print(json.load(open('$MARKET'))['metadata']['version'])")"

if [[ "$plugin_ver" != "$market_ver" ]]; then
  echo "FAIL: version drift between plugin and marketplace." >&2
  echo "  $PLUGIN  version          = $plugin_ver" >&2
  echo "  $MARKET  metadata.version = $market_ver" >&2
  echo "" >&2
  echo "Fix: set .metadata.version in $MARKET to \"$plugin_ver\" (in the same PR" >&2
  echo "that bumps plugin.json), then re-run. The two must always match." >&2
  exit 1
fi

echo "OK: marketplace.json metadata.version and plugin.json version agree ($plugin_ver)."
