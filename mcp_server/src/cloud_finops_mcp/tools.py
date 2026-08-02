"""Tool implementations exposed by the MCP server.

Each tool returns a JSON-serialisable ``dict``. The server module wraps these
as MCP tools using the ``mcp`` SDK.

The reference tools (``list_references`` / ``get_reference`` / ``find_references``)
serve the long-form provider and discipline files. The playbook tools
(``list_playbooks`` / ``get_playbook`` / ``find_playbooks``) serve the
named-pattern runbooks - small, retrieval-friendly chunks scoped to one waste
pattern each.
"""

from __future__ import annotations

import difflib
from typing import Any

from .metadata import (
    Playbook,
    Reference,
    get_by_name,
    get_index,
    get_playbook_by_name,
    get_playbook_index,
)


def list_references() -> dict[str, Any]:
    """Return all bundled references with their FCP metadata.

    Useful as a discovery call: the agent inspects the result and decides which
    reference(s) to fetch via ``get_reference``.
    """
    refs = [r.to_dict() for r in get_index()]
    return {"references": refs, "total": len(refs)}


def get_reference(name: str) -> dict[str, Any]:
    """Return the full markdown content of one reference.

    On miss, returns ``{"error": ..., "suggestions": [...]}`` so the agent can
    self-correct.
    """
    if not isinstance(name, str) or not name.strip():
        return {
            "error": "Parameter 'name' is required and must be a non-empty string.",
            "suggestions": [],
        }

    ref = get_by_name(name)
    if ref is None:
        all_names = [r.name for r in get_index()]
        suggestions = difflib.get_close_matches(name, all_names, n=3, cutoff=0.5)
        return {
            "error": f"No reference named '{name}'. See list_references() for the full set.",
            "suggestions": suggestions,
        }

    try:
        content = ref.path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": f"Failed to read '{name}': {exc}", "suggestions": []}

    return {
        "name": ref.name,
        "content": content,
        "lines": ref.lines,
    }


def _matches_scalar(value: str | None, filter_value: str) -> bool:
    return value is not None and value.casefold() == filter_value.casefold()


def _matches_list(values: list[str], filter_value: str) -> bool:
    fv = filter_value.casefold()
    return any(v.casefold() == fv for v in values)


def _persona_match(ref: Reference, persona: str) -> bool:
    """Persona filter checks both primary and collaborating lists."""
    return _matches_list(ref.fcp_personas_primary, persona) or _matches_list(
        ref.fcp_personas_collaborating, persona
    )


def _capability_match(ref: Reference, capability: str) -> bool:
    """Capability filter checks both primary and secondary."""
    return _matches_scalar(ref.fcp_capability, capability) or _matches_list(
        ref.fcp_capabilities_secondary, capability
    )


def reference_vocabulary() -> dict[str, list[str]]:
    """Distinct values present in the reference index, per facet.

    Derived from the bundled data rather than hardcoded, so it cannot drift
    from what the files actually declare.
    """
    vocab: dict[str, set[str]] = {
        "domain": set(),
        "capability": set(),
        "phase": set(),
        "persona": set(),
        "maturity": set(),
    }
    for ref in get_index():
        if ref.fcp_domain:
            vocab["domain"].add(ref.fcp_domain)
        if ref.fcp_capability:
            vocab["capability"].add(ref.fcp_capability)
        vocab["capability"].update(ref.fcp_capabilities_secondary)
        vocab["phase"].update(ref.fcp_phases)
        vocab["persona"].update(ref.fcp_personas_primary)
        vocab["persona"].update(ref.fcp_personas_collaborating)
        if ref.fcp_maturity_entry:
            vocab["maturity"].add(ref.fcp_maturity_entry)
    return {k: sorted(v) for k, v in vocab.items()}


def playbook_vocabulary() -> dict[str, list[str]]:
    """Distinct values present in the playbook index, per facet."""
    vocab: dict[str, set[str]] = {
        "scope": set(),
        "service": set(),
        "waste_category": set(),
        "confidence": set(),
    }
    for pb in get_playbook_index():
        for facet, value in (
            ("scope", pb.scope),
            ("service", pb.service),
            ("waste_category", pb.waste_category),
            ("confidence", pb.confidence),
        ):
            if value:
                vocab[facet].add(value)
    return {k: sorted(v) for k, v in vocab.items()}


def _unmatched_filters(
    active: dict[str, str], vocabulary: dict[str, list[str]]
) -> list[str]:
    """Active filter names whose value appears nowhere in the index.

    A filter listed here is the reason the result set is empty - as opposed to
    a legitimate no-overlap combination of individually-valid values.
    """
    unmatched = []
    for key, value in active.items():
        known = {v.casefold() for v in vocabulary.get(key, [])}
        if value.casefold() not in known:
            unmatched.append(key)
    return unmatched


def _empty_result_help(
    active: dict[str, str], vocabulary: dict[str, list[str]]
) -> dict[str, Any]:
    """Explain a zero-match faceted query instead of returning a bare total: 0.

    The name-based tools already offer difflib suggestions on a miss; the
    faceted tools returned nothing at all, leaving the caller unable to tell a
    typo from a genuine gap in coverage.
    """
    unmatched = _unmatched_filters(active, vocabulary)
    if unmatched:
        detail = (
            "No match for "
            + ", ".join(f"{k}={active[k]!r}" for k in unmatched)
            + " - "
            + ("that value is" if len(unmatched) == 1 else "those values are")
            + " not present in the bundled set."
        )
    else:
        detail = (
            "Every filter value is valid on its own, but no single item carries "
            "all of them together. Try relaxing one filter."
        )
    return {
        "hint": detail,
        "valid_values": {k: vocabulary.get(k, []) for k in active},
    }


def find_references(
    domain: str | None = None,
    capability: str | None = None,
    phase: str | None = None,
    persona: str | None = None,
    maturity: str | None = None,
) -> dict[str, Any]:
    """Filter references by FCP frontmatter.

    All parameters are optional and combine with AND semantics. String matches
    are case-insensitive and exact (no substring matching). Empty filters return
    the full index. A query that matches nothing returns ``hint`` and
    ``valid_values`` alongside ``total: 0``, so a typo is distinguishable from a
    genuine coverage gap.

    Args:
        domain: one of the four FinOps Framework domains, e.g.
            ``"Optimize Usage & Cost"``.
        capability: a FinOps Capability, matched against both the primary and
            the secondary declarations, e.g. ``"Rate Optimization"``.
        phase: ``Inform``, ``Optimize``, or ``Operate``.
        persona: matched against both primary and collaborating personas, e.g.
            ``"Engineering"``.
        maturity: ``Crawl``, ``Walk``, or ``Run`` - the entry gate below which
            the reference is premature.
    """
    filters = {
        "domain": domain,
        "capability": capability,
        "phase": phase,
        "persona": persona,
        "maturity": maturity,
    }
    active = {k: v for k, v in filters.items() if isinstance(v, str) and v.strip()}

    matches: list[Reference] = []
    for ref in get_index():
        if "domain" in active and not _matches_scalar(ref.fcp_domain, active["domain"]):
            continue
        if "capability" in active and not _capability_match(ref, active["capability"]):
            continue
        if "phase" in active and not _matches_list(ref.fcp_phases, active["phase"]):
            continue
        if "persona" in active and not _persona_match(ref, active["persona"]):
            continue
        if "maturity" in active and not _matches_scalar(
            ref.fcp_maturity_entry, active["maturity"]
        ):
            continue
        matches.append(ref)

    result: dict[str, Any] = {
        "filters": active,
        "references": [r.to_dict() for r in matches],
        "total": len(matches),
    }
    if not matches and active:
        result.update(_empty_result_help(active, reference_vocabulary()))
    return result


# --- playbook tools ---------------------------------------------------------


def list_playbooks() -> dict[str, Any]:
    """Return all bundled named-pattern playbooks.

    Each playbook is a ~80-130 line runbook scoped to one waste pattern
    (e.g. ``aws-zombie-nat-gateway``). Use this for discovery; fetch the body
    via ``get_playbook(name)``.
    """
    playbooks = [pb.to_dict() for pb in get_playbook_index()]
    return {"playbooks": playbooks, "total": len(playbooks)}


def get_playbook(name: str) -> dict[str, Any]:
    """Return the full markdown content of one playbook.

    On miss, returns ``{"error": ..., "suggestions": [...]}`` so the agent can
    self-correct.
    """
    if not isinstance(name, str) or not name.strip():
        return {
            "error": "Parameter 'name' is required and must be a non-empty string.",
            "suggestions": [],
        }

    pb = get_playbook_by_name(name)
    if pb is None:
        all_names = [p.name for p in get_playbook_index()]
        suggestions = difflib.get_close_matches(name, all_names, n=3, cutoff=0.5)
        return {
            "error": f"No playbook named '{name}'. See list_playbooks() for the full set.",
            "suggestions": suggestions,
        }

    try:
        content = pb.path.read_text(encoding="utf-8")
    except OSError as exc:
        return {"error": f"Failed to read '{name}': {exc}", "suggestions": []}

    return {
        "name": pb.name,
        "title": pb.title,
        "content": content,
        "lines": pb.lines,
    }


def find_playbooks(
    scope: str | None = None,
    service: str | None = None,
    waste_category: str | None = None,
    confidence: str | None = None,
) -> dict[str, Any]:
    """Filter playbooks by their pattern frontmatter.

    All parameters are optional and combine with AND semantics. String matches
    are case-insensitive and exact (no substring matching). A query that
    matches nothing returns `hint` and `valid_values` alongside `total: 0`.

    The double-backtick values listed below are the accepted vocabulary for
    each facet, and are pinned against the bundled data by
    `tests/test_conformance.py` - keep them in step when content changes.

    Args:
        scope: ``aws``, ``azure``, ``gcp``, or ``cross-cloud``.
        service: provider service name (e.g. ``"AWS NAT Gateway"``,
            ``"Azure Managed Disks"``). Exact-match against a free-text field -
            call ``list_playbooks`` first to see the values actually present,
            or filter on ``scope`` instead. A miss returns the valid values.
        waste_category: ``orphaned``, ``idle``, ``overprovisioned``,
            ``commitment-mismatch``, ``schedule-blindness``, ``modernization``,
            ``ai-ml-inefficiency``, or ``egress``.
        confidence: ``obvious``, ``likely``, or ``possible`` - the OptimNow
            three-tier confidence model defined in the
            `finops-waste-detection-playbooks` reference.
    """
    filters = {
        "scope": scope,
        "service": service,
        "waste_category": waste_category,
        "confidence": confidence,
    }
    active = {k: v for k, v in filters.items() if isinstance(v, str) and v.strip()}

    matches: list[Playbook] = []
    for pb in get_playbook_index():
        if "scope" in active and not _matches_scalar(pb.scope, active["scope"]):
            continue
        if "service" in active and not _matches_scalar(pb.service, active["service"]):
            continue
        if "waste_category" in active and not _matches_scalar(
            pb.waste_category, active["waste_category"]
        ):
            continue
        if "confidence" in active and not _matches_scalar(
            pb.confidence, active["confidence"]
        ):
            continue
        matches.append(pb)

    result: dict[str, Any] = {
        "filters": active,
        "playbooks": [pb.to_dict() for pb in matches],
        "total": len(matches),
    }
    if not matches and active:
        result.update(_empty_result_help(active, playbook_vocabulary()))
    return result
