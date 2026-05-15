"""Unit tests for the FCP frontmatter index."""

from __future__ import annotations

from cloud_finops_mcp import metadata


def setup_function() -> None:
    metadata.reset_cache()


def test_index_returns_28_references() -> None:
    refs = metadata.get_index()
    assert len(refs) == 28


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


def test_lookup_unknown_returns_none() -> None:
    assert metadata.get_by_name("nope-not-here") is None


# --- playbook index ---------------------------------------------------------


def test_playbook_index_returns_23() -> None:
    playbooks = metadata.get_playbook_index()
    assert len(playbooks) == 23


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
