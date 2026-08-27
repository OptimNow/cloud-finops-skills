"""Reference + playbook indexes built from YAML frontmatter.

Walks the bundled ``data/`` directory at startup, parses frontmatter from each
``.md`` file, and builds two in-memory indexes used by the tool surfaces:

- references (FCP frontmatter: domain, capability, phases, personas, maturity)
- playbooks  (named-pattern frontmatter: scope, service, waste_category,
  confidence)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent / "data"
PLAYBOOKS_DIR = DATA_DIR / "playbooks"
CONTENT_VERSION_FILE = DATA_DIR / "content_version.txt"

# The FCP fields the index exposes are the ones named field-by-field in
# ``Reference`` and ``_parse_reference`` below - there is no registry to edit.

# Frontmatter is delimited by a ``---`` line at the very start of the file and
# the next ``---`` line on its own. Anchoring both ends matters: a substring
# match treats a leading markdown horizontal rule as an opening fence, and a
# value containing ``---`` mid-line as a closing one. The negative lookahead
# rejects the remaining horizontal-rule case - a rule is followed by a blank
# line, real frontmatter opens straight onto its first key.
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(?![ \t]*\n)(.*?)\n---[ \t]*(?:\n|\Z)", re.S)

# Every listing entry is paid for once per discovery call, so the descriptions
# are summarised rather than shipped whole: the full text runs to a mean of
# ~350 characters over three sentences, and only the first one discriminates
# between references. 200 characters is the measured point where every
# reference's opening sentence still survives intact for the large majority of
# the library - a harder cap starts cutting the clause that names the tools or
# providers a file covers, which is precisely the clause an agent chooses on.
SUMMARY_LIMIT = 200

# Four characters per token is the rough-and-ready estimate the whole repo uses
# for English markdown. It exists so an agent can tell a 3K-token reference from
# a 26K-token one BEFORE fetching it, not to be accurate to the token.
CHARS_PER_TOKEN = 4

_SENTENCE_BREAK_RE = re.compile(r"(?<=[.!?])\s+")


def approx_tokens(chars: int) -> int:
    """Rough token count for a body of ``chars`` characters."""
    return round(chars / CHARS_PER_TOKEN)


def summarise(text: str, limit: int = SUMMARY_LIMIT) -> str:
    """Shorten a description to its first sentence, hard-capped at ``limit``.

    Whitespace is collapsed first so a description wrapped across source lines
    does not carry its line breaks into the JSON payload.
    """
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    first = _SENTENCE_BREAK_RE.split(text, maxsplit=1)[0]
    if len(first) <= limit:
        return first
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-") + "..."


@dataclass
class Reference:
    """One indexed reference file."""

    name: str
    path: Path
    description: str
    lines: int
    chars: int = 0
    title: str = ""
    fcp_domain: str | None = None
    fcp_capability: str | None = None
    fcp_capabilities_secondary: list[str] = field(default_factory=list)
    fcp_phases: list[str] = field(default_factory=list)
    fcp_personas_primary: list[str] = field(default_factory=list)
    fcp_personas_collaborating: list[str] = field(default_factory=list)
    fcp_maturity_entry: str | None = None

    def to_dict(self) -> dict:
        """Stable JSON-friendly shape returned by the MCP tools.

        This is a *listing* entry, not the whole record. Two facets are
        deliberately withheld: ``fcp_capabilities_secondary`` and
        ``fcp_personas_collaborating``. Both stay fully filterable through
        ``find_references`` - they are dropped from the payload because they
        do not help a caller *choose* (a broad persona collaborates on nearly
        every file, which is why ``persona_primary_only`` exists) while
        costing ~17% of a discovery call that every session makes.

        ``approx_tokens`` replaces the old ``lines`` field: an agent budgets in
        tokens, and the whole point of the hint is to let it tell a 3K-token
        reference from a 26K-token one before paying for the body.
        """
        return {
            "name": self.name,
            "title": self.title,
            "description": summarise(self.description),
            "fcp_domain": self.fcp_domain,
            "fcp_capability": self.fcp_capability,
            "fcp_phases": self.fcp_phases,
            "fcp_personas_primary": self.fcp_personas_primary,
            "fcp_maturity_entry": self.fcp_maturity_entry,
            "approx_tokens": approx_tokens(self.chars),
        }


def _split_frontmatter(text: str, source: str = "<unknown>") -> tuple[dict, str]:
    """Return (frontmatter_dict, body). Empty frontmatter dict if none present.

    A malformed frontmatter block is not fatal - the file stays in the index and
    is still retrievable by name - but it silently loses every facet, so it
    vanishes from ``find_references`` / ``find_playbooks`` results. Log it at
    WARNING so the failure is visible rather than mysterious.

    Both delimiters are matched as whole lines. Substring matching got this
    wrong two ways: a file opening with a markdown horizontal rule was read as
    frontmatter running to the next ``---`` in the document, and a value
    containing ``---`` mid-line truncated the block, dropping every facet
    declared after it.
    """
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        return {}, text
    try:
        fm = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError as exc:
        logger.warning(
            "Malformed YAML frontmatter in %s - facets unavailable, the file will "
            "not appear in any faceted query: %s",
            source,
            exc,
        )
        fm = {}
    if not isinstance(fm, dict):
        logger.warning(
            "Frontmatter in %s parsed as %s, expected a mapping - facets unavailable.",
            source,
            type(fm).__name__,
        )
        fm = {}
    body = text[match.end() :].lstrip("\n")
    return fm, body


def _extract_description(fm: dict, body: str) -> str:
    """Pull a one-line description.

    Preference order: ``description`` frontmatter field → first blockquote
    (all its contiguous lines joined, since the visible description under the
    H1 usually wraps across several ``>`` lines and taking only the first cut
    it mid-sentence) → first non-blank prose line.
    """
    if isinstance(fm.get("description"), str) and fm["description"].strip():
        return fm["description"].strip()

    lines = body.splitlines()
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue  # skip headings, we want the explainer line
        if stripped.startswith(">"):
            parts: list[str] = []
            for follow in lines[i:]:
                follow_stripped = follow.strip()
                if not follow_stripped.startswith(">"):
                    break
                text = follow_stripped.lstrip("> ").strip()
                if not text:
                    break  # an empty '>' separates paragraphs; keep the first
                parts.append(text)
            return " ".join(parts)
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
    fm, body = _split_frontmatter(text, source=path.name)

    name = str(fm.get("name") or path.stem)
    description = _extract_description(fm, body)
    title = _extract_title(body, fallback=name)
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)

    return Reference(
        name=name,
        path=path,
        description=description,
        title=title,
        lines=lines,
        chars=len(text),
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


def _warn_on_duplicate_names(items: list, label: str) -> None:
    """Log any ``name`` claimed by more than one bundled file.

    Lookups are first-match, so a duplicate silently shadows whichever file
    sorts later: ``get_reference(name=...)`` would return one body while the
    other became unreachable, with nothing anywhere saying so. No duplicates
    exist today; this exists so introducing one is visible rather than latent.
    """
    seen: dict[str, str] = {}
    for item in items:
        first = seen.get(item.name)
        if first is None:
            seen[item.name] = item.path.name
        else:
            logger.error(
                "Duplicate %s name %r: %s shadows %s. The shadowed file is "
                "unreachable by name; rename one of them.",
                label,
                item.name,
                first,
                item.path.name,
            )


@lru_cache(maxsize=1)
def get_index() -> list[Reference]:
    """Return the full index of bundled references, sorted by name.

    An empty result means the wheel was built without its data bundle. The
    server still starts and every tool still answers, just with nothing in it -
    which is indistinguishable from a working server to any caller. Log loudly
    so a mis-built package is diagnosable from the server's own output.
    """
    if not DATA_DIR.exists():
        logger.error(
            "Reference data directory is missing (%s). This package was built "
            "without its content bundle; every reference tool will return empty "
            "results.",
            DATA_DIR,
        )
        return []
    refs = [_parse_reference(p) for p in DATA_DIR.glob("*.md")]
    if not refs:
        logger.error(
            "No reference files found in %s. This package was built without its "
            "content bundle; every reference tool will return empty results.",
            DATA_DIR,
        )
    refs.sort(key=lambda r: r.name)
    _warn_on_duplicate_names(refs, "reference")
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
    chars: int = 0

    def to_dict(self) -> dict:
        """Listing entry. Carries the same ``approx_tokens`` hint as a reference.

        Playbooks are uniformly small, so the hint rarely changes a decision on
        one of them - it earns its ~8% of the payload when an agent is deciding
        how many to pull in a single answer.
        """
        return {
            "name": self.name,
            "title": self.title,
            "scope": self.scope,
            "service": self.service,
            "waste_category": self.waste_category,
            "confidence": self.confidence,
            "approx_tokens": approx_tokens(self.chars),
        }


def _extract_title(body: str, fallback: str) -> str:
    """Pull the first ``#`` heading as the human-readable title.

    Only the two-character ``"# "`` marker is removed. ``lstrip("# ")`` strips
    every leading ``#`` and space, which silently ate the first word of a
    heading like ``# #1 Top Pattern``.
    """
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return fallback


def _parse_playbook(path: Path) -> Playbook:
    text = path.read_text(encoding="utf-8")
    fm, body = _split_frontmatter(text, source=f"playbooks/{path.name}")

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
        chars=len(text),
    )


@lru_cache(maxsize=1)
def get_playbook_index() -> list[Playbook]:
    """Return the full index of bundled playbooks, sorted by name.

    Same failure mode as :func:`get_index` - an empty bundle looks like a
    healthy server serving nothing. Log it.
    """
    if not PLAYBOOKS_DIR.exists():
        logger.error(
            "Playbook data directory is missing (%s). This package was built "
            "without its content bundle; every playbook tool will return empty "
            "results.",
            PLAYBOOKS_DIR,
        )
        return []
    playbooks = [_parse_playbook(p) for p in PLAYBOOKS_DIR.glob("*.md")]
    if not playbooks:
        logger.error(
            "No playbook files found in %s. This package was built without its "
            "content bundle; every playbook tool will return empty results.",
            PLAYBOOKS_DIR,
        )
    playbooks.sort(key=lambda p: p.name)
    _warn_on_duplicate_names(playbooks, "playbook")
    return playbooks


def get_playbook_by_name(name: str) -> Playbook | None:
    """Look up a playbook by its slug (frontmatter ``name`` or filename stem)."""
    for pb in get_playbook_index():
        if pb.name == name:
            return pb
    return None


# --- section splitting ------------------------------------------------------
#
# Section-level retrieval exists because the pattern catalogues are enumerated
# lists: an agent asking about S3 lifecycle wants one of the seven headings in
# finops-aws-patterns, not all 26K tokens of it.
#
# H3 is not optional here, it is the whole point. finops-aws-patterns carries
# ONE H2 and seven H3s; finops-azure-patterns one H2 and five H3s. An
# H2-only splitter would leave the two biggest files in the library
# un-sectionable, which is exactly the case section retrieval was built for.

# ATX headings only. Setext (underlined) headings do not appear in this
# content set and matching them would need lookahead over the next line.
_HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(\S.*?)[ \t]*$")
# Fenced code blocks contain shell comments (``## comment``) and markdown
# examples. A heading found inside a fence is not a section boundary; missing
# this splits a section in half at a line the reader never sees as a heading.
_FENCE_RE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})")

_SECTION_LEVELS = (2, 3)

# Headings often end in a count the author maintains by hand ("Compute
# Optimization Patterns (42)"). An agent will not know the number, so it is
# stripped before matching.
_TRAILING_COUNT_RE = re.compile(r"\s*\(\s*\d+\s*\)\s*$")
_WORD_RE = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Section:
    """One H2/H3 span of a reference body, as line offsets into that body."""

    heading: str
    level: int
    start: int  # index of the heading line
    end: int  # exclusive

    @property
    def label(self) -> str:
        """``"### Storage Optimization Patterns (28)"`` - heading with its level.

        The level marker is what tells a caller which headings nest inside
        which, so an error listing them is navigable rather than flat.
        """
        return f"{'#' * self.level} {self.heading}"


def _normalise_heading(text: str) -> str:
    """Casefolded, punctuation-free token string used for tolerant matching."""
    return " ".join(_WORD_RE.findall(_TRAILING_COUNT_RE.sub("", text).lower()))


def _atx_headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """``(line index, level, text)`` for every ATX heading outside a code fence."""
    found: list[tuple[int, int, str]] = []
    fence: str | None = None
    for i, line in enumerate(lines):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)[0]
            fence = marker if fence is None else (None if fence == marker else fence)
            continue
        if fence is not None:
            continue
        heading = _HEADING_RE.match(line)
        if heading:
            found.append((i, len(heading.group(1)), heading.group(2).strip()))
    return found


def split_sections(body: str, levels: tuple[int, ...] = _SECTION_LEVELS) -> list[Section]:
    """Split a reference body into its H2/H3 sections, in document order.

    A section runs from its heading to the next heading of the same or a
    higher level, so an H2 span contains its H3 children and an H3 span stops
    at its sibling. Both are offered: an agent that wants the whole storage
    chapter and one that wants a single pattern group are asking for
    different-sized chunks of the same file.
    """
    lines = body.splitlines()
    headings = _atx_headings(lines)
    sections: list[Section] = []
    for index, (line_no, level, text) in enumerate(headings):
        if level not in levels:
            continue
        end = len(lines)
        for next_line, next_level, _ in headings[index + 1 :]:
            if next_level <= level:
                end = next_line
                break
        sections.append(Section(heading=text, level=level, start=line_no, end=end))
    return sections


def section_text(body: str, section: Section) -> str:
    """The markdown of one section, heading line included."""
    return "\n".join(body.splitlines()[section.start : section.end]).rstrip() + "\n"


def section_labels(body: str, levels: tuple[int, ...] = _SECTION_LEVELS) -> list[str]:
    """Every section heading, level marker included, in document order."""
    return [s.label for s in split_sections(body, levels)]


def find_sections(
    body: str, query: str, levels: tuple[int, ...] = _SECTION_LEVELS
) -> list[Section]:
    """Sections whose heading matches ``query``, best tier first.

    Matching is deliberately tolerant, because the caller is a model writing a
    natural phrase from a user's question, not a string it copied out of the
    file. Four tiers are tried in order and only the first non-empty one is
    returned, so a exact heading is never buried under loose substring hits:

    1. the normalised heading equals the query
    2. the heading starts with the query (``"storage"`` -> "Storage
       Optimization Patterns (28)")
    3. the query appears anywhere in the heading
    4. every word of the query appears as a word of the heading, in any order

    Within a tier, shallower headings come first: asking for "storage" when
    both an H2 chapter and an H3 subsection match should hand back the chapter.
    """
    normalised = _normalise_heading(query)
    if not normalised:
        return []
    query_words = normalised.split()
    tiers: list[list[Section]] = [[], [], [], []]
    for section in split_sections(body, levels):
        heading = _normalise_heading(section.heading)
        if heading == normalised:
            tiers[0].append(section)
        elif heading.startswith(normalised):
            tiers[1].append(section)
        elif normalised in heading:
            tiers[2].append(section)
        elif all(word in heading.split() for word in query_words):
            tiers[3].append(section)
    for tier in tiers:
        if tier:
            return sorted(tier, key=lambda s: (s.level, s.start))
    return []


def strip_frontmatter(text: str, source: str = "<unknown>") -> str:
    """The body of a bundled file with any YAML frontmatter block removed."""
    return _split_frontmatter(text, source=source)[1]


def content_version_summary() -> str | None:
    """One-line summary of the bundle stamp, or ``None`` if there is none.

    The stamp (``data/content_version.txt``) is written by
    ``scripts/sync_references.py`` and names the release version and sync date
    the bundled content belongs to. ``None`` means the bundle predates the
    stamp or is an editable install whose sync has not been re-run.
    """
    try:
        text = CONTENT_VERSION_FILE.read_text(encoding="utf-8")
    except OSError:
        return None
    fields: dict[str, str] = {}
    for line in text.splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    version = fields.get("version", "unknown")
    synced_at = fields.get("synced_at", "unknown date")
    return f"content version {version}, synced {synced_at}"


def reset_cache() -> None:
    """Test hook: drop both cached indexes so the next call rebuilds them."""
    get_index.cache_clear()
    get_playbook_index.cache_clear()
