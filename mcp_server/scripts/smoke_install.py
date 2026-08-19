#!/usr/bin/env python
"""Clean-install smoke test for the ``cloud-finops-mcp`` console script.

Reproduces what a first-time user experiences: the package is freshly installed
(fresh dependency resolution, no lockfile) and the ``cloud-finops-mcp`` binary
is launched. This catches the failure mode the unit tests miss - an upstream
dependency shipping a breaking change (e.g. the ``mcp`` SDK 2.0.0 removing
``mcp.server.fastmcp``) while our own code is unchanged.

Run it with the interpreter of the environment where the package is installed,
so the console script sits next to ``sys.executable``::

    python smoke_install.py

Two phases:

1. **Liveness** - launch the binary, hold stdin open, and assert it is still
   running after ``LIVENESS_SECONDS`` with no traceback on stderr. A stdio MCP
   server is silent and long-lived; an early exit or a stderr traceback is a
   failure.
2. **MCP round-trip** - use the official ``mcp`` SDK stdio client to
   ``initialize`` the server and ``list_tools``, asserting the expected tools
   are present.

Exit code 0 = pass. Any failure prints a loud, actionable message (plus a
GitHub Actions ``::error::`` annotation) and exits 1.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from pathlib import Path
from shutil import which

LIVENESS_SECONDS = 5
ROUNDTRIP_TIMEOUT = 30
# Floor for the bundled content, deliberately set well below the real counts so
# it does not need bumping on every content PR. It exists to catch a wheel built
# with an empty or partial data bundle, not to pin exact numbers: a wheel that
# ships zero content starts cleanly and answers every tool call with an empty
# list, which phases 1 and 2 cannot tell apart from a healthy server.
MIN_REFERENCES = 20
MIN_PLAYBOOKS = 20
EXPECTED_TOOLS = {
    "list_references",
    "get_reference",
    "find_references",
    "list_playbooks",
    "get_playbook",
    "find_playbooks",
}


def _fail(msg: str) -> None:
    """Print a loud, readable failure and exit non-zero."""
    print("\n" + "=" * 72, file=sys.stderr)
    print("SMOKE TEST FAILED", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(msg, file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    # GitHub Actions annotation - surfaces at the top of the run summary.
    print(f"::error::cloud-finops-mcp smoke test failed: {msg.splitlines()[0]}")
    sys.exit(1)


def _console_script() -> str:
    """Locate the installed ``cloud-finops-mcp`` console script for this Python."""
    bindir = Path(sys.executable).parent
    for name in ("cloud-finops-mcp", "cloud-finops-mcp.exe"):
        candidate = bindir / name
        if candidate.exists():
            return str(candidate)
    found = which("cloud-finops-mcp")
    if found:
        return found
    _fail(
        "Could not find the 'cloud-finops-mcp' console script.\n"
        f"Looked in {bindir} and on PATH. Is the package installed in this "
        "environment? Check the 'pip install' step above."
    )
    raise SystemExit(1)  # unreachable; _fail already exits


def phase1_liveness(cmd: str) -> None:
    """Launch the binary and assert it stays alive and silent on stderr."""
    print(f"[phase 1] launching '{cmd}' - expecting a silent, long-lived stdio server")
    # Keep stdin as a pipe we never close, so the server does not receive EOF
    # and exit. Capture stderr; discard stdout.
    proc = subprocess.Popen(
        [cmd],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    time.sleep(LIVENESS_SECONDS)

    rc = proc.poll()
    if rc is not None:
        # Exited early = crashed at startup. This is exactly the mcp 2.0.0 case.
        err = b""
        if proc.stderr is not None:
            err = proc.stderr.read() or b""
        _fail(
            f"The server exited {LIVENESS_SECONDS}s after launch with exit code "
            f"{rc}, but a stdio MCP server must stay running.\n"
            "This usually means the binary crashed at startup - most often "
            "because a dependency published a breaking change.\n"
            "Check the resolved 'mcp' / 'pyyaml' versions logged above against "
            "the constraints in mcp_server/pyproject.toml.\n"
            "----- server stderr -----\n" + err.decode("utf-8", "replace")
        )

    # Still alive: stop it and inspect what it wrote to stderr during startup.
    proc.terminate()
    try:
        _, err = proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        _, err = proc.communicate()
    text = (err or b"").decode("utf-8", "replace")
    if text.strip():
        # A clean bare launch is silent. Print anything it wrote for diagnosis,
        # but only fail on an actual traceback/error (a benign warning must not
        # break the build).
        print("[phase 1] note: server wrote to stderr during startup:")
        print(text)
        if "Traceback" in text or "Error" in text:
            _fail(
                "The server stayed alive but wrote an error/traceback to stderr "
                "during startup (see above)."
            )
    print(f"[phase 1] OK - alive after {LIVENESS_SECONDS}s, no traceback on stderr")


async def _roundtrip(cmd: str) -> set[str]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=cmd, args=[])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.list_tools()
            return {t.name for t in result.tools}


def _parse_total(payload: str, tool: str) -> int:
    """Pull ``total`` out of a tool result, whatever shape the SDK returns."""
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        _fail(
            f"{tool} did not return JSON. Got:\n{payload[:500]}"
        )
        raise SystemExit(1)  # unreachable
    if not isinstance(data, dict) or "total" not in data:
        _fail(f"{tool} returned no 'total' field. Got keys: {list(data)[:10]}")
    return int(data["total"])


async def _content_counts(cmd: str) -> dict[str, int]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    params = StdioServerParameters(command=cmd, args=[])
    counts: dict[str, int] = {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for tool in ("list_references", "list_playbooks"):
                result = await session.call_tool(tool, {})
                text = "".join(
                    block.text for block in result.content if getattr(block, "text", None)
                )
                counts[tool] = _parse_total(text, tool)
    return counts


def phase2_roundtrip(cmd: str) -> None:
    """Do a minimal MCP handshake via the official SDK stdio client."""
    print("[phase 2] MCP initialize + list_tools round-trip via the mcp SDK client")
    try:
        names = asyncio.run(asyncio.wait_for(_roundtrip(cmd), timeout=ROUNDTRIP_TIMEOUT))
    except asyncio.TimeoutError:
        _fail(
            f"The MCP handshake did not complete within {ROUNDTRIP_TIMEOUT}s. "
            "The server started but is not responding to 'initialize' - it may "
            "be hanging on import or on transport setup."
        )
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - any failure is a test failure
        import traceback

        _fail(
            "The MCP handshake raised an exception - the server likely crashed "
            "when the client connected:\n"
            f"{type(exc).__name__}: {exc}\n"
            "----- traceback -----\n" + traceback.format_exc()
        )

    missing = EXPECTED_TOOLS - names
    if missing:
        _fail(
            "MCP initialize succeeded but the server did not expose the expected "
            f"tools. Missing: {sorted(missing)}. Got: {sorted(names)}."
        )
    print(f"[phase 2] OK - MCP initialize + list_tools returned {len(names)} tools")


def phase3_content(cmd: str) -> None:
    """Assert the wheel actually carries its content bundle.

    Phases 1 and 2 pass identically on a wheel whose data/ directory is empty:
    the server starts, speaks MCP, and lists all six tools. Only calling a tool
    and counting the results distinguishes a working package from a hollow one.
    """
    print("[phase 3] calling list_references / list_playbooks to verify the data bundle")
    try:
        counts = asyncio.run(
            asyncio.wait_for(_content_counts(cmd), timeout=ROUNDTRIP_TIMEOUT)
        )
    except asyncio.TimeoutError:
        _fail(f"Content tool calls did not complete within {ROUNDTRIP_TIMEOUT}s.")
    except SystemExit:
        raise
    except BaseException as exc:  # noqa: BLE001 - any failure is a test failure
        import traceback

        _fail(
            "Calling a content tool raised an exception:\n"
            f"{type(exc).__name__}: {exc}\n"
            "----- traceback -----\n" + traceback.format_exc()
        )

    problems = []
    for tool, floor in (
        ("list_references", MIN_REFERENCES),
        ("list_playbooks", MIN_PLAYBOOKS),
    ):
        got = counts.get(tool, 0)
        print(f"[phase 3] {tool} -> total={got} (floor {floor})")
        if got < floor:
            problems.append(f"{tool} returned {got}, expected at least {floor}")
    if problems:
        _fail(
            "The server starts and speaks MCP but is serving an empty or partial "
            "content bundle:\n  - "
            + "\n  - ".join(problems)
            + "\nThis means the wheel was built without running "
            "scripts/sync_references.py, or the hatch-build-scripts hook did not "
            "fire. The package is installable and starts cleanly, so nothing else "
            "in the pipeline catches this."
        )
    print("[phase 3] OK - content bundle present")


def main() -> None:
    cmd = _console_script()
    print(f"cloud-finops-mcp smoke test - interpreter:    {sys.executable}")
    print(f"cloud-finops-mcp smoke test - console script: {cmd}")
    phase1_liveness(cmd)
    phase2_roundtrip(cmd)
    phase3_content(cmd)
    print("\nSMOKE TEST PASSED - clean install starts, speaks MCP, and serves content.")


if __name__ == "__main__":
    main()
