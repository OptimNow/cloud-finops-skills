#!/usr/bin/env bash
# Cloud FinOps Skill installer
# Usage:
#   curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh | bash
#   curl -sL https://raw.githubusercontent.com/OptimNow/cloud-finops-skills/main/install.sh | bash -s -- --dir ~/my-project

set -euo pipefail

REPO="https://github.com/OptimNow/cloud-finops-skills.git"
SKILL_FOLDER="cloud-finops"
TARGET_DIR=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --dir)
      TARGET_DIR="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: install.sh [--dir /path/to/target]"
      exit 1
      ;;
  esac
done

# If no target specified, try to detect a sensible default
if [[ -z "$TARGET_DIR" ]]; then
  if [[ -d ".claude" ]]; then
    # We're inside a Claude Code project
    TARGET_DIR="."
  else
    TARGET_DIR="."
  fi
fi

echo ""
echo "  Cloud FinOps Skill - installer"
echo "  by OptimNow (https://optimnow.io)"
echo "  ----------------------------------------"
echo ""

# Create a temporary directory for cloning
TMPDIR=$(mktemp -d 2>/dev/null || mktemp -d -t 'finops-skill')
trap 'rm -rf "$TMPDIR"' EXIT

echo "  Downloading skill from GitHub..."
git clone --depth 1 --quiet "$REPO" "$TMPDIR/cloud-finops-skills"

# Copy the skill folder to the target
DEST="$TARGET_DIR/$SKILL_FOLDER"

if [[ -d "$DEST" ]]; then
  echo "  Existing installation found at $DEST"
  echo "  Updating..."
  rm -rf "$DEST"
fi

cp -r "$TMPDIR/cloud-finops-skills/$SKILL_FOLDER" "$DEST"

# Count installed files
FILE_COUNT=$(find "$DEST" -name "*.md" | wc -l | tr -d ' ')

echo ""
echo "  Installed to: $DEST"
echo "  Files: $FILE_COUNT markdown files"
echo ""

# Verify
if [[ -f "$DEST/SKILL.md" ]] && [[ -d "$DEST/references" ]]; then
  echo "  Verification: OK"
else
  echo "  Verification: FAILED - missing SKILL.md or references/"
  exit 1
fi

echo ""
echo "  Done. The skill is ready to use."
echo ""
echo "  If using Claude Code, add this to your project's .claude/settings.json:"
echo ""
echo "    { \"skills\": [\"$SKILL_FOLDER\"] }"
echo ""
echo "  Then test with:"
echo "    \"What are the first steps to manage AI inference costs?\""
echo ""
