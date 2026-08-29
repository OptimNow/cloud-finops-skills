"""Conformance checks over the bundled content.

These tests guard the failure class where a content PR silently degrades
retrieval without breaking anything visibly:

- a broken YAML frontmatter block leaves the file in ``list_*`` but strips
  every facet, so it disappears from ``find_*`` (F8)
- a facet value that exists in the data but is not advertised in the tool
  docstring, or vice versa, makes the tool surface lie to the agent (F9)

Both are invisible to a reviewer reading the markdown diff, which is why they
are pinned here rather than left to the PR checklist.
"""

from __future__ import annotations

import logging
import re

import pytest

from cloud_finops_mcp import metadata, server, tools

# Advertised in the find_playbooks docstring but carried by no playbook today.
# The taxonomy defines the category and the tool offers it as a filter, so a
# caller can ask for it and get an empty result. Tracked as a coverage gap in
# docs/ROADMAP.md. If you add a playbook for one of these, delete it from
# this set - the test will tell you to. Empty since PR #177 closed the last
# one (commitment-mismatch, 2026-08-21); kept so the ratchet still guards
# any future enum-without-content regression.
KNOWN_EMPTY_FACET_VALUES: set[str] = set()

# The eight waste categories are defined in the taxonomy reference as
# ``## Category N: <phrase>`` headings; the facet vocabulary is a kebab-case
# shortening of those phrases.
CATEGORY_HEADING_RE = re.compile(r"^## Category \d+: (.+?)\s*$", re.M)


def _advertised_in(fn, facet: str) -> set[str]:
    """Pull the double-backtick-quoted values a docstring advertises for a facet.

    The docstring is the contract the agent reads, so these tests parse it
    rather than a duplicate list held in code. Single backticks are used for
    file and field references and are deliberately not picked up here.
    """
    doc = fn.__doc__ or ""
    # Google-style Args: entries sit at 8 spaces, their continuations at 12,
    # and the following section ("Returns:", prose) dedents to 4 or less. Stop
    # at the next entry or at that dedent, so trailing prose in the last entry
    # is not read as part of its vocabulary.
    m = re.search(
        rf"^ {{8}}{facet}: (.+?)(?=^ {{8}}\w+:|^ {{0,4}}\S|\Z)", doc, re.S | re.M
    )
    assert m, f"{fn.__module__}.{fn.__name__} documents no {facet!r} facet"
    # server.py quotes its values (``"aws"``), tools.py does not (``aws``).
    return {v.strip('"').strip("'") for v in re.findall(r"``([^`]+)``", m.group(1))}


def _advertised(facet: str) -> set[str]:
    """The vocabulary the agent-facing docstring advertises."""
    return _advertised_in(server.find_playbooks, facet)


@pytest.mark.parametrize("facet", ["scope", "waste_category", "confidence"])
def test_tools_and_server_docstrings_agree(facet: str) -> None:
    """The two copies of the facet vocabulary must not drift apart.

    The vocabulary is written out twice: in tools.py (the implementation) and
    in server.py (the docstring FastMCP actually publishes to the agent).
    server.py's is what a model reads; tools.py's is what a developer reads.
    A fix applied to one and not the other is silent.
    """
    in_tools = _advertised_in(tools.find_playbooks, facet)
    in_server = _advertised_in(server.find_playbooks, facet)
    assert in_tools == in_server, (
        f"{facet} vocabulary differs between tools.py and server.py: "
        f"only in tools={sorted(in_tools - in_server)}, "
        f"only in server={sorted(in_server - in_tools)}"
    )


# --- frontmatter integrity (F8) --------------------------------------------


def test_every_reference_declares_an_fcp_domain() -> None:
    """A reference with no domain has either broken or missing frontmatter.

    Either way it is unreachable via find_references(domain=...).
    """
    missing = [r.name for r in metadata.get_index() if not r.fcp_domain]
    assert not missing, (
        "references with no fcp_domain (broken or missing frontmatter): "
        f"{sorted(missing)}"
    )


def test_every_reference_declares_a_capability_and_maturity() -> None:
    incomplete = [
        r.name
        for r in metadata.get_index()
        if not r.fcp_capability or not r.fcp_maturity_entry
    ]
    assert not incomplete, f"references missing capability or maturity: {sorted(incomplete)}"


def test_every_reference_declares_at_least_one_phase_and_persona() -> None:
    incomplete = [
        r.name
        for r in metadata.get_index()
        if not r.fcp_phases or not r.fcp_personas_primary
    ]
    assert not incomplete, f"references missing phases or personas: {sorted(incomplete)}"


def test_every_playbook_declares_all_four_facets() -> None:
    incomplete = [
        pb.name
        for pb in metadata.get_playbook_index()
        if not (pb.scope and pb.service and pb.waste_category and pb.confidence)
    ]
    assert not incomplete, f"playbooks with an incomplete facet set: {sorted(incomplete)}"


def test_malformed_frontmatter_is_logged_not_swallowed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    broken = "---\nname: x\n  bad: [unclosed\n---\n\n# Body\n"
    with caplog.at_level(logging.WARNING, logger="cloud_finops_mcp.metadata"):
        fm, body = metadata._split_frontmatter(broken, source="broken.md")
    assert fm == {}
    assert "# Body" in body
    assert any("broken.md" in r.getMessage() for r in caplog.records), (
        "a malformed frontmatter block must warn - silently returning {} strips "
        "every facet and removes the file from faceted search"
    )


def test_non_mapping_frontmatter_is_logged(caplog: pytest.LogCaptureFixture) -> None:
    scalar_fm = "---\njust a string\n---\n\n# Body\n"
    with caplog.at_level(logging.WARNING, logger="cloud_finops_mcp.metadata"):
        fm, _ = metadata._split_frontmatter(scalar_fm, source="scalar.md")
    assert fm == {}
    assert caplog.records


# --- facet vocabulary conformance (F9) --------------------------------------


@pytest.mark.parametrize("facet", ["scope", "waste_category", "confidence"])
def test_no_facet_value_is_undocumented(facet: str) -> None:
    """Every value in the data must be advertised by the tool docstring.

    This is the check that would have caught `waste_category: egress` sitting
    outside the taxonomy: the playbook carried a value the docs never named.
    """
    in_data = set(tools.playbook_vocabulary()[facet])
    advertised = _advertised(facet)
    undocumented = in_data - advertised
    assert not undocumented, (
        f"{facet} values present in playbooks but not advertised in the "
        f"find_playbooks docstring: {sorted(undocumented)}"
    )


@pytest.mark.parametrize("facet", ["scope", "waste_category", "confidence"])
def test_no_advertised_facet_value_is_empty(facet: str) -> None:
    """Every advertised value should return something, or be a known gap.

    An advertised value with no content is a silent empty result for the agent.
    """
    in_data = set(tools.playbook_vocabulary()[facet])
    advertised = _advertised(facet)
    empty = advertised - in_data - KNOWN_EMPTY_FACET_VALUES
    assert not empty, (
        f"{facet} values advertised by find_playbooks but carried by no "
        f"playbook: {sorted(empty)}. Either write the playbooks or add them to "
        "KNOWN_EMPTY_FACET_VALUES and record the gap in the CLAUDE.md Roadmap."
    )


def test_known_empty_values_are_still_empty() -> None:
    """Ratchet: when a known gap is filled, this reminds you to close it out."""
    in_data = set(tools.playbook_vocabulary()["waste_category"])
    now_covered = KNOWN_EMPTY_FACET_VALUES & in_data
    assert not now_covered, (
        f"{sorted(now_covered)} now has playbook coverage. Remove it from "
        "KNOWN_EMPTY_FACET_VALUES and drop the matching CLAUDE.md Roadmap entry."
    )


def _words(text: str) -> list[str]:
    return [w for w in re.split(r"[^a-z0-9]+", text.lower()) if w]


def _names_heading(value: str, heading: str) -> bool:
    """True when a kebab facet value names the taxonomy heading it came from.

    The facet value is a shortened kebab form of the human-readable heading
    (``commitment-mismatch`` for "Commitment mismatches", ``egress`` for
    "Egress / data transfer"), so every word of the value must line up with the
    heading's leading words, the last one allowed to differ by an inflection.
    """
    v, h = _words(value), _words(heading)
    if not v or len(v) > len(h):
        return False
    if v[:-1] != h[: len(v) - 1]:
        return False
    return h[len(v) - 1].startswith(v[-1])


def test_waste_categories_match_the_taxonomy_file() -> None:
    """The eight categories are defined in the reference, not in the code.

    The advertised vocabulary and the taxonomy's own ``## Category N:``
    headings must pair up one-to-one. The previous version of this check only
    looked for the value's first word somewhere in the file, which let
    ``ai-ml-inefficiency`` pass on any text containing "ai" - and would have
    passed just as happily on a category the reference no longer defines.
    """
    ref = metadata.get_by_name("finops-waste-detection-playbooks")
    assert ref is not None
    text = ref.path.read_text(encoding="utf-8")
    assert "## The eight waste categories" in text, (
        "the waste taxonomy heading changed - the facet vocabulary in "
        "find_playbooks must be re-checked against it"
    )
    headings = CATEGORY_HEADING_RE.findall(text)
    assert len(headings) == 8, (
        "expected eight '## Category N: ...' headings in "
        f"finops-waste-detection-playbooks.md, found {len(headings)}: {headings}"
    )

    claimed: dict[str, str] = {}
    for value in sorted(_advertised("waste_category")):
        hits = [h for h in headings if _names_heading(value, h)]
        assert len(hits) == 1, (
            f"advertised waste_category {value!r} matches {len(hits)} of the "
            f"eight taxonomy categories {headings} - it should name exactly one"
        )
        already = claimed.get(hits[0])
        assert already is None, (
            f"waste_category {value!r} and {already!r} both name the taxonomy "
            f"category {hits[0]!r}"
        )
        claimed[hits[0]] = value

    unclaimed = [h for h in headings if h not in claimed]
    assert not unclaimed, (
        f"taxonomy categories with no advertised waste_category: {unclaimed}. "
        "Either add the facet value to the find_playbooks docstrings or drop "
        "the category from the reference."
    )


def test_facet_values_are_lowercase_and_consistent() -> None:
    """Facets are matched case-insensitively but stored values should be uniform."""
    vocab = tools.playbook_vocabulary()
    for facet in ("scope", "waste_category", "confidence"):
        odd = [v for v in vocab[facet] if v != v.lower()]
        assert not odd, f"{facet} values are not lowercase: {odd}"


# --- directory conformance: tool annotations (F10) ---------------------------


async def test_every_tool_declares_title_and_read_only_annotations() -> None:
    """Every tool must carry a title and explicit read-only annotations.

    Connector directories (Anthropic's included) treat a missing title or
    readOnlyHint/destructiveHint as a rejection criterion, not a default.
    Everything this server does is a read-only lookup over a bundled set,
    so the hints are uniform.
    """
    tools_list = await server.mcp.list_tools()
    assert tools_list, "server exposes no tools"
    for tool in tools_list:
        assert tool.title, f"{tool.name} declares no title"
        ann = tool.annotations
        assert ann is not None, f"{tool.name} declares no annotations"
        assert ann.readOnlyHint is True, f"{tool.name} is not marked read-only"
        assert ann.destructiveHint is False, f"{tool.name} lacks destructiveHint=False"


async def test_every_tool_description_says_when_to_use_it() -> None:
    """A description that only says WHAT a tool does reads as interchangeable.

    The directory review expects each description to steer the model on WHEN
    to pick this tool over its siblings; 'Use this' is the convention all six
    docstrings follow.
    """
    tools_list = await server.mcp.list_tools()
    for tool in tools_list:
        assert tool.description and "Use this" in tool.description, (
            f"{tool.name} description does not say when to use it"
        )
