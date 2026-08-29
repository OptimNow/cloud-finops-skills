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
import logging
from typing import Any

from .metadata import (
    Playbook,
    Reference,
    find_sections,
    get_by_name,
    get_index,
    get_playbook_by_name,
    get_playbook_index,
    section_labels,
    section_text,
    split_sections,
    strip_frontmatter,
)

logger = logging.getLogger(__name__)

# Cap on the headings listed back after a section miss. finops-azure has 100
# H2+H3 headings; listing them all is ~900 tokens, still an order of magnitude
# below the 21K-token body the caller is trying not to fetch, so the cap is
# generous on purpose and only exists to bound a pathological file.
SECTION_LIST_LIMIT = 120

# Ambiguity is reported, not resolved by silence: the caller gets the best
# match plus a short list of the runners-up so a wrong pick is one cheap,
# correctly-spelled retry away.
OTHER_MATCH_LIMIT = 5


def _log_zero_result(tool: str, active: dict[str, Any]) -> None:
    """Log a faceted query that matched nothing.

    A zero-result query is the purest coverage signal there is: an agent
    (so, a user) asked for something the bundled set does not have. The
    marker string is grepped from the hosted deployment's logs during the
    periodic coverage review (see the maintainer coverage-probe doctrine),
    which is why it must stay stable.
    """
    logger.info("zero-result query: %s filters=%r", tool, active)


def list_references() -> dict[str, Any]:
    """Return all bundled references with their discriminating FCP facets.

    Useful as a discovery call: the agent inspects the result and decides which
    reference(s) to fetch via ``get_reference``.

    Each entry is a summary, not the full record - see ``Reference.to_dict``
    for what is withheld and why. ``approx_tokens`` is the size hint: the
    library spans roughly 3K to 26K tokens per file, so it is the difference
    between one cheap fetch and a fifth of a context window.
    """
    refs = [r.to_dict() for r in get_index()]
    return {"references": refs, "total": len(refs)}


def _section_miss(ref: Reference, section: str, body: str) -> dict[str, Any]:
    """Loud failure for a section query that matched no heading.

    Silently returning the whole body would hand back the 26K tokens the
    caller was explicitly trying to avoid, and an empty result would leave it
    unable to tell a typo from a file with no sections. So the miss returns
    the vocabulary instead: every available heading, plus difflib's nearest
    guesses, which is everything needed to get the second call right.
    """
    labels = section_labels(body)
    if not labels:
        detail = (
            f"Reference '{ref.name}' has no H2 or H3 sections to select from. "
            "Call get_reference without 'section' to read it whole."
        )
    else:
        detail = (
            f"No section of '{ref.name}' matches {section!r}. Retry with one of "
            "the headings in 'available_sections', or call get_reference "
            "without 'section' for the full body."
        )
    _log_zero_result("get_reference", {"name": ref.name, "section": section})
    result: dict[str, Any] = {
        "error": detail,
        "available_sections": labels[:SECTION_LIST_LIMIT],
        "suggestions": difflib.get_close_matches(
            section, [s.heading for s in split_sections(body)], n=3, cutoff=0.4
        ),
    }
    if len(labels) > SECTION_LIST_LIMIT:
        result["available_sections_truncated"] = len(labels) - SECTION_LIST_LIMIT
    return result


def get_reference(name: str, section: str | None = None) -> dict[str, Any]:
    """Return one reference: the whole body, or a single section of it.

    With ``section`` omitted the payload is exactly what it has always been -
    ``{"name", "content", "lines"}`` with ``content`` the file verbatim,
    frontmatter included. Callers and the reference-browser widget depend on
    that, so it is pinned by a test.

    With ``section`` set, ``content`` is the matched H2/H3 span prefixed by the
    reference's H1 so the chunk is self-describing, and ``partial: True`` says
    plainly that this is not the whole file.

    On either kind of miss - unknown name, or a section that matches no
    heading - returns an error carrying enough vocabulary to retry.
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

    # An absent, empty, or whitespace-only section is the full-body path. A
    # model that fills the parameter in with "" should get the document, not
    # an error about a heading it never meant to ask for.
    if not isinstance(section, str) or not section.strip():
        return {
            "name": ref.name,
            "content": content,
            "lines": ref.lines,
        }

    body = strip_frontmatter(content, source=ref.path.name)
    matches = find_sections(body, section)
    if not matches:
        return _section_miss(ref, section, body)

    best = matches[0]
    chunk = f"# {ref.title}\n\n{section_text(body, best)}"
    result: dict[str, Any] = {
        "name": ref.name,
        "title": ref.title,
        "section": best.heading,
        "section_level": best.level,
        "partial": True,
        "note": (
            f"Section extract of '{ref.name}', not the full reference. Call "
            "get_reference without 'section' for the whole body."
        ),
        "content": chunk,
        "lines": chunk.count("\n"),
        "full_lines": ref.lines,
    }
    if len(matches) > 1:
        result["other_matching_sections"] = [
            s.label for s in matches[1 : 1 + OTHER_MATCH_LIMIT]
        ]
    return result


def _matches_scalar(value: str | None, filter_value: str) -> bool:
    return value is not None and value.casefold() == filter_value.casefold()


def _matches_list(values: list[str], filter_value: str) -> bool:
    fv = filter_value.casefold()
    return any(v.casefold() == fv for v in values)


def _persona_match(ref: Reference, persona: str, primary_only: bool = False) -> bool:
    """Persona filter checks the primary list, plus collaborating by default.

    The collaborating check is opt-out for a reason found in the field: a
    persona like Engineering collaborates on nearly everything in FinOps, so
    the OR over both lists barely narrows anything (the 2026-08-19 test
    measured exactly one exclusion across the whole library). The metadata is
    descriptively correct; ``primary_only`` is the operational cut.
    """
    if _matches_list(ref.fcp_personas_primary, persona):
        return True
    if primary_only:
        return False
    return _matches_list(ref.fcp_personas_collaborating, persona)


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
    persona_primary_only: bool = False,
) -> dict[str, Any]:
    """Filter references by FCP frontmatter.

    All parameters are optional and combine with AND semantics. String matches
    are case-insensitive and exact (no substring matching). Empty filters return
    the full index. A query that matches nothing returns ``hint`` and
    ``valid_values`` alongside ``total: 0``, so a typo is distinguishable from a
    genuine coverage gap.

    ``capability`` and ``persona`` filter over the secondary and collaborating
    declarations too, even though the returned entries no longer print them -
    the listing shape is trimmed for tokens, the filtering is not.

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
        persona_primary_only: when True, ``persona`` matches only
            ``fcp_personas_primary``. Use it when the default match barely
            narrows the set - broad personas like Engineering collaborate on
            nearly every file, so the collaborating list is descriptive
            rather than discriminating.
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
        if "persona" in active and not _persona_match(
            ref, active["persona"], primary_only=persona_primary_only
        ):
            continue
        if "maturity" in active and not _matches_scalar(
            ref.fcp_maturity_entry, active["maturity"]
        ):
            continue
        matches.append(ref)

    reported_filters: dict[str, Any] = dict(active)
    if persona_primary_only and "persona" in active:
        reported_filters["persona_primary_only"] = True

    result: dict[str, Any] = {
        "filters": reported_filters,
        "references": [r.to_dict() for r in matches],
        "total": len(matches),
    }
    if not matches and active:
        result.update(_empty_result_help(active, reference_vocabulary()))
        _log_zero_result("find_references", reported_filters)
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
        _log_zero_result("find_playbooks", active)
    return result
