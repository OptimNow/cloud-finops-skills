"""The connector ships no MCP Apps widget, and this keeps it that way.

Until 1.50.0 five tools linked a ``ui://`` resource. In claude.ai that link is
what classified them as ``[third_party_mcp_app]`` tools that "need opt-in"
(read in the host's own tool-search response on 2026-11-10): both finders and
``get_playbook`` sat behind a connector card, while ``get_reference``, the one
content tool without a widget, was called freely. The widgets also never
rendered there, and a model that had fetched a playbook answered "the runbook is
above" without repeating the query.

So a widget link on a tool is a routing regression on the main host, not a
cosmetic addition. Anyone who adds one back should have measured it first; the
record is ``docs/mcp-apps-lessons.md``.
"""

from __future__ import annotations

from pathlib import Path

from cloud_finops_mcp import server

WIDGET_META_KEYS = ("ui", "ui/resourceUri", "openai/outputTemplate")

SEVEN_TOOLS = {
    "list_references",
    "get_reference",
    "find_references",
    "list_playbooks",
    "get_playbook",
    "find_playbooks",
    "get_live_figures",
}


async def test_no_tool_links_a_widget() -> None:
    tools = await server.mcp.list_tools()
    assert {t.name for t in tools} == SEVEN_TOOLS
    for tool in tools:
        meta = tool.meta or {}
        for key in WIDGET_META_KEYS:
            assert key not in meta, f"{tool.name} declares {key}"


async def test_no_ui_resource_is_registered() -> None:
    resources = await server.mcp.list_resources()
    assert not [str(r.uri) for r in resources if str(r.uri).startswith("ui://")]


def test_no_widget_file_ships_in_the_package() -> None:
    package = Path(server.__file__).resolve().parent
    assert not (package / "ui").exists()


def test_tool_descriptions_do_not_promise_a_card() -> None:
    """A description that announces a rendered view invites "see the card above"."""
    import asyncio

    tools = asyncio.run(server.mcp.list_tools())
    for tool in tools:
        text = (tool.description or "").lower()
        for word in ("mcp apps", "ui://", "widget", "interactive explorer", "viewer"):
            assert word not in text, f"{tool.name} description mentions {word!r}"
