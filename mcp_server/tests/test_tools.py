"""Unit tests for the tool implementations."""

from __future__ import annotations

from cloud_finops_mcp import metadata, tools


def setup_function() -> None:
    metadata.reset_cache()


# --- list_references --------------------------------------------------------


def test_list_returns_28() -> None:
    result = tools.list_references()
    assert result["total"] == 28
    assert len(result["references"]) == 28
    sample = result["references"][0]
    assert {"name", "description", "fcp_domain", "fcp_phases", "lines"}.issubset(sample)


# --- get_reference ----------------------------------------------------------


def test_get_reference_returns_full_content() -> None:
    result = tools.get_reference("finops-aws")
    assert result["name"] == "finops-aws"
    assert "fcp_domain" in result["content"]  # frontmatter included for provenance
    assert "# FinOps on AWS" in result["content"]


def test_get_reference_unknown_returns_suggestions() -> None:
    result = tools.get_reference("finops-aw")  # typo
    assert "error" in result
    assert "finops-aws" in result["suggestions"]


def test_get_reference_empty_name_rejects() -> None:
    result = tools.get_reference("")
    assert "error" in result
    assert result["suggestions"] == []


# --- find_references --------------------------------------------------------


def test_find_no_filters_returns_everything() -> None:
    result = tools.find_references()
    assert result["total"] == 28
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


def test_list_playbooks_returns_23() -> None:
    result = tools.list_playbooks()
    assert result["total"] == 23
    assert len(result["playbooks"]) == 23
    sample = result["playbooks"][0]
    assert {"name", "title", "scope", "waste_category", "confidence", "lines"}.issubset(sample)


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


def test_find_playbooks_no_filters_returns_everything() -> None:
    result = tools.find_playbooks()
    assert result["total"] == 23
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
