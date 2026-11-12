#!/usr/bin/env python3
"""
check-companion-tools.py - Compare the companion connectors' tools, as INSTALLATION.md
lists them, with what the live servers serve.

Why: INSTALLATION.md describes two MCP servers that live in other repositories, the
OptimNow AI Pricing Hub (each tool with its parameters) and the AI ROI Calculator
(tool names). Both lists are copies kept by hand, and nothing in this repository can
see the other two move. On 12 November 2026 the page still listed five pricing tools
while the server, at 0.11.0, served eight, with new parameters on two of the five; it
was found by reading, not by a check (DEPENDENCIES.md, "Known asymmetries").

What it does: reads the two "Companion connector" sections of INSTALLATION.md, asks
each server for its tools over MCP (`initialize`, then `tools/list`, streamable
HTTP), and reports per server the tools on one side only and, for the pricing
server, the parameters on one side only or marked optional on the page and required
on the server (or the reverse). Exit codes:

  0  the page and both servers agree
  1  they differ, a section of the page no longer parses, or a server answered a
     client error at its URL (404, 410: the endpoint moved, which is drift too)
  2  nothing differs, and at least one server could not be read (timeout, dropped
     connection, 429, 5xx): an outage is not a difference

What it never does: edit INSTALLATION.md. A difference is a proposal for the
maintainer, who reads the server's own README and changes the page in a docs PR.

Modes:
  python scripts/check-companion-tools.py                live run, report on stdout
  python scripts/check-companion-tools.py --output f.md  also write the report to a file
  python scripts/check-companion-tools.py --offline      no network: both sections
                                                         parse, the stated tool count
                                                         matches the bullets, and
                                                         DEPENDENCIES.md names the
                                                         URLs asked here (the CI run)
  python scripts/check-companion-tools.py --server pricing   restrict to one server

Standard library only, so the offline run needs no install. A request that times
out, is throttled (429) or fails with a 5xx is retried three times, 2, 5 then 15
seconds apart.

Wired into .github/workflows/companion-tools.yml (weekly, live) and ci.yml (--offline).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLATION_PATH = REPO_ROOT / "INSTALLATION.md"
DEPENDENCIES_PATH = REPO_ROOT / "DEPENDENCIES.md"

EXIT_OK, EXIT_DIFFERS, EXIT_UNREACHABLE = 0, 1, 2

USER_AGENT = "companion-tools-check/1.0"
PROTOCOL_VERSION = "2025-06-18"
TIMEOUT_SECONDS = 30
RETRY_PAUSES = (2, 5, 15)
MAX_PAGES = 20  # of tools/list; a server that pages forever is refused, not followed


@dataclass(frozen=True)
class Server:
    """One companion connector: where the page lists it and where it answers."""

    key: str
    label: str
    heading: str  # the text of its heading in INSTALLATION.md, without the hashes
    url: str  # also named in DEPENDENCIES.md, which the offline run checks
    parameters: bool  # the page lists each tool's parameters, so they are compared


SERVERS = (
    Server(
        key="pricing",
        label="OptimNow AI Pricing Hub",
        heading="Companion connector: OptimNow AI Pricing Hub",
        url="https://optimtoken-mcp.optimnow.io/mcp",
        parameters=True,
    ),
    Server(
        key="roi",
        label="AI ROI Calculator",
        heading="Companion connector: AI ROI Calculator",
        url="https://airoicalculator-mcp.optimnow.io/mcp",
        parameters=False,
    ),
)

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
# A tool bullet: "- `name(param?, param)` - what it does", or "- `name` - ...".
# The " - " after the code span keeps the section's other bullets out ("- Claude
# Code: `claude mcp add ...`.").
TOOL_BULLET_RE = re.compile(r"^- `([a-z][a-z0-9_-]*)(?:\(([^)`]*)\))?` - \S")
PARAMETER_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)(\?)?$")
COUNT_RE = re.compile(r"^\*\*([A-Za-z]+) tools\b")
AS_OF_RE = re.compile(r"as of server (\d+(?:\.\d+)+)")
NUMBER_WORDS = {
    word: number
    for number, word in enumerate(
        "one two three four five six seven eight nine ten eleven twelve thirteen "
        "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split(),
        start=1,
    )
}


class PageError(ValueError):
    """INSTALLATION.md no longer has the shape this script reads."""


class Unreachable(Exception):
    """The server could not be read: an outage, not a difference."""


class Moved(Exception):
    """The server answered, and not as an MCP endpoint at this URL."""


@dataclass
class PageTool:
    name: str
    # parameter name -> True when the page marks it optional ("name?")
    parameters: dict[str, bool] = field(default_factory=dict)


@dataclass
class PageSection:
    tools: list[PageTool]
    stated_count: int | None  # "**Eight tools ...**", None when the line is absent
    as_of_version: str | None  # "as of server 0.11.0", None when not stated


@dataclass
class LiveTool:
    name: str
    # parameter name -> True when the server does not require it
    parameters: dict[str, bool] = field(default_factory=dict)


@dataclass
class LiveServer:
    name: str
    version: str
    tools: list[LiveTool]


# --------------------------------------------------------------------------- the page


def section_lines(text: str, heading: str) -> list[str]:
    """The lines under ``heading``, up to the next heading of its level or above."""
    lines = text.splitlines()
    start = level = None
    for index, line in enumerate(lines):
        match = HEADING_RE.match(line)
        if match and match.group(2).startswith(heading):
            start, level = index + 1, len(match.group(1))
            break
    if start is None:
        raise PageError(f'no heading starts with "{heading}"')
    for index in range(start, len(lines)):
        match = HEADING_RE.match(lines[index])
        if match and len(match.group(1)) <= level:
            return lines[start:index]
    return lines[start:]


def parse_section(text: str, server: Server) -> PageSection:
    """The tools one section lists. Raises :class:`PageError` when it lists none."""
    tools: list[PageTool] = []
    stated = as_of = None
    for line in section_lines(text, server.heading):
        count = COUNT_RE.match(line)
        if count and stated is None:
            stated = NUMBER_WORDS.get(count.group(1).lower())
            if stated is None:
                raise PageError(f'"{count.group(1)} tools" is not a count this script reads')
            version = AS_OF_RE.search(line)
            as_of = version.group(1) if version else None
            continue
        bullet = TOOL_BULLET_RE.match(line)
        if not bullet:
            continue
        tool = PageTool(name=bullet.group(1))
        if bullet.group(2) is not None:
            for raw in bullet.group(2).split(","):
                raw = raw.strip()
                if not raw:
                    continue
                parameter = PARAMETER_RE.match(raw)
                if not parameter:
                    raise PageError(f"`{tool.name}`: `{raw}` is not a parameter name")
                if parameter.group(1) in tool.parameters:
                    raise PageError(f"`{tool.name}` lists `{parameter.group(1)}` twice")
                tool.parameters[parameter.group(1)] = parameter.group(2) == "?"
        if any(tool.name == other.name for other in tools):
            raise PageError(f"`{tool.name}` is listed twice")
        tools.append(tool)
    if not tools:
        raise PageError("the section lists no tool in the form - `name(...)` - text")
    if server.parameters and not any(tool.parameters for tool in tools):
        raise PageError("no tool carries a parameter list any more")
    return PageSection(tools=tools, stated_count=stated, as_of_version=as_of)


def page_problems(section: PageSection) -> list[str]:
    """What is wrong with the section on its own, before any server is asked."""
    if section.stated_count is None:
        return ['the "**<Count> tools ...**" line is missing']
    if section.stated_count != len(section.tools):
        return [
            f"the page says {section.stated_count} tools and lists {len(section.tools)}"
        ]
    return []


# ------------------------------------------------------------------------- the server


def _post(url: str, payload: dict[str, Any], headers: dict[str, str]) -> tuple[dict[str, str], bytes]:
    """One POST, retried on a timeout, a dropped connection, a 429 or a 5xx."""
    request_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": USER_AGENT,
        **headers,
    }
    body = json.dumps(payload).encode("utf-8")
    last = ""
    for attempt in range(len(RETRY_PAUSES) + 1):
        if attempt:
            time.sleep(RETRY_PAUSES[attempt - 1])
        request = urllib.request.Request(url, data=body, headers=request_headers, method="POST")
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                return {k.lower(): v for k, v in response.headers.items()}, response.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 429 or exc.code >= 500:
                last = f"HTTP {exc.code}"
                continue
            raise Moved(f"HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = type(exc).__name__ if not getattr(exc, "reason", None) else str(exc.reason)
    raise Unreachable(last or "no answer")


def decode_rpc(headers: dict[str, str], body: bytes, request_id: int) -> dict[str, Any]:
    """The JSON-RPC answer to ``request_id``, from a JSON body or an event stream."""
    text = body.decode("utf-8", errors="replace")
    candidates: list[Any] = []
    if "text/event-stream" in headers.get("content-type", ""):
        for line in text.splitlines():
            if line.startswith("data:"):
                try:
                    candidates.append(json.loads(line[5:].strip()))
                except ValueError:
                    continue
    else:
        try:
            candidates.append(json.loads(text))
        except ValueError:
            raise Moved("the answer is not JSON") from None
    for message in candidates:
        if isinstance(message, dict) and message.get("id") == request_id:
            if "error" in message:
                error = message["error"]
                detail = error.get("message") if isinstance(error, dict) else error
                raise Moved(f"JSON-RPC error: {detail}")
            if isinstance(message.get("result"), dict):
                return message["result"]
    raise Moved("no JSON-RPC result in the answer")


def fetch_server(url: str) -> LiveServer:
    """Ask one MCP server who it is and which tools it serves.

    Raises :class:`Unreachable` for an outage and :class:`Moved` when something
    answers that is not this MCP endpoint.
    """
    headers, body = _post(
        url,
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "companion-tools-check", "version": "1.0"},
            },
        },
        {},
    )
    init = decode_rpc(headers, body, 1)
    info = init.get("serverInfo") if isinstance(init.get("serverInfo"), dict) else {}
    session: dict[str, str] = {
        "MCP-Protocol-Version": str(init.get("protocolVersion") or PROTOCOL_VERSION)
    }
    if headers.get("mcp-session-id"):
        session["Mcp-Session-Id"] = headers["mcp-session-id"]
    try:
        _post(url, {"jsonrpc": "2.0", "method": "notifications/initialized"}, session)
    except (Moved, Unreachable):
        pass  # a server that ignores the notification still answers tools/list

    tools: list[LiveTool] = []
    cursor: str | None = None
    for page in range(MAX_PAGES):
        payload: dict[str, Any] = {"jsonrpc": "2.0", "id": 2 + page, "method": "tools/list"}
        if cursor:
            payload["params"] = {"cursor": cursor}
        headers, body = _post(url, payload, session)
        result = decode_rpc(headers, body, 2 + page)
        for raw in result.get("tools") or []:
            if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
                continue
            schema = raw.get("inputSchema") if isinstance(raw.get("inputSchema"), dict) else {}
            properties = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
            required = set(schema.get("required") or [])
            tools.append(
                LiveTool(name=raw["name"], parameters={p: p not in required for p in properties})
            )
        cursor = result.get("nextCursor") if isinstance(result.get("nextCursor"), str) else None
        if not cursor:
            break
    else:
        raise Moved(f"tools/list still pages after {MAX_PAGES} pages")
    return LiveServer(
        name=str(info.get("name") or "unnamed server"),
        version=str(info.get("version") or "unknown version"),
        tools=tools,
    )


# ---------------------------------------------------------------------- the comparison


def _names(values: list[str]) -> str:
    return ", ".join(f"`{value}`" for value in sorted(values))


def compare(section: PageSection, live: LiveServer, parameters: bool) -> list[str]:
    """Every difference between the page's list and the server's, as sentences."""
    differences: list[str] = []
    page = {tool.name: tool for tool in section.tools}
    served = {tool.name: tool for tool in live.tools}
    missing = [name for name in served if name not in page]
    extra = [name for name in page if name not in served]
    if missing:
        differences.append(f"On the server, not on the page: {_names(missing)}")
    if extra:
        differences.append(f"On the page, not on the server: {_names(extra)}")
    if not parameters:
        return differences
    for name in sorted(set(page) & set(served)):
        written, actual = page[name].parameters, served[name].parameters
        absent = [p for p in actual if p not in written]
        gone = [p for p in written if p not in actual]
        now_required = [p for p in written if p in actual and written[p] and not actual[p]]
        now_optional = [p for p in written if p in actual and not written[p] and actual[p]]
        if absent:
            differences.append(f"`{name}`: on the server, not on the page: {_names(absent)}")
        if gone:
            differences.append(f"`{name}`: on the page, not on the server: {_names(gone)}")
        if now_required:
            differences.append(
                f"`{name}`: required on the server, marked optional on the page: {_names(now_required)}"
            )
        if now_optional:
            differences.append(
                f"`{name}`: optional on the server, not marked `?` on the page: {_names(now_optional)}"
            )
    return differences


# -------------------------------------------------------------------------- the runs


def run_offline(installation: Path, dependencies: Path, servers: tuple[Server, ...]) -> int:
    """The CI run: the page still has the shape the weekly run reads."""
    text = installation.read_text(encoding="utf-8")
    known_urls = dependencies.read_text(encoding="utf-8") if dependencies.is_file() else None
    failures = 0
    for server in servers:
        try:
            section = parse_section(text, server)
            problems = page_problems(section)
        except PageError as exc:
            problems, section = [str(exc)], None
        if known_urls is not None and server.url not in known_urls:
            problems.append(
                f"{dependencies.name} does not name {server.url}: the URL this script asks "
                "and the one the dependency map gives have parted"
            )
        if problems:
            failures += 1
            for problem in problems:
                print(f"FAIL: {server.label}: {problem}", file=sys.stderr)
        else:
            print(f"OK: {server.label}: {len(section.tools)} tools listed, section parses.")
    return EXIT_DIFFERS if failures else EXIT_OK


def run_live(installation: Path, servers: tuple[Server, ...]) -> tuple[int, str]:
    """The weekly run. Returns the exit code and the markdown report."""
    text = installation.read_text(encoding="utf-8")
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    out = [
        "# Companion connector tools: INSTALLATION.md against the live servers",
        "",
        f"Read on {today} (UTC).",
    ]
    differs = unreachable = False
    for server in servers:
        out += ["", f"## {server.label}", "", f"<{server.url}>", ""]
        try:
            section = parse_section(text, server)
        except PageError as exc:
            differs = True
            out.append(f"**The page could not be read:** {exc}. Nothing was compared.")
            continue
        try:
            live = fetch_server(server.url)
        except Unreachable as exc:
            unreachable = True
            out.append(f"**Not compared:** the server could not be read ({exc}).")
            continue
        except Moved as exc:
            differs = True
            out.append(
                f"**The server did not answer as an MCP endpoint at this URL ({exc}).** "
                "If it moved, the URL in this script and in DEPENDENCIES.md moves with it."
            )
            continue
        differences = page_problems(section) + compare(section, live, server.parameters)
        served = f"`{live.name}` {live.version}, {len(live.tools)} tools"
        if differences:
            differs = True
            out.append(f"**Differs.** Server: {served}. Page: {len(section.tools)} tools.")
            out.append("")
            out += [f"- {difference[0].upper()}{difference[1:]}" for difference in differences]
        else:
            compared = "names, parameters and optional marks" if server.parameters else "names"
            out.append(f"Agrees ({compared}). Server: {served}.")
        if section.as_of_version and section.as_of_version != live.version:
            out += [
                "",
                f"The page says it was read at server {section.as_of_version}; "
                f"the server is at {live.version}.",
            ]
    code = EXIT_DIFFERS if differs else EXIT_UNREACHABLE if unreachable else EXIT_OK
    return code, "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--offline", action="store_true", help="no network: check that the page still parses")
    parser.add_argument("--output", type=Path, help="also write the markdown report to this file")
    parser.add_argument("--server", choices=[s.key for s in SERVERS], help="restrict the run to one server")
    parser.add_argument("--installation", type=Path, default=INSTALLATION_PATH, help=argparse.SUPPRESS)
    parser.add_argument("--dependencies", type=Path, default=DEPENDENCIES_PATH, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    servers = tuple(s for s in SERVERS if args.server in (None, s.key))
    if not args.installation.is_file():
        print(f"FAIL: {args.installation} does not exist.", file=sys.stderr)
        return EXIT_DIFFERS
    if args.offline:
        return run_offline(args.installation, args.dependencies, servers)

    code, report = run_live(args.installation, servers)
    sys.stdout.write(report)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    return code


if __name__ == "__main__":
    sys.exit(main())
