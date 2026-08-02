#!/usr/bin/env bash
#
# check-skill-description.sh - guard the SKILL.md frontmatter description length.
#
# Claude.ai's skill uploader rejects a description over 1024 characters. The
# description is edited by most content PRs (every new domain wants a mention),
# and nothing else in CI notices when it grows. At the time this check was
# written it stood at 987 of 1024 - one more domain away from breaking the
# claude.ai upload path silently.
#
# Fails above HARD_LIMIT. Warns above WARN_LIMIT so the ceiling is visible
# before it is hit rather than at the moment it breaks.
#
# Usage: ./scripts/check-skill-description.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_MD="$REPO_ROOT/skills/cloud-finops/SKILL.md"

HARD_LIMIT=1024
WARN_LIMIT=950

if [[ ! -f "$SKILL_MD" ]]; then
  echo "ERROR: $SKILL_MD not found." >&2
  exit 1
fi

# Extract the frontmatter `description:` value, including folded continuation
# lines, and report its character count. Done in Python because the value spans
# multiple lines and YAML folding rules decide the real length.
length="$(python3 - "$SKILL_MD" <<'PY'
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML is required (pip install pyyaml).", file=sys.stderr)
    raise SystemExit(1)

text = open(sys.argv[1], encoding="utf-8").read()
if not text.startswith("---"):
    print("ERROR: SKILL.md has no YAML frontmatter.", file=sys.stderr)
    raise SystemExit(1)

parts = text.split("---", 2)
if len(parts) < 3:
    print("ERROR: SKILL.md frontmatter is not terminated.", file=sys.stderr)
    raise SystemExit(1)

fm = yaml.safe_load(parts[1]) or {}
desc = fm.get("description")
if not isinstance(desc, str) or not desc.strip():
    print("ERROR: SKILL.md frontmatter has no 'description' field.", file=sys.stderr)
    raise SystemExit(1)

print(len(desc))
PY
)"

if (( length > HARD_LIMIT )); then
  echo "FAIL: SKILL.md description is $length characters, over the $HARD_LIMIT limit." >&2
  echo "      claude.ai rejects a skill whose description exceeds $HARD_LIMIT chars," >&2
  echo "      so this would break the upload path. Tighten it before merging." >&2
  exit 1
fi

if (( length > WARN_LIMIT )); then
  echo "WARN: SKILL.md description is $length of $HARD_LIMIT characters."
  echo "      Little headroom left - consider tightening it in this PR."
  exit 0
fi

echo "OK: SKILL.md description is $length of $HARD_LIMIT characters."
