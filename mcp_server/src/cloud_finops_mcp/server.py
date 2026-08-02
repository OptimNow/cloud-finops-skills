"""MCP server wiring.

Registers the six tools with FastMCP and runs the stdio transport - three over
references (list / get / find) and three over playbooks (list / get / find).
The actual tool logic lives in :mod:`cloud_finops_mcp.tools` so it can be
unit-tested without an MCP client.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __version__
from . import metadata as _metadata
from . import tools as _tools

mcp = FastMCP(
    "cloud-finops",
    instructions=(
        "Cloud FinOps knowledge by OptimNow. Two retrieval surfaces: "
        "REFERENCES (long-form provider/discipline files) and PLAYBOOKS "
        "(small named-pattern runbooks for specific waste patterns). "
        "REFERENCES: list_references() to discover, find_references(domain=, "
        "capability=, phase=, persona=, maturity=) to narrow by FinOps "
        "Capability/Phase facets, get_reference(name=) to fetch one body. "
        "PLAYBOOKS: list_playbooks() to discover, find_playbooks(scope=, "
        "service=, waste_category=, confidence=) to narrow by pattern facets, "
        "get_playbook(name=) to fetch one body. "
        "Use a playbook for 'how do I detect/fix this specific pattern' "
        "(zombie NAT, snapshot sprawl, idle ELB, etc.). Use a reference for "
        "billing mechanics, commitment strategy, allocation methodology, "
        "or any cross-pattern reasoning."
    ),
)


@mcp.tool()
def list_references() -> dict[str, Any]:
    """List every bundled FinOps reference with its FCP metadata.

    Returns a dict shaped ``{"references": [...], "total": N}`` where each
    entry includes ``name``, ``description``, FCP fields (``fcp_domain``,
    ``fcp_capability``, ``fcp_phases`` etc.) and ``lines``.
    """
    return _tools.list_references()


@mcp.tool()
def get_reference(name: str) -> dict[str, Any]:
    """Fetch the full markdown content of one reference by name.

    Args:
        name: Reference name as returned by ``list_references`` (e.g.
            ``"finops-aws"``, ``"finops-genai-capacity"``,
            ``"optimnow-methodology"``).

    Returns the dict ``{"name": ..., "content": "...", "lines": N}``. On miss,
    returns ``{"error": ..., "suggestions": [...]}`` with up to three
    string-distance matches so the caller can self-correct.
    """
    return _tools.get_reference(name)


@mcp.tool()
def find_references(
    domain: str | None = None,
    capability: str | None = None,
    phase: str | None = None,
    persona: str | None = None,
    maturity: str | None = None,
) -> dict[str, Any]:
    """Filter references by FinOps Capability/Phase (FCP) frontmatter.

    All filters are optional and combine with AND semantics. String matching
    is case-insensitive and exact (not substring). Examples:

    - ``find_references(domain="Optimize Usage & Cost")``
    - ``find_references(phase="Optimize", persona="Engineering")``
    - ``find_references(capability="Rate Optimization")``
    - ``find_references(maturity="Crawl")``

    Args:
        domain: FinOps Framework domain (e.g. ``"Optimize Usage & Cost"``,
            ``"Quantify Business Value"``, ``"Manage the FinOps Practice"``).
        capability: FinOps capability (matches ``fcp_capability`` and
            ``fcp_capabilities_secondary``).
        phase: FinOps phase (``"Inform"``, ``"Optimize"``, ``"Operate"``).
        persona: Persona (matches ``fcp_personas_primary`` and
            ``fcp_personas_collaborating``).
        maturity: Entry maturity level (``"Crawl"``, ``"Walk"``, ``"Run"``).

    Returns ``{"filters": {...}, "references": [...], "total": N}``. A query
    that matches nothing also returns `hint` and `valid_values`, so a typo is
    distinguishable from a genuine gap in coverage.
    """
    return _tools.find_references(
        domain=domain,
        capability=capability,
        phase=phase,
        persona=persona,
        maturity=maturity,
    )


@mcp.tool()
def list_playbooks() -> dict[str, Any]:
    """List every bundled named-pattern playbook.

    Each playbook is a small (~80-130 line) runbook scoped to one waste
    pattern (e.g. ``aws-zombie-nat-gateway``, ``azure-orphan-disks``). Returns
    ``{"playbooks": [...], "total": N}`` where each entry includes ``name``,
    ``title``, ``scope`` (aws/azure/gcp/cross-cloud), ``service``,
    ``waste_category``, ``confidence`` (obvious/likely/possible), and
    ``lines``.
    """
    return _tools.list_playbooks()


@mcp.tool()
def get_playbook(name: str) -> dict[str, Any]:
    """Fetch the full markdown content of one playbook by slug.

    Args:
        name: Playbook slug as returned by ``list_playbooks`` (e.g.
            ``"aws-zombie-nat-gateway"``, ``"azure-orphan-disks"``,
            ``"cross-cloud-untagged-spend-drift"``).

    Returns ``{"name": ..., "title": ..., "content": "...", "lines": N}``.
    On miss, returns ``{"error": ..., "suggestions": [...]}`` with up to
    three string-distance matches so the caller can self-correct.
    """
    return _tools.get_playbook(name)


@mcp.tool()
def find_playbooks(
    scope: str | None = None,
    service: str | None = None,
    waste_category: str | None = None,
    confidence: str | None = None,
) -> dict[str, Any]:
    """Filter playbooks by their pattern frontmatter.

    All filters are optional and combine with AND semantics. String matching
    is case-insensitive and exact. Examples:

    - ``find_playbooks(scope="aws")`` - all AWS-specific playbooks
    - ``find_playbooks(waste_category="idle")`` - every idle-resource pattern
    - ``find_playbooks(scope="cross-cloud", confidence="obvious")``

    Args:
        scope: ``"aws"``, ``"azure"``, ``"gcp"``, or ``"cross-cloud"``.
        service: Provider service exact-match (e.g. ``"AWS NAT Gateway"``).
        waste_category: ``"orphaned"``, ``"idle"``, ``"overprovisioned"``,
            ``"commitment-mismatch"``, ``"schedule-blindness"``,
            ``"modernization"``, ``"ai-ml-inefficiency"``, or ``"egress"``.
        confidence: ``"obvious"`` (single signal is enough),
            ``"likely"`` (two signals required), or ``"possible"``
            (needs human review). From the OptimNow three-tier confidence
            model in `finops-waste-detection-playbooks`.

    Returns ``{"filters": {...}, "playbooks": [...], "total": N}``. A query
    that matches nothing also returns `hint` and `valid_values`, so a typo is
    distinguishable from a genuine gap in coverage.
    """
    return _tools.find_playbooks(
        scope=scope,
        service=service,
        waste_category=waste_category,
        confidence=confidence,
    )


async def run() -> None:
    """Run the MCP server over the stdio transport."""
    # Touch both indexes before serving. They are lru_cached and built lazily,
    # so without this an empty content bundle stays silent until the first tool
    # call - and then answers it with an empty list rather than an error. The
    # index builders log at ERROR when they find nothing, which surfaces in the
    # client's MCP server log at startup instead of never.
    _metadata.get_index()
    _metadata.get_playbook_index()
    # FastMCP exposes both synchronous and asynchronous run helpers; we use
    # the async one so the entry point can be called from ``asyncio.run``.
    await mcp.run_stdio_async()


__all__ = ["mcp", "run", "__version__"]
