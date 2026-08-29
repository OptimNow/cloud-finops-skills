"""Unit tests for the FCP frontmatter index."""

from __future__ import annotations

from cloud_finops_mcp import metadata


def setup_function() -> None:
    metadata.reset_cache()


def test_index_returns_all_references(expected_references: int) -> None:
    refs = metadata.get_index()
    assert len(refs) == expected_references


def test_index_is_sorted_by_name() -> None:
    refs = metadata.get_index()
    names = [r.name for r in refs]
    assert names == sorted(names)


def test_known_reference_has_expected_fcp_fields() -> None:
    """finops-aws is a stable anchor — its FCP frontmatter is locked in main."""
    aws = metadata.get_by_name("finops-aws")
    assert aws is not None
    assert aws.fcp_domain == "Optimize Usage & Cost"
    assert aws.fcp_capability == "Rate Optimization"
    assert "Engineering" in aws.fcp_personas_primary
    assert "Optimize" in aws.fcp_phases
    assert aws.fcp_maturity_entry == "Walk"


def test_description_is_non_empty_for_every_reference() -> None:
    for ref in metadata.get_index():
        assert ref.description, f"{ref.name} has no description"


def test_extract_description_joins_multiline_blockquote() -> None:
    """A blockquote wrapped across lines is one description, not its first line."""
    body = (
        "# Some Reference\n"
        "\n"
        "> First half of the sentence that\n"
        "> continues on the next line.\n"
        "\n"
        "Prose that must not leak into the description.\n"
    )
    desc = metadata._extract_description({}, body)
    assert desc == "First half of the sentence that continues on the next line."


def test_extract_description_stops_at_blockquote_paragraph_break() -> None:
    """An empty '>' line separates paragraphs; only the first one is the description."""
    body = "# T\n\n> The description.\n>\n> A second paragraph.\n"
    assert metadata._extract_description({}, body) == "The description."


# --- frontmatter delimiters --------------------------------------------------


def test_leading_horizontal_rule_is_not_frontmatter() -> None:
    """A file opening with a markdown rule has no frontmatter, and keeps its body.

    Substring matching read the rule as an opening fence and everything up to
    the next ``---`` in the document as YAML, so the body silently started
    partway down the file.
    """
    text = (
        "---\n"
        "\n"
        "# Title\n"
        "\n"
        "Opening prose that must survive.\n"
        "\n"
        "---\n"
        "\n"
        "## A section\n"
    )
    fm, body = metadata._split_frontmatter(text, source="rule.md")
    assert fm == {}
    assert body == text
    assert "Opening prose that must survive." in body


def test_value_containing_a_triple_dash_does_not_truncate_the_block() -> None:
    """``---`` inside a value is not a closing fence.

    Splitting on the substring ended the block mid-value, so every facet
    declared after that line vanished and the file dropped out of find_*.
    """
    text = "---\ndesc: a---b\nname: kept\nfcp_domain: Optimize Usage & Cost\n---\n\n# Body\n"
    fm, body = metadata._split_frontmatter(text, source="dashes.md")
    assert fm == {
        "desc": "a---b",
        "name": "kept",
        "fcp_domain": "Optimize Usage & Cost",
    }
    assert body == "# Body\n"


# --- titles ------------------------------------------------------------------


def test_extract_title_keeps_a_leading_hash_in_the_heading_text() -> None:
    """Only the '# ' marker is stripped, not every leading '#' and space.

    ``lstrip("# ")`` ate the first word of a heading like ``# #1 Top Pattern``.
    """
    assert metadata._extract_title("# #1 Top Pattern\n", fallback="x") == "#1 Top Pattern"


def test_extract_title_falls_back_when_there_is_no_heading() -> None:
    assert metadata._extract_title("no heading here\n", fallback="slug") == "slug"


# --- description summarising -------------------------------------------------


def test_summarise_leaves_a_short_description_alone() -> None:
    assert metadata.summarise("Short enough.") == "Short enough."


def test_summarise_prefers_a_sentence_boundary_over_a_hard_cut() -> None:
    text = "The first sentence carries the point. " + "Filler. " * 40
    assert metadata.summarise(text) == "The first sentence carries the point."


def test_summarise_hard_caps_a_runaway_first_sentence() -> None:
    text = "word " * 200
    out = metadata.summarise(text)
    assert out.endswith("...")
    assert len(out) <= metadata.SUMMARY_LIMIT + 3
    assert not out[:-3].endswith(" "), "the cut must land on a word boundary"


def test_summarise_collapses_wrapped_whitespace() -> None:
    assert metadata.summarise("one\n  two\tthree") == "one two three"


# --- section splitting -------------------------------------------------------

SECTIONED = (
    "# Title\n"
    "\n"
    "Intro prose.\n"
    "\n"
    "## First chapter\n"
    "\n"
    "Chapter prose.\n"
    "\n"
    "### Nested one\n"
    "\n"
    "Nested prose.\n"
    "\n"
    "### Nested two\n"
    "\n"
    "More nested prose.\n"
    "\n"
    "## Second chapter\n"
    "\n"
    "Last prose.\n"
)


def test_split_sections_finds_h2_and_h3() -> None:
    headings = [(s.level, s.heading) for s in metadata.split_sections(SECTIONED)]
    assert headings == [
        (2, "First chapter"),
        (3, "Nested one"),
        (3, "Nested two"),
        (2, "Second chapter"),
    ]


def test_an_h2_span_contains_its_h3_children() -> None:
    first = metadata.split_sections(SECTIONED)[0]
    text = metadata.section_text(SECTIONED, first)
    assert "### Nested one" in text and "### Nested two" in text
    assert "## Second chapter" not in text


def test_an_h3_span_stops_at_its_sibling() -> None:
    nested = metadata.split_sections(SECTIONED)[1]
    text = metadata.section_text(SECTIONED, nested)
    assert "Nested prose." in text
    assert "Nested two" not in text


def test_headings_inside_a_code_fence_are_not_sections() -> None:
    """Shell comments split a section in half if fences are ignored.

    ``## Cost report`` inside a bash block is a comment, not a boundary.
    """
    body = (
        "## Real heading\n"
        "\n"
        "```bash\n"
        "## Not a heading\n"
        "### Also not a heading\n"
        "```\n"
        "\n"
        "Trailing prose.\n"
    )
    sections = metadata.split_sections(body)
    assert [s.heading for s in sections] == ["Real heading"]
    assert "Trailing prose." in metadata.section_text(body, sections[0])


def test_tilde_fences_are_handled_too() -> None:
    body = "## Real\n\n~~~\n## Fake\n~~~\n"
    assert [s.heading for s in metadata.split_sections(body)] == ["Real"]


def test_find_sections_prefers_an_exact_heading_over_a_substring() -> None:
    body = "## Storage\n\na\n\n## Storage lifecycle deep dive\n\nb\n"
    assert metadata.find_sections(body, "storage")[0].heading == "Storage"


def test_find_sections_ignores_a_trailing_count() -> None:
    body = "### Compute Optimization Patterns (42)\n\na\n"
    hits = metadata.find_sections(body, "compute optimization patterns")
    assert len(hits) == 1


def test_find_sections_prefers_the_shallower_heading_on_a_tie() -> None:
    body = "## Egress\n\na\n\n### Egress\n\nb\n"
    assert metadata.find_sections(body, "egress")[0].level == 2


def test_find_sections_returns_nothing_for_an_empty_query() -> None:
    assert metadata.find_sections(SECTIONED, "   ") == []


def test_section_labels_carry_the_level_marker() -> None:
    assert metadata.section_labels(SECTIONED)[:2] == ["## First chapter", "### Nested one"]


def test_strip_frontmatter_removes_the_yaml_block() -> None:
    text = "---\nname: x\n---\n\n# Body\n\n## A section\n"
    body = metadata.strip_frontmatter(text, source="x.md")
    assert body.startswith("# Body")
    assert [s.heading for s in metadata.split_sections(body)] == ["A section"]


def test_approx_tokens_is_the_repo_wide_chars_over_four_estimate() -> None:
    assert metadata.approx_tokens(4000) == 1000
    assert metadata.approx_tokens(0) == 0


# --- content version stamp ---------------------------------------------------


def test_content_version_summary_reads_stamp(monkeypatch, tmp_path) -> None:
    stamp = tmp_path / "content_version.txt"
    stamp.write_text(
        "version: 1.32.0\nsynced_at: 2026-08-19T10:00:00Z\nreferences: 33\nplaybooks: 25\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(metadata, "CONTENT_VERSION_FILE", stamp)
    assert (
        metadata.content_version_summary()
        == "content version 1.32.0, synced 2026-08-19T10:00:00Z"
    )


def test_content_version_summary_none_when_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(metadata, "CONTENT_VERSION_FILE", tmp_path / "absent.txt")
    assert metadata.content_version_summary() is None


def test_lookup_unknown_returns_none() -> None:
    assert metadata.get_by_name("nope-not-here") is None


# --- playbook index ---------------------------------------------------------


def test_playbook_index_returns_all(expected_playbooks: int) -> None:
    playbooks = metadata.get_playbook_index()
    assert len(playbooks) == expected_playbooks


def test_playbook_index_excludes_readme() -> None:
    names = {p.name for p in metadata.get_playbook_index()}
    assert "README" not in names
    assert "readme" not in names


def test_playbook_index_is_sorted_by_name() -> None:
    names = [p.name for p in metadata.get_playbook_index()]
    assert names == sorted(names)


def test_known_playbook_has_expected_fields() -> None:
    """aws-zombie-nat-gateway is a stable anchor."""
    pb = metadata.get_playbook_by_name("aws-zombie-nat-gateway")
    assert pb is not None
    assert pb.scope == "aws"
    assert pb.waste_category == "idle"
    assert pb.confidence == "obvious"
    assert "NAT Gateway" in pb.title


def test_every_playbook_has_a_title() -> None:
    for pb in metadata.get_playbook_index():
        assert pb.title, f"{pb.name} has no title"


def test_lookup_unknown_playbook_returns_none() -> None:
    assert metadata.get_playbook_by_name("nope-not-here") is None
