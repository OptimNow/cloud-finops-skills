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

import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
REFERENCES_SRC = REPO_ROOT / "skills" / "cloud-finops" / "references"
PLAYBOOKS_SRC = REPO_ROOT / "skills" / "cloud-finops" / "playbooks"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"

DATA_ROOT = Path(__file__).resolve().parents[1] / "src" / "cloud_finops_mcp" / "data"
REFERENCES_DEST = DATA_ROOT
PLAYBOOKS_DEST = DATA_ROOT / "playbooks"
STAMP_FILE = DATA_ROOT / "content_version.txt"


def _sync(label: str, src_dir: Path, dest_dir: Path, *, skip: set[str]) -> int:
    """Mirror ``*.md`` from ``src_dir`` into ``dest_dir``.

    Returns the number of files copied, or -1 if the source could not supply
    any content. Falls back gracefully when ``src_dir`` is missing
    (sdist-build case) but ``dest_dir`` is already populated.
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

    # Resolve the candidate list before touching the destination. An existing
    # but empty source would otherwise wipe the bundle and report success,
    # producing a wheel with an empty catalogue that only fails at runtime.
    candidates = []
    for src in sorted(src_dir.glob("*.md")):
        if src.name in skip:
            continue
        # Skip symlinks: a malicious *.md symlink landed in the skill dir
        # (via a bad PR) would otherwise have its target's content copied
        # verbatim into the published wheel. We only ship real reference files.
        if src.is_symlink():
            print(f"[sync_references] {label}: skipping symlink {src.name}")
            continue
        candidates.append(src)

    if not candidates:
        print(
            f"[sync_references] {label}: source directory exists but contains "
            f"no eligible *.md files: {src_dir}. Refusing to empty the bundle "
            f"at {dest_dir} ({len(existing)} file(s) left untouched).",
            file=sys.stderr,
        )
        return -1

    # Wipe stale .md files so deletions upstream propagate to the bundle.
    for stale in existing:
        stale.unlink()

    for src in candidates:
        shutil.copy2(src, dest_dir / src.name)

    copied = len(candidates)
    print(f"[sync_references] {label}: copied {copied} file(s) to {dest_dir}")
    return copied


def _content_version() -> str:
    """The released version the content belongs to, from plugin.json.

    plugin.json is the canonical version holder (the release train bumps it
    and everything else follows). It is absent when building from an sdist,
    where the repo is not around - the caller falls back to the stamp that
    travelled with the pre-bundled data.
    """
    try:
        return str(json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["version"])
    except (OSError, KeyError, ValueError):
        return "unknown"


def _write_stamp(refs: int, playbooks: int) -> None:
    """Record what was synced, so a running server can say what it serves.

    The server logs this file at startup (see ``server._warm_indexes``). It
    exists because a stale bundle is otherwise invisible from the outside:
    the 2026-08-19 audit had to fingerprint deployments by per-file line
    counts to discover they were serving content two releases old.
    """
    version = _content_version()
    if version == "unknown" and STAMP_FILE.exists():
        # sdist rebuild: no repo, no plugin.json - keep the stamp written at
        # original build time rather than overwriting it with "unknown".
        print(f"[sync_references] keeping existing stamp at {STAMP_FILE}")
        return
    synced_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    STAMP_FILE.write_text(
        f"version: {version}\n"
        f"synced_at: {synced_at}\n"
        f"references: {refs}\n"
        f"playbooks: {max(playbooks, 0)}\n",
        encoding="utf-8",
    )
    print(f"[sync_references] wrote {STAMP_FILE} (version {version}, synced {synced_at})")


def main() -> int:
    refs = _sync("references", REFERENCES_SRC, REFERENCES_DEST, skip=set())
    playbooks = _sync(
        "playbooks", PLAYBOOKS_SRC, PLAYBOOKS_DEST, skip={"README.md"}
    )

    if refs < 0:
        # Either the source is missing with nothing pre-bundled, or it is
        # present but empty. Both would ship a server with no catalogue, so
        # the build fails here rather than at first query.
        return 1
    _write_stamp(refs, playbooks)
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
