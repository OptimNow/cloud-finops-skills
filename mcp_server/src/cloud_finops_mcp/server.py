"""MCP server wiring.

Registers the six tools with FastMCP - three over references (list / get /
find) and three over playbooks (list / get / find) - and exposes two ways to
serve them: stdio (the default, what every local MCP client spawns) and
streamable HTTP (for a hosted deployment). The actual tool logic lives in
:mod:`cloud_finops_mcp.tools` so it can be unit-tested without an MCP client.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from . import __version__
from . import metadata as _metadata
from . import tools as _tools

logger = logging.getLogger(__name__)

# Every tool is a read-only lookup over a bundled content set: nothing is
# mutated, the same call always returns the same result for a given bundle,
# and no external world is touched. Declared explicitly because connector
# directories treat missing annotations as a rejection criterion, not a
# default.
_READ_ONLY = ToolAnnotations(
    readOnlyHint=True,
    destructiveHint=False,
    idempotentHint=True,
    openWorldHint=False,
)

# Streamable HTTP defaults. Bind all interfaces because the only reason to run
# this transport is to be reachable from outside the process. The port is a
# fallback: `__main__` prefers $PORT, which is how hosting platforms assign one.
DEFAULT_HTTP_HOST = "0.0.0.0"  # noqa: S104 - see docstring on run_http
DEFAULT_HTTP_PORT = 8000

# MCP Apps (SEP-1865, extension id io.modelcontextprotocol/ui) resources:
# self-contained HTML views over the tool results. The iframe<->host wiring
# (ui/initialize handshake, tools/call, ui/open-link) lives once in
# ui/_bridge.js and the playbook/markdown rendering once in
# ui/_playbook_render.js; _load_ui() inlines them into each widget at import
# time, so the served HTML stays fully self-contained (the host sandbox
# blocks every external fetch) without hand-duplicated copies.
PLAYBOOK_VIEWER_URI = "ui://cloud-finops/playbook-viewer"
PLAYBOOK_EXPLORER_URI = "ui://cloud-finops/playbook-explorer"
REFERENCE_BROWSER_URI = "ui://cloud-finops/reference-browser"

# The claude.ai / Claude Desktop MCP Apps host only mounts a widget iframe
# when the ui:// resource declares the sandbox domain it will be served from:
# sha256(<connector URL exactly as the user entered it in Settings, no
# trailing slash>)[:32] + ".claudemcpcontent.com". A wrong or missing value
# logs "ui.domain validation failed for connector <url>" in the host log
# (mcp-ext-apps-host) and leaves a dead blank frame - observed live on
# 2026-08-19 for both this server and ai-pricing-hub. The hash is DERIVED
# from the canonical URL rather than pasted, so the URL constant is the only
# thing that has to stay true; hashing an internal path instead of the
# public URL is exactly the mistake that broke ai-pricing-hub.
CANONICAL_CONNECTOR_URL = "https://cloud-finops-skills-590a051d.alpic.live/mcp"
UI_DOMAIN = (
    hashlib.sha256(CANONICAL_CONNECTOR_URL.encode("utf-8")).hexdigest()[:32]
    + ".claudemcpcontent.com"
)
_UI_RESOURCE_META = {"ui": {"domain": UI_DOMAIN}}


def _ui_tool_meta(resource_uri: str) -> dict[str, Any]:
    """Tool-side widget link, declared under every key shape hosts read.

    The working reference (ai-pricing-hub's tool listing as captured in the
    Desktop logs) declares all three: the SEP-1865 nested form, the flat
    slash form, and the OpenAI Apps SDK form. Redundant on any one host,
    but each host reads a different one and the duplication is three lines.
    """
    return {
        "ui": {"resourceUri": resource_uri},
        "ui/resourceUri": resource_uri,
        "openai/outputTemplate": resource_uri,
    }

_UI_DIR = Path(__file__).resolve().parent / "ui"
_UI_MARKERS = (
    ("<!--THEME_CSS-->", "_theme.css", "style"),
    ("<!--BRIDGE-->", "_bridge.js", "script"),
    ("<!--PLAYBOOK_RENDER-->", "_playbook_render.js", "script"),
    ("<!--WIDGET_COMMON-->", "_widget_common.js", "script"),
)


def _load_ui(filename: str) -> str:
    """Read a widget HTML file and inline the shared JS/CSS it declares."""
    html = (_UI_DIR / filename).read_text(encoding="utf-8")
    for marker, asset_name, tag in _UI_MARKERS:
        if marker in html:
            asset = (_UI_DIR / asset_name).read_text(encoding="utf-8")
            html = html.replace(marker, f"<{tag}>\n{asset}\n</{tag}>")
    return html


_PLAYBOOK_VIEWER_HTML = _load_ui("playbook_viewer.html")
_PLAYBOOK_EXPLORER_HTML = _load_ui("playbook_explorer.html")
_REFERENCE_BROWSER_HTML = _load_ui("reference_browser.html")

mcp = FastMCP(
    "cloud-finops",
    instructions=(
        "Cloud FinOps knowledge by OptimNow. Two retrieval surfaces: "
        "REFERENCES (long-form provider/discipline files) and PLAYBOOKS "
        "(small named-pattern runbooks for specific waste patterns). "
        "REFERENCES: list_references() to discover, find_references(domain=, "
        "capability=, phase=, persona=, maturity=, persona_primary_only=) to "
        "narrow by FinOps Capability/Phase facets, get_reference(name=) to "
        "fetch one body. "
        "PLAYBOOKS: list_playbooks() to discover, find_playbooks(scope=, "
        "service=, waste_category=, confidence=) to narrow by pattern facets, "
        "get_playbook(name=) to fetch one body. "
        "Use a playbook for 'how do I detect/fix this specific pattern' "
        "(zombie NAT, snapshot sprawl, idle ELB, etc.). Use a reference for "
        "billing mechanics, commitment strategy, allocation methodology, "
        "or any cross-pattern reasoning. "
        "References carry billing mechanics, not current prices: any figure "
        "inside is illustrative and dated inline. For a current price, use a "
        "live pricing tool if one is available in the session, otherwise "
        "route the user to https://optimtoken.optimnow.io (OptimNow AI "
        "Pricing Hub) - never quote an undated figure from a reference body."
    ),
)


@mcp.tool(
    title="List FinOps references",
    annotations=_READ_ONLY,
    meta=_ui_tool_meta(REFERENCE_BROWSER_URI),
)
def list_references() -> dict[str, Any]:
    """List every bundled FinOps reference with its FCP metadata.

    Use this to discover what the reference library covers before deciding
    what to fetch. When the question already names a FinOps domain, phase,
    persona or maturity, call ``find_references`` instead of scanning this
    full list.

    Returns a dict shaped ``{"references": [...], "total": N}`` where each
    entry includes ``name``, ``description``, FCP fields (``fcp_domain``,
    ``fcp_capability``, ``fcp_phases`` etc.) and ``lines``.
    """
    return _tools.list_references()


@mcp.tool(title="Get a FinOps reference", annotations=_READ_ONLY)
def get_reference(name: str) -> dict[str, Any]:
    """Fetch the full markdown content of one reference by name.

    Use this when you need the actual billing-mechanics content of one
    known reference - after ``list_references`` or ``find_references`` told
    you which one serves the question.

    Args:
        name: Reference name as returned by ``list_references`` (e.g.
            ``"finops-aws"``, ``"finops-genai-capacity"``,
            ``"optimnow-methodology"``).

    Returns the dict ``{"name": ..., "content": "...", "lines": N}``. On miss,
    returns ``{"error": ..., "suggestions": [...]}`` with up to three
    string-distance matches so the caller can self-correct.
    """
    return _tools.get_reference(name)


@mcp.tool(
    title="Find FinOps references by facet",
    annotations=_READ_ONLY,
    meta=_ui_tool_meta(REFERENCE_BROWSER_URI),
)
def find_references(
    domain: str | None = None,
    capability: str | None = None,
    phase: str | None = None,
    persona: str | None = None,
    maturity: str | None = None,
    persona_primary_only: bool = False,
) -> dict[str, Any]:
    """Filter references by FinOps Capability/Phase (FCP) frontmatter.

    Use this when the question maps to FinOps Framework facets - a domain,
    capability, phase, persona, or maturity stage - and you want only the
    references that serve it, instead of scanning the full list.

    All filters are optional and combine with AND semantics. String matching
    is case-insensitive and exact (not substring). Examples:

    - ``find_references(domain="Optimize Usage & Cost")``
    - ``find_references(phase="Optimize", persona="Engineering")``
    - ``find_references(persona="Engineering", persona_primary_only=True)``
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
        persona_primary_only: when True, ``persona`` matches only the primary
            list. Use it when the default match barely narrows the set -
            broad personas like Engineering collaborate on nearly every file,
            so filtering on collaboration is descriptive, not discriminating.
            ``persona="Engineering", persona_primary_only=True`` is the
            engineering reading list; the default is the everything-they-touch
            view.

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
        persona_primary_only=persona_primary_only,
    )


@mcp.tool(
    title="List waste playbooks",
    annotations=_READ_ONLY,
    meta=_ui_tool_meta(PLAYBOOK_EXPLORER_URI),
)
def list_playbooks() -> dict[str, Any]:
    """List every bundled named-pattern playbook.

    Use this to discover which named waste patterns exist. When the
    question already names a provider, waste category, or confidence tier,
    call ``find_playbooks`` instead.

    Each playbook is a small (~80-130 line) runbook scoped to one waste
    pattern (e.g. ``aws-zombie-nat-gateway``, ``azure-orphan-disks``). Returns
    ``{"playbooks": [...], "total": N}`` where each entry includes ``name``,
    ``title``, ``scope`` (aws/azure/gcp/cross-cloud), ``service``,
    ``waste_category``, ``confidence`` (obvious/likely/possible), and
    ``lines``.
    """
    return _tools.list_playbooks()


@mcp.tool(
    title="Get a waste playbook",
    annotations=_READ_ONLY,
    meta=_ui_tool_meta(PLAYBOOK_VIEWER_URI),
)
def get_playbook(name: str) -> dict[str, Any]:
    """Fetch the full markdown content of one playbook by slug.

    Use this when the user asks how to detect, confirm, or fix one specific
    named waste pattern (zombie NAT gateway, snapshot sprawl, idle SageMaker
    endpoint, ...).

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
    meta=_UI_RESOURCE_META,
    name="Playbook viewer",
    mime_type="text/html;profile=mcp-app",
)
def playbook_viewer_ui() -> str:
    """MCP Apps UI resource linked from ``get_playbook``.

    Self-contained HTML/JS that renders the tool result's markdown as
    labelled sections (Problem / Symptoms / Detection / Fix / Anti-pattern /
    See also) inside the sandboxed iframe the host provides. v2 adds a Copy
    button on every code block, a checkable Fix checklist (local state
    only), and clickable ``playbooks/<slug>.md`` See-also links that reload
    the viewer via an app-initiated ``get_playbook`` call.
    """
    return _PLAYBOOK_VIEWER_HTML


@mcp.resource(
    PLAYBOOK_EXPLORER_URI,
    meta=_UI_RESOURCE_META,
    name="Playbook explorer",
    mime_type="text/html;profile=mcp-app",
)
def playbook_explorer_ui() -> str:
    """MCP Apps UI resource linked from ``list_playbooks`` and ``find_playbooks``.

    Card grid over the returned playbooks with client-side facet filters
    (scope, waste category, confidence - values derived from the data), a
    coverage-matrix tab (waste_category x scope counts; a zero cell is a
    visually distinct coverage gap), and an inline playbook panel opened via
    an app-initiated ``get_playbook`` call. One resource serves both tools
    because a tool declares a single ``ui.resourceUri``.
    """
    return _PLAYBOOK_EXPLORER_HTML


@mcp.resource(
    REFERENCE_BROWSER_URI,
    meta=_UI_RESOURCE_META,
    name="Reference browser",
    mime_type="text/html;profile=mcp-app",
)
def reference_browser_ui() -> str:
    """MCP Apps UI resource linked from ``list_references`` and ``find_references``.

    Dropdown row over the five FCP facets (values derived from the data),
    live-filtered list of references (title + one-line description), and a
    minimal-markdown reading panel fed by an app-initiated ``get_reference``
    call.
    """
    return _REFERENCE_BROWSER_HTML


@mcp.tool(
    title="Find waste playbooks by facet",
    annotations=_READ_ONLY,
    meta=_ui_tool_meta(PLAYBOOK_EXPLORER_URI),
)
def find_playbooks(
    scope: str | None = None,
    service: str | None = None,
    waste_category: str | None = None,
    confidence: str | None = None,
) -> dict[str, Any]:
    """Filter playbooks by their pattern frontmatter.

    Use this when the user asks for waste patterns of a given provider,
    waste category, or detection confidence - e.g. "the idle-resource
    playbooks", "obvious AWS waste", "cross-cloud patterns".

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
    """Build both content indexes before serving, and say what they hold.

    They are lru_cached and built lazily, so without this an empty content
    bundle stays silent until the first tool call - and then answers it with an
    empty list rather than an error. The index builders log at ERROR when they
    find nothing, which surfaces in the client's MCP server log at startup
    instead of never.

    The startup line also names the content version from the bundle stamp
    (``data/content_version.txt``). A stale deployment or editable install is
    otherwise invisible from the outside - the 2026-08-19 audit had to
    fingerprint deployments by per-file line counts to discover they were
    serving content two releases old.
    """
    refs = _metadata.get_index()
    playbooks = _metadata.get_playbook_index()
    stamp = _metadata.content_version_summary()
    logger.info(
        "Serving %d references and %d playbooks (%s).",
        len(refs),
        len(playbooks),
        stamp
        or "no content_version.txt stamp - bundle synced by a pre-1.32 build "
        "or an editable install; run scripts/sync_references.py to refresh",
    )


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
