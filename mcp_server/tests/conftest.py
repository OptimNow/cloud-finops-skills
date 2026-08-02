"""Shared test fixtures.

The tests run against the real bundled ``data/`` folder. We assume
``scripts/sync_references.py`` has been run at least once; otherwise the
fixture below will populate it on the fly so ``pytest`` works in a fresh
checkout.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parents[1] / "src" / "cloud_finops_mcp" / "data"
PLAYBOOKS_DIR = DATA_DIR / "playbooks"
REFERENCES_SOURCE = REPO_ROOT / "skills" / "cloud-finops" / "references"
PLAYBOOKS_SOURCE = REPO_ROOT / "skills" / "cloud-finops" / "playbooks"


def _ensure_dir(dest: Path, source: Path, *, skip: set[str]) -> None:
    if any(dest.glob("*.md")):
        return
    if not source.is_dir():
        pytest.skip(f"source missing at {source}")
    dest.mkdir(parents=True, exist_ok=True)
    for src in source.glob("*.md"):
        if src.name in skip:
            continue
        shutil.copy2(src, dest / src.name)


@pytest.fixture(autouse=True, scope="session")
def _populate_data() -> None:
    _ensure_dir(DATA_DIR, REFERENCES_SOURCE, skip=set())
    _ensure_dir(PLAYBOOKS_DIR, PLAYBOOKS_SOURCE, skip={"README.md"})
    # Ensure a fresh import picks up data/ — important when the tree was
    # populated mid-session.
    sys.modules.pop("cloud_finops_mcp.metadata", None)


# Authoritative reference/playbook counts read from disk at collection
# time. Tests assert the function output matches these counts, so adding a
# new reference or playbook does not require hand-editing count assertions
# across multiple test files. The >= 20 floor keeps an empty or misplaced
# source directory from turning every count assertion into 0 == 0.
@pytest.fixture(scope="session")
def expected_references() -> int:
    count = len(list(REFERENCES_SOURCE.glob("*.md")))
    assert count >= 20, f"suspiciously few references in {REFERENCES_SOURCE}"
    return count


@pytest.fixture(scope="session")
def expected_playbooks() -> int:
    count = len([p for p in PLAYBOOKS_SOURCE.glob("*.md") if p.name != "README.md"])
    assert count >= 20, f"suspiciously few playbooks in {PLAYBOOKS_SOURCE}"
    return count
