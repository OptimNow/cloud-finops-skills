"""Reference + playbook indexes built from YAML frontmatter.

Walks the bundled ``data/`` directory at startup, parses frontmatter from each
``.md`` file, and builds two in-memory indexes used by the tool surfaces:

- references (FCP frontmatter: domain, capability, phases, personas, maturity)
- playbooks  (named-pattern frontmatter: scope, service, waste_category,
  confidence)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

DATA_DIR = Path(__file__).resolve().parent / "data"
PLAYBOOKS_DIR = DATA_DIR / "playbooks"

# FCP fields we expose. Anything not listed here is ignored by the index.
FCP_SCALAR_FIELDS = (
    "fcp_domain",
    "fcp_capability",
    "fcp_maturity_entry",
)
FCP_LIST_FIELDS = (
    "fcp_capabilities_secondary",
    "fcp_phases",
    "fcp_personas_primary",
    "fcp_personas_collaborating",
)


@dataclass
class Reference:
    """One indexed reference file."""

    name: str
    path: Path
    description: str
    lines: int
    fcp_domain: str | None = None
    fcp_capability: str | None = None
    fcp_capabilities_secondary: list[str] = field(default_factory=list)
    fcp_phases: list[str] = field(default_factory=list)
    fcp_personas_primary: list[str] = field(default_factory=list)
    fcp_personas_collaborating: list[str] = field(default_factory=list)
    fcp_maturity_entry: str | None = None

    def to_dict(self) -> dict:
        """Stable JSON-friendly shape returned by the MCP tools."""
        return {
            "name": self.name,
            "description": self.description,
            "fcp_domain": self.fcp_domain,
            "fcp_capability": self.fcp_capability,
            "fcp_capabilities_secondary": self.fcp_capabilities_secondary,
            "fcp_phases": self.fcp_phases,
            "fcp_personas_primary": self.fcp_personas_primary,
            "fcp_personas_collaborating": self.fcp_personas_collaborating,
            "fcp_maturity_entry": self.fcp_maturity_entry,
            "lines": self.lines,
        }


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Empty frontmatter dict if none present."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        fm = {}
    body = parts[2].lstrip("\n")
    return fm, body


def _extract_description(fm: dict, body: str) -> str:
    """Pull a one-line description.

    Preference order: ``description`` frontmatter field → first non-blank
    blockquote line → first non-blank prose line.
    """
    if isinstance(fm.get("description"), str) and fm["description"].strip():
        return fm["description"].strip()

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue  # skip headings, we want the explainer line
        if stripped.startswith(">"):
            return stripped.lstrip("> ").strip()
        return stripped

    return ""


def _normalize_list(value) -> list[str]:
    """Coerce frontmatter list fields into ``list[str]``; tolerate scalars."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _parse_reference(path: Path) -> Reference:
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)

    name = str(fm.get("name") or path.stem)
    description = _extract_description(fm, body)
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)

    return Reference(
        name=name,
        path=path,
        description=description,
        lines=lines,
        fcp_domain=fm.get("fcp_domain") if isinstance(fm.get("fcp_domain"), str) else None,
        fcp_capability=fm.get("fcp_capability") if isinstance(fm.get("fcp_capability"), str) else None,
        fcp_capabilities_secondary=_normalize_list(fm.get("fcp_capabilities_secondary")),
        fcp_phases=_normalize_list(fm.get("fcp_phases")),
        fcp_personas_primary=_normalize_list(fm.get("fcp_personas_primary")),
        fcp_personas_collaborating=_normalize_list(fm.get("fcp_personas_collaborating")),
        fcp_maturity_entry=(
            fm.get("fcp_maturity_entry") if isinstance(fm.get("fcp_maturity_entry"), str) else None
        ),
    )


@lru_cache(maxsize=1)
def get_index() -> list[Reference]:
    """Return the full index of bundled references, sorted by name."""
    if not DATA_DIR.exists():
        return []
    refs = [_parse_reference(p) for p in DATA_DIR.glob("*.md")]
    refs.sort(key=lambda r: r.name)
    return refs


def get_by_name(name: str) -> Reference | None:
    """Look up a reference by its ``name`` (frontmatter or filename stem)."""
    for ref in get_index():
        if ref.name == name:
            return ref
    return None


# --- playbooks --------------------------------------------------------------


@dataclass
class Playbook:
    """One indexed named-pattern playbook.

    Playbooks live in ``skills/cloud-finops/playbooks/`` and follow a different
    frontmatter schema from references: a single waste-pattern slug plus
    ``scope``, ``service``, ``waste_category``, and ``confidence``.
    """

    name: str
    path: Path
    title: str
    scope: str | None = None
    service: str | None = None
    waste_category: str | None = None
    confidence: str | None = None
    lines: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "scope": self.scope,
            "service": self.service,
            "waste_category": self.waste_category,
            "confidence": self.confidence,
            "lines": self.lines,
        }


def _extract_title(body: str, fallback: str) -> str:
    """Pull the first ``#`` heading as the human-readable title."""
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped.lstrip("# ").strip()
    return fallback


def _parse_playbook(path: Path) -> Playbook:
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text)

    name = str(fm.get("name") or path.stem)
    title = _extract_title(body, fallback=name)
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)

    def _scalar(key: str) -> str | None:
        value = fm.get(key)
        return value if isinstance(value, str) else None

    return Playbook(
        name=name,
        path=path,
        title=title,
        scope=_scalar("scope"),
        service=_scalar("service"),
        waste_category=_scalar("waste_category"),
        confidence=_scalar("confidence"),
        lines=lines,
    )


@lru_cache(maxsize=1)
def get_playbook_index() -> list[Playbook]:
    """Return the full index of bundled playbooks, sorted by name."""
    if not PLAYBOOKS_DIR.exists():
        return []
    playbooks = [_parse_playbook(p) for p in PLAYBOOKS_DIR.glob("*.md")]
    playbooks.sort(key=lambda p: p.name)
    return playbooks


def get_playbook_by_name(name: str) -> Playbook | None:
    """Look up a playbook by its slug (frontmatter ``name`` or filename stem)."""
    for pb in get_playbook_index():
        if pb.name == name:
            return pb
    return None


def reset_cache() -> None:
    """Test hook: drop both cached indexes so the next call rebuilds them."""
    get_index.cache_clear()
    get_playbook_index.cache_clear()
