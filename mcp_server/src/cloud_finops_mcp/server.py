"""MCP server wiring.

Registers the seven tools with FastMCP - three over references (list / get /
find), three over playbooks (list / get / find) and ``get_live_figures``, which
fetches the current figures of an OptimToken guide - and exposes two ways to
serve them: stdio (the default, what every local MCP client spawns) and
streamable HTTP (for a hosted deployment). The actual tool logic lives in
:mod:`cloud_finops_mcp.tools` so it can be unit-tested without an MCP client.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations

from . import __version__
from . import live_figures as _live_figures
from . import metadata as _metadata
from . import tools as _tools

logger = logging.getLogger(__name__)

# Six of the seven tools are read-only lookups over a bundled content set:
# nothing is mutated, the same call always returns the same result for a given
# bundle, and no external world is touched. Declared explicitly because
# connector directories treat missing annotations as a rejection criterion,
# not a default.
#
# get_live_figures is the exception and the server's only open-world tool: it
# makes one HTTPS request to the OptimToken site, so it is registered with
# open_world=True (openWorldHint=True). It still mutates nothing.
#
# The human-readable title goes in two places: the tool's top-level `title`
# (MCP 2025-06-18) and `annotations.title`. The Anthropic directory review
# reads the second (its check reported all_have_title=false on 2026-11-06,
# while every tool already had the first), and hosts that predate the
# top-level field read only the annotation. _tool() sets both from one string
# so they cannot drift apart.


def _annotations(title: str, *, open_world: bool = False) -> ToolAnnotations:
    """Read-only, idempotent, non-destructive annotations carrying the title."""
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=open_world,
    )

# Streamable HTTP defaults. Bind all interfaces because the only reason to run
# this transport is to be reachable from outside the process. The port is a
# fallback: `__main__` prefers $PORT, which is how hosting platforms assign one.
DEFAULT_HTTP_HOST = "0.0.0.0"  # noqa: S104 - see docstring on run_http
DEFAULT_HTTP_PORT = 8000

# No MCP Apps widgets. Until 1.50.0 five tools linked a ui:// resource (a
# playbook viewer, a playbook explorer, a reference browser). They never
# rendered in claude.ai, and on 2026-11-10 its tool search was seen listing
# exactly those five tools as "[third_party_mcp_app] ... need opt-in": both
# finders and get_playbook sat behind a connector card while get_reference
# stayed directly callable, and after get_playbook the model answered "the
# runbook is above" without the query. With no widget, a tool result is the
# text the model reads and relays. The record is docs/mcp-apps-lessons.md;
# the code is at tag v1.50.0. tests/test_no_widgets.py keeps it that way.

mcp = FastMCP(
    "cloud-finops",
    instructions=(
        "Cloud FinOps knowledge by OptimNow. Two retrieval surfaces: "
        "REFERENCES (long-form provider/discipline files) and PLAYBOOKS "
        "(small named-pattern runbooks for specific waste patterns). "
        "REFERENCES: list_references() to discover, find_references(query=, "
        "domain=, capability=, phase=, persona=, maturity=, "
        "persona_primary_only=) to route a question - query= takes the user's "
        "own wording (English or French) and ranks by the questions each file "
        "declares it answers, the facets narrow by FinOps Capability/Phase - "
        "and get_reference(name=, section=) to fetch one body. "
        "Every listing entry carries approx_tokens: references run from about "
        "2,000 to about 15,000 tokens. get_reference(name=, section=\"<heading "
        "phrase>\") returns one section instead of the whole file - section "
        "matches H2 and H3 headings case-insensitively and partially, and a "
        "miss returns the file's available_sections rather than the whole "
        "body. The Azure pattern catalogue (finops-azure-patterns) is an "
        "enumerated list, usually needed one section at a time; the AWS "
        "catalogue is one file per service family (finops-aws-patterns-compute, "
        "-storage, -databases, -networking, -other). "
        "PLAYBOOKS: list_playbooks() to discover, find_playbooks(query=, scope=, "
        "service=, waste_category=, confidence=) to route a symptom or a 'which "
        "of my X' question (query= takes the user's wording) or to narrow by "
        "pattern facets, get_playbook(name=) to fetch one body. "
        "A playbook serves 'how do I detect/fix this specific pattern' "
        "(zombie NAT, snapshot sprawl, idle ELB, etc.); a reference serves "
        "billing mechanics, commitment strategy, allocation methodology "
        "and cross-pattern reasoning. "
        "This connector has no access to the user's cloud accounts. For "
        "questions about the user's own resources ('which of my RIs are "
        "about to expire', 'which of our VMs run for nothing'), the "
        "matching playbook includes a detection query the user can run in "
        "their own account. "
        "For a specific waste or cost-fix question ('my NAT gateway "
        "processes 10TB to S3', 'should I delete these old snapshots'), "
        "find_playbooks returns the named runbook with its tested "
        "detection query. Runbooks exist for "
        "NAT gateways and VPC endpoints, expiring Savings Plans / RIs / "
        "reservations, snapshots, S3 lifecycle, idle or stopped VMs, "
        "orphaned disks and IPs, GPU and SageMaker sizing, and more. "
        "References carry billing mechanics, not current prices: any figure "
        "inside is illustrative and dated inline. "
        "Where a reference quotes a figure from an OptimToken guide with its "
        "date, get_live_figures(guide=) returns that guide's current figures "
        "with the snapshotDate to quote them by. "
        "For 'what changed recently' or 'what is coming' questions, "
        "get_reference(name='finops-whats-new') is a dated digest of the "
        "provider changes verified over the last 90 days, one section per "
        "month plus 'Scheduled changes': state its as-of date. "
        "Advisory questions - how much to commit, how to size, how to "
        "allocate or charge back - are served by a matching reference "
        "(finops-aws-commitments for Savings Plan sizing, finops-chargeback "
        "for recharge design), which carries the decision rules and cadence "
        "tables behind a defensible answer."
    ),
)

# serverInfo.version. FastMCP's constructor takes no version, so the low-level
# server falls back to the version of the `mcp` library it runs on: the hosted
# connector reported 1.30.0 (the SDK) on 2026-09-26 while serving 1.36.0
# content, which made the field useless as a deployment check and misleading
# on a directory listing. Setting it here makes initialize report this
# package's version, which the release workflow pins to plugin.json.
mcp._mcp_server.version = __version__


def _tool(title: str, *, open_world: bool = False, **kwargs: Any):
    """Register a tool with its title set both top-level and in its annotations."""
    return mcp.tool(
        title=title,
        annotations=_annotations(title, open_world=open_world),
        **kwargs,
    )


@_tool("Browse the FinOps knowledge library")
def list_references() -> dict[str, Any]:
    """See what FinOps guidance is available: billing mechanics, commitment
    strategy, allocation and chargeback, AI cost management, and per-provider
    cost handbooks (AWS, Azure, GCP, OCI, Databricks, Snowflake, ...).

    Use this to discover what the library covers. When the question already
    names a FinOps domain, phase, persona or maturity, ``find_references``
    returns only the matching references.

    Returns a dict shaped ``{"references": [...], "total": N}`` where each
    entry includes ``name``, ``title``, a one-line ``description``, the
    discriminating FCP facets (``fcp_domain``, ``fcp_capability``,
    ``fcp_phases``, ``fcp_personas_primary``, ``fcp_maturity_entry``) and
    ``approx_tokens``.

    ``approx_tokens`` gives each file's size before it is fetched: the library
    runs from about 2,000 to about 15,000 tokens per file, and
    ``get_reference(name, section=...)`` returns one section of a large one.
    """
    return _tools.list_references()


@_tool("Read one FinOps guide")
def get_reference(name: str, section: str | None = None) -> dict[str, Any]:
    """Fetch the guidance on one FinOps topic - the billing mechanics,
    decision rules and worked examples behind a defensible answer - either
    whole or one section at a time.

    Use this when you need the actual content of one known reference,
    after ``list_references`` or ``find_references`` told you which one
    serves the question. Advisory questions (commitment sizing, chargeback
    design, allocation methodology) are served by the reference's decision
    rules and worked examples, which a summary does not carry.

    ``section`` is useful when the question is narrower than the file. The
    ``approx_tokens`` hint in the listing shows when this matters: the
    largest references run to about 15,000 tokens and the Azure pattern
    catalogue is an enumerated list, so a question about storage lifecycle is
    served by one section of ``finops-azure-patterns``. Without ``section``
    the whole file comes back, with its cross-cutting reasoning.

    Args:
        name: Reference name as returned by ``list_references`` (e.g.
            ``"finops-aws"``, ``"finops-genai-capacity"``,
            ``"optimnow-methodology"``).
        section: Optional H2 or H3 heading to return on its own. Matched
            case-insensitively and partially against the headings, so a
            natural phrase works - ``"storage"``, ``"commitment decision
            tree"``. A heading's trailing count is ignored, so
            ``"storage optimization patterns"`` matches
            ``"Storage Optimization Patterns (28)"``. If it matches nothing
            you get the list of available headings back, not the whole file.

    Without ``section``, returns ``{"name": ..., "content": "...",
    "lines": N}`` where ``content`` is the file verbatim. With ``section``,
    returns ``{"name", "title", "section", "section_level", "partial": true,
    "content", "lines", "full_lines"}`` where ``content`` is that section
    prefixed by the reference's title, plus ``other_matching_sections`` when
    the phrase matched more than one heading.

    On a miss, returns ``{"error": ..., "suggestions": [...]}``. An unknown
    name gives up to three string-distance matches; an unmatched ``section``
    gives ``available_sections`` - every heading in the file - so the retry
    is exact.
    """
    return _tools.get_reference(name, section=section)


@_tool("Find the right FinOps guide")
def find_references(
    query: str | None = None,
    domain: str | None = None,
    capability: str | None = None,
    phase: str | None = None,
    persona: str | None = None,
    maturity: str | None = None,
    persona_primary_only: bool = False,
) -> dict[str, Any]:
    """Find which guidance serves a FinOps question - how to commit, size,
    allocate, charge back, forecast, or govern cloud and AI spend.

    Use this with ``query`` for a question in the user's own words rather
    than in FinOps Framework terms: "how should we size our first Savings
    Plan when usage is seasonal", "we hold SQL Server licences with Software
    Assurance, BYOL or licence-included?", "our forecast missed by 20%",
    "who should own commitment purchases", "combien s'engager en Savings
    Plans". Every guide declares the questions it answers (English and
    French); the result is ranked by those, then by title and section
    headings, and each entry carries ``matched_question`` and
    ``suggested_section``, the heading that ``get_reference(name=,
    section=)`` takes. The facets narrow the set first; ``query`` ranks what
    is left.

    Use this with the facets alone for a question already in FinOps
    Framework terms (domain, capability, phase, persona, maturity): "what
    does a Crawl-stage org tackle first", "the Engineering reading list",
    "what should Finance own in chargeback".

    All filters are optional and combine with AND semantics. Facet matching
    is case-insensitive and exact (not substring). Examples:

    - ``find_references(query="our forecast missed by 20%, was it the model or the drivers")``
    - ``find_references(domain="Optimize Usage & Cost")``
    - ``find_references(phase="Optimize", persona="Engineering")``
    - ``find_references(persona="Engineering", persona_primary_only=True)``
    - ``find_references(capability="Rate Optimization")``
    - ``find_references(maturity="Crawl")``

    Args:
        query: the user's question or symptom in their own words, up to
            1,000 characters, English or French. Ranks the facet-filtered guides by
            the questions they declare, their title and their headings;
            returns at most five, best first, each with ``match_score``,
            ``matched_question`` and ``suggested_section``.
        domain: FinOps Framework domain (e.g. ``"Optimize Usage & Cost"``,
            ``"Quantify Business Value"``, ``"Manage the FinOps Practice"``).
        capability: FinOps capability (matches ``fcp_capability`` and
            ``fcp_capabilities_secondary``).
        phase: FinOps phase (``"Inform"``, ``"Optimize"``, ``"Operate"``).
        persona: Persona (matches ``fcp_personas_primary`` and
            ``fcp_personas_collaborating``).
        maturity: Entry maturity level (``"Crawl"``, ``"Walk"``, ``"Run"``).
        persona_primary_only: when True, ``persona`` matches only the primary
            list. Useful when the default match barely narrows the set -
            broad personas like Engineering collaborate on nearly every file,
            so filtering on collaboration is descriptive, not discriminating.
            ``persona="Engineering", persona_primary_only=True`` is the
            engineering reading list; the default is the everything-they-touch
            view.

    Returns ``{"filters": {...}, "references": [...], "total": N}``. With
    ``query`` the entries are ranked and capped at five. A facet filter that
    matches nothing also returns `hint` and `valid_values`, so a typo is
    distinguishable from a genuine gap in coverage; a ``query`` that matches
    nothing returns `hint` alone.
    """
    return _tools.find_references(
        query=query,
        domain=domain,
        capability=capability,
        phase=phase,
        persona=persona,
        maturity=maturity,
        persona_primary_only=persona_primary_only,
    )


@_tool("Browse the cloud waste runbooks")
def list_playbooks() -> dict[str, Any]:
    """See every ready-made runbook for finding and fixing cloud waste:
    idle, orphaned and overprovisioned resources, egress surprises,
    schedule blindness and AI/ML inefficiency across AWS, Azure and GCP.

    Use this to discover which waste patterns have a runbook. When the
    question already names a provider, waste category, or confidence tier,
    ``find_playbooks`` returns only the matching runbooks.

    Each playbook is a small (~90-170 line) runbook scoped to one waste
    pattern (e.g. ``aws-zombie-nat-gateway``, ``azure-orphan-disks``). Returns
    ``{"playbooks": [...], "total": N}`` where each entry includes ``name``,
    ``title``, ``scope`` (aws/azure/gcp/cross-cloud), ``service``,
    ``waste_category``, ``confidence`` (obvious/likely/possible), and
    ``approx_tokens`` - the same size hint the reference listing carries, so a
    multi-playbook answer can be budgeted before fetching.
    """
    return _tools.list_playbooks()


@_tool("Read one waste runbook")
def get_playbook(name: str) -> dict[str, Any]:
    """Fetch the step-by-step runbook for one specific waste pattern:
    symptoms, the detection queries to run, the fix, and the anti-pattern
    to avoid.

    Use this when the user asks how to detect, confirm, or fix one specific
    named waste pattern (zombie NAT gateway, snapshot sprawl, idle SageMaker
    endpoint, ...), including questions about the user's own resources
    ("which of my X..."). Each runbook includes a detection query the user
    can run in their own cloud account; this connector has no access to the
    user's accounts.

    Args:
        name: Playbook slug as returned by ``list_playbooks`` (e.g.
            ``"aws-zombie-nat-gateway"``, ``"azure-orphan-disks"``,
            ``"cross-cloud-untagged-spend-drift"``).

    Returns ``{"name": ..., "title": ..., "content": "...", "lines": N}``.
    On miss, returns ``{"error": ..., "suggestions": [...]}`` with up to
    three string-distance matches so the caller can self-correct.
    """
    return _tools.get_playbook(name)


@_tool("Find a waste runbook")
def find_playbooks(
    query: str | None = None,
    scope: str | None = None,
    service: str | None = None,
    waste_category: str | None = None,
    confidence: str | None = None,
) -> dict[str, Any]:
    """Finds runbooks for a suspected cloud-waste pattern, filterable by
    provider, service, waste category or detection confidence. Useful when
    the user asks how to detect or fix a specific waste pattern; each
    runbook includes a detection query the user can run in their own
    account. This connector has no access to the user's accounts.

    Use this with ``query`` for a symptom or a "which of my X" question in
    the user's own words: "our AWS bill has NAT gateway charges but nothing
    uses them", "which of my RIs are about to expire", "my NAT gateway
    processes 10TB to S3", "should I delete these old snapshots", "our Log
    Analytics ingestion doubled", "which VMs are running for nothing",
    "passerelle NAT qui ne sert à rien". Every runbook declares the
    questions it answers (English and French); the result is ranked by
    those, then by title and service, and carries ``matched_question``; the
    first entry is the one ``get_playbook(name=)`` fetches. Facets narrow
    the set first; ``query`` ranks what is left.

    Use this with the facets alone to browse: "what waste can we clean up safely
    without review" (confidence), "every idle pattern on Azure" (scope and
    waste category). Patterns covered include NAT gateways and VPC
    endpoints, expiring Savings Plans / RIs / reservations, snapshot
    sprawl, S3 lifecycle gaps, idle or stopped VMs, orphaned disks / public
    IPs / EBS volumes, GPU and SageMaker sizing, Kubernetes idle capacity,
    and schedule blindness.

    All filters are optional and combine with AND semantics. String matching
    is case-insensitive and exact. Examples:

    - ``find_playbooks(query="which of my RIs are about to expire")`` - ranked runbooks
    - ``find_playbooks(scope="aws")`` - all AWS-specific playbooks
    - ``find_playbooks(waste_category="idle")`` - every idle-resource pattern
    - ``find_playbooks(scope="cross-cloud", confidence="obvious")``

    Args:
        query: the user's symptom or question in their own words, up to
            1,000 characters, English or French. Ranks the facet-filtered runbooks by
            the questions they declare, their title and their service;
            returns at most five, best first, each with ``match_score``
            and ``matched_question`` (a runbook is read whole, so its
            ``suggested_section`` is null).
        scope: ``"aws"``, ``"azure"``, ``"gcp"``, or ``"cross-cloud"``.
        service: Provider service exact-match (e.g. ``"AWS NAT Gateway"``).
        waste_category: ``"orphaned"``, ``"idle"``, ``"overprovisioned"``,
            ``"commitment-mismatch"``, ``"schedule-blindness"``,
            ``"modernization"``, ``"ai-ml-inefficiency"``, or ``"egress"``.
        confidence: ``"obvious"`` (single signal is enough),
            ``"likely"`` (two signals required), or ``"possible"``
            (needs human review). From the OptimNow three-tier confidence
            model in `finops-waste-detection-playbooks`.

    Returns ``{"filters": {...}, "playbooks": [...], "total": N}``. With
    ``query`` the entries are ranked and capped at five. A facet filter that
    matches nothing also returns `hint` and `valid_values`, so a typo is
    distinguishable from a genuine gap in coverage; a ``query`` that matches
    nothing returns `hint` alone.
    """
    return _tools.find_playbooks(
        query=query,
        scope=scope,
        service=service,
        waste_category=waste_category,
        confidence=confidence,
    )


@_tool("Current figures from an OptimToken guide", open_world=True)
async def get_live_figures(guide: str) -> dict[str, Any]:
    """Get the current value of a figure a reference quotes with a date.

    Use this when a reference quotes a figure from an OptimToken guide
    ("measured on the 2026-10-25 OptimToken catalogue") and the answer needs
    the current value: the Compute Savings Plan or reservation discount, the
    gap between a flexible and a locked commitment, the ARM discount against
    Intel and AMD, the share of LLM models with a batch rate. It fetches the
    guide's figures file, rebuilt daily, and returns it as published.

    Args:
        guide: The guide slug, lowercase letters, digits and hyphens. Guides
            with figures today: ``"savings-plans-vs-reserved-instances"``,
            ``"arm-against-x86"``, ``"batch-api-economics"``.

    Returns ``{"document": {...}, "fetched_at": ..., "source": "live" |
    "cached", "note": ...}``, plus ``cache_age_seconds`` when cached (six-hour
    cache). ``document`` is the file unchanged: ``guide``, ``title``,
    ``url``, ``dataSource``, ``snapshotDate`` (the catalogue the figures come
    from), ``dateModified`` and ``figures``, where discounts are fractions
    (0.2743 is 27.4%) and each key names a median, a range or a count.

    An unknown slug returns ``{"error", "available_guides", "suggestions"}``.
    Any other failure (timeout, HTTP error, invalid JSON) returns
    ``{"error", "fallback"}``: the dated figure in the reference then stands,
    quoted with its date.
    """
    # The fetch blocks for up to the 5-second timeout. FastMCP calls a sync
    # tool on the event loop, so on the hosted server a slow OptimToken would
    # stall every other request; a worker thread keeps the loop free.
    return await asyncio.to_thread(_live_figures.get_live_figures, guide)


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
    # The module-level ``mcp`` is constructed with the SDK's default host
    # (127.0.0.1), and the SDK then switches on DNS-rebinding protection with
    # an allow-list of localhost Host headers. Changing ``settings.host`` here
    # does not revisit that choice, so a public deployment answered every
    # request with 421 "Invalid Host header: cloud-finops-mcp.fly.dev"
    # (observed on Fly.io, 2026-09-09; Alpic's ingress had masked it by
    # rewriting Host). Rebinding protection defends a server bound to
    # localhost against a hostile web page; a public host behind a
    # TLS-terminating ingress gains nothing from it, so it is switched off
    # for the HTTP transport only. Stdio is unaffected.
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=False
    )
    await mcp.run_streamable_http_async()


__all__ = [
    "mcp",
    "run",
    "run_http",
    "DEFAULT_HTTP_HOST",
    "DEFAULT_HTTP_PORT",
    "__version__",
]
