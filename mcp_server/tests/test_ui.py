"""Conformance tests for the MCP Apps widgets.

These lock the non-negotiable widget constraints: self-contained HTML (the
host sandbox blocks every external fetch), the shared bridge inlined by
``server._load_ui`` (never hand-pasted), theme via CSS custom properties
with a dark block, the four UI states, and the tool->resource wiring.

What they cannot lock is actual rendering in a real host - that requires
the hosted connector and stays a manual checklist item (see the repo's
CLAUDE.md release checklist).
"""

from __future__ import annotations

import re

import pytest

from cloud_finops_mcp import server

WIDGETS = {
    server.PLAYBOOK_VIEWER_URI: server._PLAYBOOK_VIEWER_HTML,
    server.PLAYBOOK_EXPLORER_URI: server._PLAYBOOK_EXPLORER_HTML,
    server.REFERENCE_BROWSER_URI: server._REFERENCE_BROWSER_HTML,
}

EXPECTED_TOOL_WIRING = {
    "get_playbook": server.PLAYBOOK_VIEWER_URI,
    "list_playbooks": server.PLAYBOOK_EXPLORER_URI,
    "find_playbooks": server.PLAYBOOK_EXPLORER_URI,
    "list_references": server.REFERENCE_BROWSER_URI,
    "find_references": server.REFERENCE_BROWSER_URI,
}


@pytest.mark.parametrize("uri", sorted(WIDGETS))
def test_widget_is_selfcontained(uri: str) -> None:
    """No external fetch can succeed inside the host sandbox."""
    html = WIDGETS[uri]
    assert "<!DOCTYPE html>" in html
    # Markers must have been replaced by the inliner, not shipped raw.
    for marker, _asset, _tag in server._UI_MARKERS:
        assert marker not in html, f"{uri} still carries the raw {marker} marker"
    # No element may load anything over the network.
    for pattern in (
        r'<link\b',
        r'src\s*=\s*["\']https?:',
        r'@import\b',
        r'url\(\s*["\']?https?:',
    ):
        assert not re.search(pattern, html, re.IGNORECASE), (
            f"{uri} references an external resource ({pattern})"
        )


@pytest.mark.parametrize("uri", sorted(WIDGETS))
def test_widget_carries_the_shared_bridge(uri: str) -> None:
    html = WIDGETS[uri]
    assert "ui/initialize" in html
    assert "McpBridge" in html
    assert "PlaybookRender" in html


@pytest.mark.parametrize("uri", sorted(WIDGETS))
def test_widget_theme_uses_custom_properties(uri: str) -> None:
    """Colours live in :root custom properties with a dark override block.

    The OptimNow accent is a variable so no widget hardcodes it in markup.
    """
    html = WIDGETS[uri]
    assert "--accent: #ACE849" in html
    assert "prefers-color-scheme: dark" in html
    assert "color-scheme: light dark" in html


@pytest.mark.parametrize(
    ("uri", "needles"),
    [
        (
            server.PLAYBOOK_EXPLORER_URI,
            ["state-loading", "state-error", "state-empty", "coverage gap"],
        ),
        (
            server.REFERENCE_BROWSER_URI,
            ["state-loading", "state-error", "state-empty"],
        ),
        (
            server.PLAYBOOK_VIEWER_URI,
            ["empty-state", "No playbook loaded"],
        ),
    ],
)
def test_widget_declares_its_states(uri: str, needles: list[str]) -> None:
    """Loading / data / empty / error - a mute empty state is a bug."""
    html = WIDGETS[uri]
    for needle in needles:
        assert needle in html, f"{uri} is missing its '{needle}' state"


def test_viewer_v2_enhancements_present() -> None:
    html = WIDGETS[server.PLAYBOOK_VIEWER_URI]
    assert "copy-btn" in html          # Copy button on code blocks
    assert "checklistFix" in html      # Fix section as a checklist
    assert "enhanceSeeAlso" in html    # clickable playbooks/<slug>.md links
    # The clipboard fallback must exist: the sandbox may deny the API.
    assert "execCommand" in html


@pytest.mark.parametrize("uri", sorted(WIDGETS))
def test_widget_branding_is_discreet(uri: str) -> None:
    """One small OptimNow link, no protocol jargon stamped on every render."""
    html = WIDGETS[uri]
    assert "brand-note" in html
    assert "optimnow.io" in html
    assert "rendered via MCP Apps" not in html
    assert "SEP-1865" not in html.split("</head>", 1)[1].split("<script>", 1)[0], (
        f"{uri} shows protocol jargon in its visible markup"
    )


async def test_ui_resources_are_registered() -> None:
    resources = await server.mcp.list_resources()
    by_uri = {str(r.uri): r for r in resources}
    for uri in WIDGETS:
        assert uri in by_uri, f"{uri} is not a registered resource"
        assert by_uri[uri].mimeType == "text/html;profile=mcp-app"
        # Skybridge parity: every widget also ships an apps-sdk variant
        # (the shape the connectors that DO render in Claude expose).
        variant = server._apps_sdk_uri(uri)
        assert variant in by_uri, f"{variant} is not a registered resource"
        assert by_uri[variant].mimeType == "text/html+skybridge"


async def test_tools_link_their_widgets() -> None:
    tools = await server.mcp.list_tools()
    by_name = {t.name: t for t in tools}
    for tool_name, uri in EXPECTED_TOOL_WIRING.items():
        meta = by_name[tool_name].meta or {}
        # Declared under every key shape hosts read (SEP-1865 nested, flat
        # slash form, OpenAI Apps SDK form) - see server._ui_tool_meta.
        assert meta.get("ui", {}).get("resourceUri") == uri, (
            f"{tool_name} does not declare {uri}"
        )
        assert meta.get("ui/resourceUri") == uri
        # openai/outputTemplate points at the apps-sdk variant (Skybridge
        # parity): the SEP-1865 keys keep the spec resource.
        assert meta.get("openai/outputTemplate") == server._apps_sdk_uri(uri)
    # get_reference deliberately has no widget: its content is read inside
    # the reference browser via an app-initiated call.
    assert not (by_name["get_reference"].meta or {}).get("ui")


def test_ui_domain_is_derived_from_the_canonical_connector_url() -> None:
    """The sandbox-domain hash must follow the URL constant, never drift.

    The claude host validates sha256(<connector URL as entered, no trailing
    slash>)[:32] + ".claudemcpcontent.com" against the resource meta; a
    pasted hash that stops matching the URL is the ai-pricing-hub failure
    mode.
    """
    import hashlib

    assert not server.CANONICAL_CONNECTOR_URL.endswith("/"), (
        "the connector URL is hashed as entered - no trailing slash"
    )
    expected = (
        hashlib.sha256(server.CANONICAL_CONNECTOR_URL.encode("utf-8")).hexdigest()[:32]
        + ".claudemcpcontent.com"
    )
    assert server.UI_DOMAIN == expected


async def test_ui_resources_declare_the_sandbox_domain() -> None:
    """Without ui.domain the host kills the iframe after reserving it."""
    resources = await server.mcp.list_resources()
    checked = 0
    variants = {server._apps_sdk_uri(u) for u in WIDGETS}
    for r in resources:
        meta = r.meta or {}
        if str(r.uri) in WIDGETS:
            ui = meta.get("ui", {})
            assert ui.get("domain") == server.UI_DOMAIN, (
                f"{r.uri} does not declare ui.domain"
            )
            # Skybridge parity: the csp block the rendering connectors send.
            assert ui.get("csp", {}).get("resourceDomains") == [
                server.CANONICAL_CONNECTOR_ORIGIN
            ]
            assert ui.get("csp", {}).get("connectDomains") == [
                server.CANONICAL_CONNECTOR_ORIGIN
            ]
            checked += 1
        elif str(r.uri) in variants:
            assert meta.get("openai/widgetDomain") == server.UI_DOMAIN, (
                f"{r.uri} does not declare openai/widgetDomain"
            )
            assert "openai/widgetCSP" in meta
            checked += 1
    assert checked == len(WIDGETS) * 2
