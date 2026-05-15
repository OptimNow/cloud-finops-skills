#!/usr/bin/env python3
"""Copy ``skills/cloud-finops/references/*.md`` and ``skills/cloud-finops/playbooks/*.md`` into
the bundled ``data/`` folder.

Runs automatically before each wheel build (declared in ``pyproject.toml`` as a
``hatch-build-scripts`` hook). Also intended to be run manually after
``pip install -e .`` so the editable install picks up the latest reference
content::

    python scripts/sync_references.py

The script is idempotent and clears the destination folders first to drop
files that have been removed upstream. The ``playbooks/README.md`` file is
intentionally skipped: it documents the format for human contributors and is
not a runbook the agent should retrieve.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_SRC = REPO_ROOT / "skills" / "cloud-finops" / "references"
PLAYBOOKS_SRC = REPO_ROOT / "skills" / "cloud-finops" / "playbooks"

DATA_ROOT = Path(__file__).resolve().parents[1] / "src" / "cloud_finops_mcp" / "data"
REFERENCES_DEST = DATA_ROOT
PLAYBOOKS_DEST = DATA_ROOT / "playbooks"


def _sync(label: str, src_dir: Path, dest_dir: Path, *, skip: set[str]) -> int:
    """Mirror ``*.md`` from ``src_dir`` into ``dest_dir``.

    Returns the number of files copied. Falls back gracefully when ``src_dir`` is
    missing (sdist-build case) but ``dest_dir`` is already populated.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    existing = [p for p in dest_dir.glob("*.md")]

    if not src_dir.is_dir():
        if existing:
            print(
                f"[sync_references] {label}: source missing; using "
                f"{len(existing)} pre-bundled file(s) at {dest_dir}"
            )
            return len(existing)
        print(
            f"[sync_references] {label}: source directory not found and no "
            f"pre-bundled files present: {src_dir}",
            file=sys.stderr,
        )
        return -1

    # Wipe stale .md files so deletions upstream propagate to the bundle.
    for stale in existing:
        stale.unlink()

    copied = 0
    for src in sorted(src_dir.glob("*.md")):
        if src.name in skip:
            continue
        shutil.copy2(src, dest_dir / src.name)
        copied += 1

    print(f"[sync_references] {label}: copied {copied} file(s) to {dest_dir}")
    return copied


def main() -> int:
    refs = _sync("references", REFERENCES_SRC, REFERENCES_DEST, skip=set())
    playbooks = _sync(
        "playbooks", PLAYBOOKS_SRC, PLAYBOOKS_DEST, skip={"README.md"}
    )

    if refs < 0:
        return 1
    if playbooks < 0:
        # Playbooks are optional - older skill versions may not have shipped
        # them. Warn but do not fail the build.
        print(
            "[sync_references] WARNING: playbooks unavailable; the MCP "
            "server will still expose references but list_playbooks() will "
            "be empty.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
