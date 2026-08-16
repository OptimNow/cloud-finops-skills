"""MCP server wiring.

Registers the six tools with FastMCP - three over references (list / get /
find) and three over playbooks (list / get / find) - and exposes two ways to
serve them: stdio (the default, what every local MCP client spawns) and
streamable HTTP (for a hosted deployment). The actual tool logic lives in
:mod:`cloud_finops_mcp.tools` so it can be unit-tested without an MCP client.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import __version__
from . import metadata as _metadata
from . import tools as _tools

# Streamable HTTP defaults. Bind all interfaces because the only reason to run
# this transport is to be reachable from outside the process. The port is a
# fallback: `__main__` prefers $PORT, which is how hosting platforms assign one.
DEFAULT_HTTP_HOST = "0.0.0.0"  # noqa: S104 - see docstring on run_http
DEFAULT_HTTP_PORT = 8000

# MCP Apps (SEP-1865, extension id io.modelcontextprotocol/ui) resource: a
# self-contained HTML view that renders get_playbook()'s markdown as
# structured sections instead of raw text. Prototype for the 2026-07-28 spec
# - see ui/playbook_viewer.html for the iframe<->host wiring.
PLAYBOOK_VIEWER_URI = "ui://cloud-finops/playbook-viewer"
_PLAYBOOK_VIEWER_HTML = (
    Path(__file__).resolve().parent / "ui" / "playbook_viewer.html"
).read_text(encoding="utf-8")

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


@mcp.tool(meta={"ui": {"resourceUri": PLAYBOOK_VIEWER_URI}})
def get_playbook(name: str) -> dict[str, Any]:
    """Fetch the full markdown content of one playbook by slug.

    Args:
        name: Playbook slug as returned by ``list_playbooks`` (e.g.
            ``"aws-zombie-nat-gateway"``, ``"azure-orphan-disks"``,
            ``"cross-cloud-untagged-spend-drift"``).

    Returns ``{"name": ..., "title": ..., "content": "...", "lines": N}``.
    On miss, returns ``{"error": ..., "suggestions": [...]}`` with up to
    three string-distance matches so the caller can self-correct.

    A host with MCP Apps (SEP-1865) support may render this result via the
    linked ``ui://cloud-finops/playbook-viewer`` resource instead of showing
    the raw markdown.
    """
    return _tools.get_playbook(name)


@mcp.resource(
    PLAYBOOK_VIEWER_URI,
    name="Playbook viewer",
    mime_type="text/html;profile=mcp-app",
)
def playbook_viewer_ui() -> str:
    """MCP Apps UI resource linked from ``get_playbook``.

    Self-contained HTML/JS that renders the tool result's markdown as
    labelled sections (Problem / Symptoms / Detection / Fix / Anti-pattern /
    See also) inside the sandboxed iframe the host provides.
    """
    return _PLAYBOOK_VIEWER_HTML


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


def _warm_indexes() -> None:
    """Build both content indexes before serving.

    They are lru_cached and built lazily, so without this an empty content
    bundle stays silent until the first tool call - and then answers it with an
    empty list rather than an error. The index builders log at ERROR when they
    find nothing, which surfaces in the client's MCP server log at startup
    instead of never.
    """
    _metadata.get_index()
    _metadata.get_playbook_index()


async def run() -> None:
    """Run the MCP server over the stdio transport."""
    _warm_indexes()
    # FastMCP exposes both synchronous and asynchronous run helpers; we use
    # the async one so the entry point can be called from ``asyncio.run``.
    await mcp.run_stdio_async()


async def run_http(host: str = DEFAULT_HTTP_HOST, port: int = DEFAULT_HTTP_PORT) -> None:
    """Run the MCP server over the streamable HTTP transport.

    Args:
        host: interface to bind. Defaults to ``0.0.0.0`` because the only
            reason to run this transport is to be reachable from outside the
            process, typically from a platform's ingress.
        port: TCP port to bind.

    In the 1.x Python SDK, ``host``/``port``/``stateless_http`` are **constructor**
    keywords on ``FastMCP`` and ``run_streamable_http_async()`` takes no
    arguments - it reads ``self.settings``. The module-level ``mcp`` instance
    has to be built at import time because every ``@mcp.tool()`` decorator
    binds to it, so the settings are assigned here instead. The session manager
    is constructed lazily on first use, after this function has run, so it
    picks the values up.

    ``stateless_http`` is deliberate: a new transport and session per request,
    no server-side session affinity. This server is a pure read-only retrieval
    surface with no per-user state, so it costs nothing and it is what lets the
    deployment scale horizontally or run on a serverless platform.

    The route is FastMCP's default ``/mcp``, which is also what hosting
    platforms expect to find - do not move it without checking the target
    platform's health check.
    """
    _warm_indexes()
    mcp.settings.host = host
    mcp.settings.port = port
    mcp.settings.stateless_http = True
    await mcp.run_streamable_http_async()


__all__ = [
    "mcp",
    "run",
    "run_http",
    "DEFAULT_HTTP_HOST",
    "DEFAULT_HTTP_PORT",
    "__version__",
]
