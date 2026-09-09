"""Prefect Horizon entrypoint for the hosted `cloud-finops-mcp` connector.

Horizon runs FastMCP 2.x-or-later server objects from the `fastmcp` package.
`cloud-finops-mcp` is written against the official `mcp` SDK's FastMCP
(``mcp.server.fastmcp``), which Horizon does not load directly. This file
bridges the two: it builds a `fastmcp` proxy server that spawns the published
`cloud-finops-mcp` console script over stdio and relays every tool, resource
and prompt call unchanged (tool results and `_meta` pass through untouched).

The package is installed from PyPI at the version pinned in `requirements.txt`,
so the content served here is exactly the released bundle - the same rule as
every other distribution channel. Bump the pin in the release PR.

Entrypoint for Horizon: ``horizon_server.py:mcp``.
Local check: ``fastmcp run horizon_server.py:mcp --transport http --port 8765``.
"""

from __future__ import annotations

import sys

from fastmcp import FastMCP

# Spawn the package through the interpreter that runs this proxy, not through a
# bare `cloud-finops-mcp` on PATH: on a machine with several installs the bare
# name resolved to an older one (33 references instead of 35) during the local
# check on 2026-09-09.
BACKEND = {
    "mcpServers": {
        "cloud-finops": {
            "command": sys.executable,
            "args": ["-m", "cloud_finops_mcp"],
        }
    }
}


def _build() -> FastMCP:
    try:  # fastmcp >= 4 exposes a module-level factory
        from fastmcp.server import create_proxy  # type: ignore[attr-defined]

        return create_proxy(BACKEND, name="cloud-finops")
    except ImportError:  # fastmcp 2.x / 3.x
        return FastMCP.as_proxy(BACKEND, name="cloud-finops")


mcp = _build()
