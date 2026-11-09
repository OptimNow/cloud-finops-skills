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
    """finops-aws is a stable anchor: its FCP frontmatter is locked in main.

    Its primary capability became Usage Optimization on 2026-10-22, when the
    billing sections moved to finops-aws-billing (commitments had moved to
    finops-aws-commitments in August 2026).
    """
    aws = metadata.get_by_name("finops-aws")
    assert aws is not None
    assert aws.fcp_domain == "Optimize Usage & Cost"
    assert aws.fcp_capability == "Usage Optimization"
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


# --- questions (phase 2 of the question index) -----------------------------


def test_questions_parse_plain_strings() -> None:
    pb = metadata.get_playbook_by_name("aws-zombie-nat-gateway")
    assert pb is not None
    texts = [q.text for q in pb.questions]
    assert "Is it safe to delete a NAT gateway nobody seems to use?" in texts
    assert all(q.persona is None and q.section is None for q in pb.questions)


def test_questions_parse_mapping_entries_with_section() -> None:
    itam = metadata.get_by_name("finops-itam")
    assert itam is not None
    first = next(q for q in itam.questions if q.text.startswith("We hold SQL Server licences"))
    assert first.section == "BYOL strategy"
    assert first.persona is None


def test_questions_parse_persona() -> None:
    pb = metadata.get_playbook_by_name("aws-expiring-commitment-no-decision")
    assert pb is not None
    assert {q.persona for q in pb.questions if q.persona} == {"FinOps lead"}


def test_questions_absent_parses_to_an_empty_list() -> None:
    assert metadata._parse_questions(None, "synthetic.md") == []


def test_every_file_declares_four_to_eight_questions() -> None:
    """Phase 3 (2026-11-09) put the field on every reference and playbook; CI gates
    it with scripts/check-questions.py, this pins it from the server's side."""
    for item in [*metadata.get_index(), *metadata.get_playbook_index()]:
        assert 4 <= len(item.questions) <= 8, (item.name, len(item.questions))


def test_parse_questions_tolerates_malformed_entries() -> None:
    parsed = metadata._parse_questions(
        [
            "A plain question?",
            {"q": " Mapped? ", "section": "Fix", "persona": ""},
            {"no_q": 1},
            42,
            "",
        ],
        source="test.md",
    )
    assert [q.text for q in parsed] == ["A plain question?", "Mapped?"]
    assert parsed[1].section == "Fix"
    assert parsed[1].persona is None
    assert metadata._parse_questions("one", source="t") == [metadata.Question(text="one")]
    assert metadata._parse_questions(None, source="t") == []
    assert metadata._parse_questions({"q": "not a list"}, source="t") == []


def test_headings_are_indexed_for_query_ranking() -> None:
    ref = metadata.get_by_name("finops-aws-commitments")
    assert ref is not None
    assert "Phased purchasing" in ref.headings
    pb = metadata.get_playbook_by_name("aws-zombie-nat-gateway")
    assert pb is not None
    assert "Detection" in pb.headings


def test_executive_persona_is_declared_across_the_index() -> None:
    """CTO / CIO / CFO questions exist on the files written for that reader."""
    files = {
        r.name for r in metadata.get_index() if any(q.persona == "Executive" for q in r.questions)
    }
    assert {"finops-kpis-benchmarking", "finops-ai-value-management", "optimnow-methodology"} <= files
    assert len(files) >= 8


def test_every_bundled_question_entry_is_parsed() -> None:
    """A malformed entry is skipped with a warning at load time; the bundle may hold none."""
    import yaml

    def declared(path) -> int:
        raw = path.read_text(encoding="utf-8")
        fm = yaml.safe_load(raw.split("\n---\n", 1)[0][4:]) or {}
        value = fm.get("questions")
        return len(value) if isinstance(value, list) else (1 if value else 0)

    for ref in metadata.get_index():
        assert len(ref.questions) == declared(metadata.DATA_DIR / f"{ref.name}.md"), ref.name
    for pb in metadata.get_playbook_index():
        assert len(pb.questions) == declared(metadata.PLAYBOOKS_DIR / f"{pb.name}.md"), pb.name

