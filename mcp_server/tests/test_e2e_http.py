"""End-to-end test over the streamable HTTP transport.

Mirrors the stdio suite in ``test_e2e.py``. The two transports share all of the
tool code, so this is not about re-testing the tools - it is about proving that
``--transport http`` actually serves them, on the route a hosting platform
expects, in stateless mode. A silent divergence between the two transports is
exactly the kind of thing that only surfaces after deployment.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from mcp import ClientSession

# `streamable_http_client`, not the older `streamablehttp_client`: the latter
# is deprecated in 1.29 and emits a DeprecationWarning. Both names exist across
# the whole `mcp>=1.28,<2` range (verified against 1.28.0 and 1.29.0), so
# taking the current one costs no compatibility.
from mcp.client.streamable_http import streamable_http_client

REPO_ROOT = Path(__file__).resolve().parents[2]
SERVER_PKG = "cloud_finops_mcp"
STARTUP_TIMEOUT_S = 30.0


def _free_port() -> int:
    """Ask the OS for an unused port, then release it.

    Racy in principle, fine in practice for a test fixture and far better than
    a hardcoded port that collides with whatever else the CI runner is doing.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_listening(port: int, proc: subprocess.Popen[bytes]) -> None:
    deadline = time.monotonic() + STARTUP_TIMEOUT_S
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(
                f"server exited during startup with code {proc.returncode}"
            )
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise TimeoutError(f"server did not listen on port {port} within {STARTUP_TIMEOUT_S}s")


@pytest.fixture(scope="module")
def http_server_url() -> Iterator[str]:
    """Serve this checkout over streamable HTTP for the duration of the module."""
    port = _free_port()
    src_dir = REPO_ROOT / "mcp_server" / "src"
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = f"{src_dir}{os.pathsep}{existing}" if existing else str(src_dir)
    # Set PORT to something else on purpose: an explicit --port must win over
    # the environment, otherwise a platform-injected PORT would silently
    # override a deliberate command line.
    env["PORT"] = str(port + 1)

    proc = subprocess.Popen(
        [sys.executable, "-m", SERVER_PKG, "--transport", "http",
         "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_until_listening(port, proc)
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)


@pytest.mark.asyncio
async def test_http_lists_tools(http_server_url: str) -> None:
    async with streamable_http_client(http_server_url) as (read, write, _):
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
async def test_http_list_references(
    http_server_url: str, expected_references: int
) -> None:
    async with streamable_http_client(http_server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_references", {})
            assert _payload(result)["total"] == expected_references


@pytest.mark.asyncio
async def test_http_list_playbooks(
    http_server_url: str, expected_playbooks: int
) -> None:
    async with streamable_http_client(http_server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("list_playbooks", {})
            assert _payload(result)["total"] == expected_playbooks


@pytest.mark.asyncio
async def test_http_get_playbook(http_server_url: str) -> None:
    async with streamable_http_client(http_server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_playbook", {"name": "aws-zombie-nat-gateway"}
            )
            payload = _payload(result)
            assert payload["name"] == "aws-zombie-nat-gateway"
            assert "## Detection" in payload["content"]


@pytest.mark.asyncio
async def test_http_serves_the_ui_resource(http_server_url: str) -> None:
    """The MCP Apps resource must survive the transport change.

    It is read from disk at import time and served as a resource, so there is
    no reason for it to differ - which is precisely why an untested assumption
    would go unnoticed until a host asked for it over HTTP.
    """
    async with streamable_http_client(http_server_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            resources = await session.list_resources()
            viewer = next(
                r
                for r in resources.resources
                if str(r.uri) == "ui://cloud-finops/playbook-viewer"
            )
            assert viewer.mimeType == "text/html;profile=mcp-app"

            read_result = await session.read_resource(viewer.uri)
            html = next(c.text for c in read_result.contents if hasattr(c, "text"))
            assert "<!DOCTYPE html>" in html
            assert "ui/initialize" in html

            tools = await session.list_tools()
            get_playbook_tool = next(t for t in tools.tools if t.name == "get_playbook")
            assert (
                get_playbook_tool.meta["ui"]["resourceUri"]
                == "ui://cloud-finops/playbook-viewer"
            )


@pytest.mark.asyncio
async def test_http_is_stateless_across_sessions(http_server_url: str) -> None:
    """Two independent connections both work against the same process.

    ``run_http`` sets ``stateless_http=True``. If that ever regresses, a second
    connection to a server that has torn down the first one's session is where
    it shows up first - and it is the failure mode a load-balanced or
    serverless deployment would hit immediately.
    """
    for _ in range(2):
        async with streamable_http_client(http_server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "find_playbooks", {"scope": "aws", "waste_category": "idle"}
                )
                assert _payload(result)["total"] >= 1


def _payload(result) -> dict:
    """Extract and JSON-decode the structured tool result."""
    if getattr(result, "structuredContent", None):
        return result.structuredContent
    text = next(c.text for c in result.content if hasattr(c, "text"))
    return json.loads(text)
