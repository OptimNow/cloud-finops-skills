"""End-to-end test: spawn the MCP server as a subprocess and call its tools.

Validates the MCP wire format using the official Python SDK client.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PKG = "cloud_finops_mcp"


@pytest.fixture
def server_params() -> StdioServerParameters:
    """Launch the server via ``python -m cloud_finops_mcp`` from this checkout."""
    src_dir = REPO_ROOT / "mcp_server" / "src"
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_dir}{os.pathsep}{existing}" if existing else str(src_dir)
    )
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", SERVER_PKG],
        env=env,
    )


@pytest.mark.asyncio
async def test_e2e_lists_tools(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            tool_names = {t.name for t in result.tools}
            assert {
                "list_references",
                "get_reference",
                "find_references",
                "list_playbooks",
                "get_playbook",
                "find_playbooks",
            }.issubset(tool_names)


@pytest.mark.asyncio
async def test_e2e_list_references(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_references", {})
            payload = _payload(result)
            assert payload["total"] == 28


@pytest.mark.asyncio
async def test_e2e_get_reference(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("get_reference", {"name": "finops-aws"})
            payload = _payload(result)
            assert payload["name"] == "finops-aws"
            assert "FinOps on AWS" in payload["content"]


@pytest.mark.asyncio
async def test_e2e_find_references(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "find_references", {"phase": "Optimize", "persona": "Engineering"}
            )
            payload = _payload(result)
            assert payload["total"] >= 1
            for ref in payload["references"]:
                assert "Optimize" in ref["fcp_phases"]


@pytest.mark.asyncio
async def test_e2e_list_playbooks(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_playbooks", {})
            payload = _payload(result)
            assert payload["total"] == 23


@pytest.mark.asyncio
async def test_e2e_get_playbook(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_playbook", {"name": "aws-zombie-nat-gateway"}
            )
            payload = _payload(result)
            assert payload["name"] == "aws-zombie-nat-gateway"
            assert "## Detection" in payload["content"]


@pytest.mark.asyncio
async def test_e2e_find_playbooks(server_params: StdioServerParameters) -> None:
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "find_playbooks", {"scope": "aws", "waste_category": "idle"}
            )
            payload = _payload(result)
            assert payload["total"] >= 1
            for pb in payload["playbooks"]:
                assert pb["scope"] == "aws"
                assert pb["waste_category"] == "idle"


def _payload(result) -> dict:
    """Extract and JSON-decode the structured tool result."""
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    # Fallback for SDK versions that return text-only content.
    text = next(c.text for c in result.content if hasattr(c, "text"))
    return json.loads(text)
