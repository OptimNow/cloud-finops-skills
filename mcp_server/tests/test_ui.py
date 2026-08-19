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
    assert "<!--BRIDGE-->" not in html
    assert "<!--PLAYBOOK_RENDER-->" not in html
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


async def test_ui_resources_are_registered() -> None:
    resources = await server.mcp.list_resources()
    by_uri = {str(r.uri): r for r in resources}
    for uri in WIDGETS:
        assert uri in by_uri, f"{uri} is not a registered resource"
        assert by_uri[uri].mimeType == "text/html;profile=mcp-app"


async def test_tools_link_their_widgets() -> None:
    tools = await server.mcp.list_tools()
    by_name = {t.name: t for t in tools}
    for tool_name, uri in EXPECTED_TOOL_WIRING.items():
        meta = by_name[tool_name].meta or {}
        assert meta.get("ui", {}).get("resourceUri") == uri, (
            f"{tool_name} does not declare {uri}"
        )
    # get_reference deliberately has no widget: its content is read inside
    # the reference browser via an app-initiated call.
    assert not (by_name["get_reference"].meta or {}).get("ui")
