"""Unit tests for the tool implementations."""

from __future__ import annotations

import json

from cloud_finops_mcp import metadata, tools


def setup_function() -> None:
    metadata.reset_cache()


# --- list_references --------------------------------------------------------


LISTING_KEYS = {
    "name",
    "title",
    "description",
    "fcp_domain",
    "fcp_capability",
    "fcp_phases",
    "fcp_personas_primary",
    "fcp_maturity_entry",
    "approx_tokens",
}


def test_list_returns_all_references(expected_references: int) -> None:
    result = tools.list_references()
    assert result["total"] == expected_references
    assert len(result["references"]) == expected_references
    sample = result["references"][0]
    assert {"name", "description", "fcp_domain", "fcp_phases"}.issubset(sample)


def test_listing_entry_carries_exactly_the_discriminating_facets() -> None:
    """The listing shape is a token budget, so it is pinned exactly.

    Every key here is something a caller chooses a reference ON. Anything
    added back costs ~35x its own size on a call every session makes, so a
    new field has to argue for itself against this assertion.
    """
    for entry in tools.list_references()["references"]:
        assert set(entry) == LISTING_KEYS, f"{entry['name']} has an unexpected shape"


def test_listing_omits_the_non_discriminating_facets() -> None:
    """Collaborating personas and secondary capabilities are not in the payload.

    Both are descriptive rather than discriminating (a broad persona
    collaborates on nearly every file) and together they were ~17% of the
    discovery payload.
    """
    entry = tools.list_references()["references"][0]
    assert "fcp_personas_collaborating" not in entry
    assert "fcp_capabilities_secondary" not in entry


def test_dropped_facets_are_still_filterable() -> None:
    """Trimming the listing must not trim the index behind it.

    finops-aws carries Finance only as a collaborating persona and Usage
    Optimization only as a secondary capability. Neither is printed any more;
    both must still select the file.
    """
    by_collaborating = {
        r["name"] for r in tools.find_references(persona="Finance")["references"]
    }
    assert "finops-aws" in by_collaborating
    by_secondary = {
        r["name"] for r in tools.find_references(capability="Usage Optimization")["references"]
    }
    assert "finops-aws" in by_secondary


def test_listing_descriptions_are_summarised() -> None:
    """Descriptions were 46% of the payload; the listing carries one sentence."""
    entries = tools.list_references()["references"]
    for entry in entries:
        assert len(entry["description"]) <= metadata.SUMMARY_LIMIT + 3  # "..."
    full = {r.name: r.description for r in metadata.get_index()}
    assert any(len(full[e["name"]]) > len(e["description"]) for e in entries), (
        "no description was actually shortened - the summariser is inert"
    )


def test_size_hint_is_present_and_plausible() -> None:
    """approx_tokens must track the real body size, not be a constant."""
    entries = {e["name"]: e["approx_tokens"] for e in tools.list_references()["references"]}
    biggest = max(entries, key=entries.get)
    assert entries[biggest] > 15_000, "the largest reference should look large"
    assert min(entries.values()) < entries[biggest] / 3, "the hint does not discriminate"
    for ref in metadata.get_index():
        assert entries[ref.name] == round(len(ref.path.read_text(encoding="utf-8")) / 4)


def test_slimming_beats_the_size_hint_it_pays_for() -> None:
    """Task 3 must not undo task 2: the listing has to be materially smaller.

    Measured against the pre-change payload (28,180 chars / ~7,045 tokens on
    the 2026-08-27 bundle). The ceiling is set well above the measured 16.3K
    so content growth does not fail the build, but a regression that put the
    dropped facets or the full descriptions back would blow straight through
    it.
    """
    payload = json.dumps(tools.list_references())
    assert len(payload) < 20_000, (
        f"list_references payload is {len(payload)} chars - the slimming has "
        "regressed or a costly field was added back"
    )


# --- get_reference ----------------------------------------------------------


def test_get_reference_returns_full_content() -> None:
    result = tools.get_reference("finops-aws")
    assert result["name"] == "finops-aws"
    assert "fcp_domain" in result["content"]  # frontmatter included for provenance
    assert "# FinOps on AWS" in result["content"]


# --- get_reference(section=...) ---------------------------------------------
#
# The catalogue files are the reason this exists: finops-aws-patterns is
# ~26,600 tokens of enumerated patterns behind a single H2 and seven H3s.

CATALOGUE = "finops-aws-patterns"


def test_omitted_section_is_byte_identical_to_the_file() -> None:
    """The compatibility guarantee: no section, no change. Ever.

    ``content`` must be the file verbatim, frontmatter included, and the
    payload must carry no extra keys - a heading list bolted onto the
    full-body response would be pure duplication of content the caller has
    just paid for.
    """
    ref = metadata.get_by_name(CATALOGUE)
    assert ref is not None
    on_disk = ref.path.read_text(encoding="utf-8")

    result = tools.get_reference(CATALOGUE)
    assert result == {"name": CATALOGUE, "content": on_disk, "lines": ref.lines}


def test_blank_section_takes_the_full_body_path() -> None:
    """An empty string is a model filling in a field, not a failed query."""
    full = tools.get_reference(CATALOGUE)
    for blank in ("", "   ", None):
        assert tools.get_reference(CATALOGUE, section=blank) == full


def test_section_returns_only_that_section() -> None:
    result = tools.get_reference(CATALOGUE, section="Storage Optimization Patterns")
    assert result["partial"] is True
    assert result["section"] == "Storage Optimization Patterns (28)"
    assert result["section_level"] == 3
    assert "### Storage Optimization Patterns (28)" in result["content"]
    # The neighbouring sections must not come along.
    assert "### Compute Optimization Patterns" not in result["content"]
    assert "### Networking Optimization Patterns" not in result["content"]
    assert result["lines"] < result["full_lines"]


def test_section_chunk_is_self_describing() -> None:
    """The chunk carries the reference's H1 so it stands on its own."""
    ref = metadata.get_by_name(CATALOGUE)
    assert ref is not None
    result = tools.get_reference(CATALOGUE, section="networking")
    assert result["content"].startswith(f"# {ref.title}\n")
    assert result["title"] == ref.title
    assert "not the full reference" in result["note"]


def test_section_is_materially_cheaper_than_the_whole_file() -> None:
    """The point of the feature, asserted as a number."""
    whole = len(json.dumps(tools.get_reference(CATALOGUE)))
    part = len(json.dumps(tools.get_reference(CATALOGUE, section="networking")))
    assert part < whole / 5, f"section fetch is {part} of {whole} chars"


def test_section_match_is_case_insensitive_and_partial() -> None:
    """A model writes a phrase from the user's question, not a copied heading."""
    canonical = tools.get_reference(CATALOGUE, section="Storage Optimization Patterns (28)")
    for phrase in (
        "storage",
        "STORAGE OPTIMIZATION",
        "storage optimization patterns",  # the count is not known to the caller
        "  Storage  ",
    ):
        result = tools.get_reference(CATALOGUE, section=phrase)
        assert result.get("section") == canonical["section"], phrase
        assert result["content"] == canonical["content"], phrase


def test_section_match_tolerates_word_order() -> None:
    """Tier 4: every word of the query appears in the heading, order-free."""
    result = tools.get_reference(CATALOGUE, section="patterns networking")
    assert result["section"] == "Networking Optimization Patterns (14)"


def test_h2_sections_are_selectable_too() -> None:
    """H3 is essential for the catalogues, but H2 must work on normal files."""
    result = tools.get_reference("finops-aws", section="Cost allocation")
    assert result["partial"] is True
    assert result["section_level"] in (2, 3)


def test_section_miss_lists_the_available_headings() -> None:
    """Loud failure: not the whole file, not an empty result - the vocabulary.

    Silently returning the body would hand back exactly the 26K tokens the
    caller asked to avoid, which is the silent-degradation failure this repo
    keeps re-learning.
    """
    result = tools.get_reference(CATALOGUE, section="kubernetes cost allocation")
    assert "content" not in result
    assert "error" in result
    assert CATALOGUE in result["error"]
    headings = result["available_sections"]
    assert "### Storage Optimization Patterns (28)" in headings
    assert "## AWS Optimization Patterns" in headings
    # Every entry carries its level marker, so the listing is navigable.
    assert all(h.startswith("## ") or h.startswith("### ") for h in headings)


def test_section_miss_is_far_cheaper_than_the_body_it_refuses() -> None:
    miss = len(json.dumps(tools.get_reference(CATALOGUE, section="nope")))
    whole = len(json.dumps(tools.get_reference(CATALOGUE)))
    assert miss < whole / 50, f"the error costs {miss} chars"


def test_section_miss_offers_near_misses() -> None:
    """A typo should come back with the heading it nearly named."""
    result = tools.get_reference(CATALOGUE, section="Storag Optimizaton Paterns")
    assert "error" in result
    assert result["suggestions"][0] == "Storage Optimization Patterns (28)"


def test_ambiguous_section_reports_the_runners_up() -> None:
    """Several headings can match one phrase; the caller is told, not guessed at."""
    result = tools.get_reference(CATALOGUE, section="optimization patterns")
    assert result["partial"] is True
    others = result.get("other_matching_sections", [])
    assert others, "an ambiguous phrase should surface the alternatives"
    assert all(o.startswith("#") for o in others)


def test_section_on_unknown_reference_still_reports_the_name() -> None:
    """The name miss is checked first - a section query cannot mask it."""
    result = tools.get_reference("finops-aw", section="storage")
    assert "finops-aws" in result["suggestions"]


def test_get_reference_unknown_returns_suggestions() -> None:
    result = tools.get_reference("finops-aw")  # typo
    assert "error" in result
    assert "finops-aws" in result["suggestions"]


def test_get_reference_empty_name_rejects() -> None:
    result = tools.get_reference("")
    assert "error" in result
    assert result["suggestions"] == []


# --- find_references --------------------------------------------------------


def test_find_no_filters_returns_everything(expected_references: int) -> None:
    result = tools.find_references()
    assert result["total"] == expected_references
    assert result["filters"] == {}


def test_find_by_phase() -> None:
    result = tools.find_references(phase="Optimize")
    names = {r["name"] for r in result["references"]}
    # finops-aws has Optimize phase; spot-check it's included.
    assert "finops-aws" in names
    assert result["total"] >= 1
    # Every returned ref must have Optimize in its phases.
    for ref in result["references"]:
        assert "Optimize" in ref["fcp_phases"]


def test_find_case_insensitive() -> None:
    a = tools.find_references(phase="optimize")
    b = tools.find_references(phase="Optimize")
    assert a["total"] == b["total"]


def test_find_capability_matches_secondary() -> None:
    """Capability filter must match both primary and secondary fields."""
    result = tools.find_references(capability="Usage Optimization")
    names = {r["name"] for r in result["references"]}
    # finops-aws lists Usage Optimization as a *secondary* capability
    # (its primary is Rate Optimization); it should still match.
    assert "finops-aws" in names


def test_find_persona_matches_collaborating() -> None:
    """Persona filter must check both primary and collaborating lists."""
    result = tools.find_references(persona="Finance")
    names = {r["name"] for r in result["references"]}
    # finops-aws has Finance only in fcp_personas_collaborating.
    assert "finops-aws" in names


def test_find_and_semantics_intersect_filters() -> None:
    optimize_refs = {r["name"] for r in tools.find_references(phase="Optimize")["references"]}
    eng_refs = {r["name"] for r in tools.find_references(persona="Engineering")["references"]}
    both = {r["name"] for r in tools.find_references(phase="Optimize", persona="Engineering")["references"]}
    assert both == optimize_refs & eng_refs


def test_find_no_match_returns_empty() -> None:
    result = tools.find_references(domain="No Such Domain")
    assert result["total"] == 0
    assert result["references"] == []


def test_find_filters_echo_input() -> None:
    result = tools.find_references(phase="Optimize", persona="Engineering")
    assert result["filters"] == {"phase": "Optimize", "persona": "Engineering"}


# --- list_playbooks ---------------------------------------------------------


def test_list_playbooks_returns_all(expected_playbooks: int) -> None:
    result = tools.list_playbooks()
    assert result["total"] == expected_playbooks
    assert len(result["playbooks"]) == expected_playbooks
    sample = result["playbooks"][0]
    assert {
        "name",
        "title",
        "scope",
        "waste_category",
        "confidence",
        "approx_tokens",
    }.issubset(sample)


def test_playbook_listing_carries_the_same_size_hint() -> None:
    """One size unit across both listings, so a mixed fetch can be budgeted."""
    for entry in tools.list_playbooks()["playbooks"]:
        assert isinstance(entry["approx_tokens"], int)
        assert entry["approx_tokens"] > 0


# --- get_playbook -----------------------------------------------------------


def test_get_playbook_returns_full_content() -> None:
    result = tools.get_playbook("aws-zombie-nat-gateway")
    assert result["name"] == "aws-zombie-nat-gateway"
    assert "NAT Gateway" in result["title"]
    assert "## Detection" in result["content"]


def test_get_playbook_unknown_returns_suggestions() -> None:
    result = tools.get_playbook("aws-zombie-nat")  # truncated
    assert "error" in result
    assert "aws-zombie-nat-gateway" in result["suggestions"]


def test_get_playbook_empty_name_rejects() -> None:
    result = tools.get_playbook("")
    assert "error" in result
    assert result["suggestions"] == []


# --- find_playbooks ---------------------------------------------------------


def test_find_playbooks_no_filters_returns_everything(expected_playbooks: int) -> None:
    result = tools.find_playbooks()
    assert result["total"] == expected_playbooks
    assert result["filters"] == {}


def test_find_playbooks_by_scope() -> None:
    result = tools.find_playbooks(scope="aws")
    names = {p["name"] for p in result["playbooks"]}
    assert "aws-zombie-nat-gateway" in names
    for pb in result["playbooks"]:
        assert pb["scope"] == "aws"


def test_find_playbooks_case_insensitive() -> None:
    a = tools.find_playbooks(scope="AWS")
    b = tools.find_playbooks(scope="aws")
    assert a["total"] == b["total"]


def test_find_playbooks_by_waste_category() -> None:
    result = tools.find_playbooks(waste_category="idle")
    assert result["total"] >= 1
    for pb in result["playbooks"]:
        assert pb["waste_category"] == "idle"


def test_find_playbooks_by_confidence() -> None:
    result = tools.find_playbooks(confidence="obvious")
    assert result["total"] >= 1
    for pb in result["playbooks"]:
        assert pb["confidence"] == "obvious"


def test_find_playbooks_and_semantics_intersect() -> None:
    aws_pbs = {p["name"] for p in tools.find_playbooks(scope="aws")["playbooks"]}
    idle_pbs = {p["name"] for p in tools.find_playbooks(waste_category="idle")["playbooks"]}
    both = {p["name"] for p in tools.find_playbooks(scope="aws", waste_category="idle")["playbooks"]}
    assert both == aws_pbs & idle_pbs


def test_find_playbooks_no_match_returns_empty() -> None:
    result = tools.find_playbooks(scope="not-a-scope")
    assert result["total"] == 0
    assert result["playbooks"] == []


def test_find_playbooks_filters_echo_input() -> None:
    result = tools.find_playbooks(scope="aws", waste_category="idle")
    assert result["filters"] == {"scope": "aws", "waste_category": "idle"}


# --- empty faceted results explain themselves (F21) -------------------------


def test_find_references_typo_returns_valid_values() -> None:
    """A bare {"total": 0} cannot be told apart from a genuine coverage gap."""
    result = tools.find_references(domain="Optimise Usage & Cost")  # British misspelling
    assert result["total"] == 0
    assert "hint" in result
    assert "domain" in result["valid_values"]
    assert "Optimize Usage & Cost" in result["valid_values"]["domain"]
    assert "not present" in result["hint"]


def test_find_playbooks_typo_returns_valid_values() -> None:
    result = tools.find_playbooks(waste_category="orphan")  # actual value is "orphaned"
    assert result["total"] == 0
    assert "orphaned" in result["valid_values"]["waste_category"]


def test_valid_but_non_overlapping_filters_say_so() -> None:
    """Each value exists; the combination does not. That is a different message."""
    result = tools.find_playbooks(scope="azure", service="AWS NAT Gateway")
    assert result["total"] == 0
    assert "no single item carries all of them" in result["hint"]


def test_empty_result_help_is_absent_when_there_are_matches() -> None:
    result = tools.find_playbooks(scope="aws")
    assert result["total"] > 0
    assert "hint" not in result
    assert "valid_values" not in result


def test_no_filters_returns_everything_without_help(expected_references: int) -> None:
    result = tools.find_references()
    assert result["total"] == expected_references
    assert "hint" not in result


def test_vocabulary_helpers_are_derived_from_data() -> None:
    vocab = tools.playbook_vocabulary()
    assert "egress" in vocab["waste_category"]
    assert set(vocab["scope"]) <= {"aws", "azure", "gcp", "cross-cloud"}
    ref_vocab = tools.reference_vocabulary()
    assert set(ref_vocab["maturity"]) <= {"Crawl", "Walk", "Run"}
    assert set(ref_vocab["phase"]) <= {"Inform", "Optimize", "Operate"}


# --- persona_primary_only (2026-08-20, from the connector field test) --------


def test_persona_primary_only_narrows_the_set() -> None:
    """Broad personas collaborate everywhere; the flag is the operational cut.

    The 2026-08-19 field test measured persona="Engineering" excluding exactly
    one reference over the whole library - the collaborating list makes the
    default filter descriptive rather than discriminating.
    """
    default = tools.find_references(persona="Engineering")
    primary = tools.find_references(persona="Engineering", persona_primary_only=True)
    assert 0 < primary["total"] < default["total"]
    names_default = {r["name"] for r in default["references"]}
    names_primary = {r["name"] for r in primary["references"]}
    assert names_primary < names_default
    # finops-itam lists Engineering only as collaborating: kept by the
    # default match, cut by the primary-only one.
    assert "finops-itam" in names_default
    assert "finops-itam" not in names_primary
    # The applied flag is echoed in the filters so the caller can see that
    # a narrowing actually happened.
    assert primary["filters"].get("persona_primary_only") is True
    assert "persona_primary_only" not in default["filters"]


def test_zero_result_faceted_query_is_logged(caplog) -> None:
    """A zero-result query is the purest coverage-gap signal; it must leave
    a grep-able trace in the server logs."""
    import logging

    with caplog.at_level(logging.INFO, logger="cloud_finops_mcp.tools"):
        tools.find_playbooks(scope="aws", waste_category="nonexistent")
        tools.find_references(persona="Nonexistent Persona")
    zero_logs = [r.message for r in caplog.records if "zero-result query" in r.message]
    assert len(zero_logs) == 2
    assert any("find_playbooks" in m for m in zero_logs)
    assert any("find_references" in m for m in zero_logs)
