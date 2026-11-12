#!/usr/bin/env python3
"""check-hosted-connector.py - does the hosted connector serve this checkout?

Calls the hosted MCP server and compares what it answers with the tree the
script is pointed at:

  1. ``initialize``: ``serverInfo.version`` equals ``version`` in
     ``plugins/cloud-finops/.claude-plugin/plugin.json``.
  2. ``list_references``: ``total`` and the names equal the ``.md`` files under
     ``references/``.
  3. ``list_playbooks``: ``total`` and the names equal the ``.md`` files under
     ``playbooks/`` (``README.md`` left out, as in the bundle).

The version says which image answers; the two listings say what content is in
it. Both are needed: until 1.37.0 the version field named the ``mcp`` library
and stayed put while the content moved, and the August 2026 audits found the
hosted server four releases behind only by calling it (docs/DESIGN.md, "Verify
the surface you measure, by calling it, on content").

Run after each deploy by the ``deploy-hosted`` job of
``auto-tag-on-plugin-bump.yml`` and by ``deploy-hosted.yml``. The MCP Registry
entry, which advertises the hosted URL, is published only once this passes.

It tries several times before failing. The Fly.io machine suspends when idle
and a deploy discards the suspend snapshot, so the first call after a rollout
pays a cold start; an answer from the previous image can also arrive while
the rollout settles.

Usage:
  python scripts/check-hosted-connector.py
  python scripts/check-hosted-connector.py --repo-root release
  python scripts/check-hosted-connector.py --url http://127.0.0.1:8080/mcp

Exit codes: 0 the server serves this checkout; 1 it does not, or it did not
answer; 2 the checkout could not be read.

Standard library only, so it runs on a bare runner. It only reads: three calls,
none of which changes anything on the server.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DEFAULT_URL = "https://mcp.optimnow.io/mcp"
PLUGIN_JSON = Path("plugins/cloud-finops/.claude-plugin/plugin.json")
REFERENCES_DIR = Path("plugins/cloud-finops/skills/cloud-finops/references")
PLAYBOOKS_DIR = Path("plugins/cloud-finops/skills/cloud-finops/playbooks")
# Same exclusion as mcp_server/scripts/sync_references.py: the playbooks README
# documents the format for contributors and is not bundled.
PLAYBOOKS_SKIP = frozenset({"README.md"})

PROTOCOL_VERSION = "2025-06-18"
USER_AGENT = "cloud-finops-skills-deploy-check"

DEFAULT_ATTEMPTS = 8
DEFAULT_DELAY = 15.0
DEFAULT_TIMEOUT = 30.0


class ConnectorError(Exception):
    """The server gave no usable answer to a call."""


class CheckoutError(Exception):
    """The tree to compare against could not be read."""


@dataclass(frozen=True)
class Listing:
    """What one listing tool reports: its ``total`` and the names it lists."""

    total: int
    names: frozenset[str]


@dataclass(frozen=True)
class Catalogue:
    """A version and the two listings, from a checkout or from the server."""

    version: str
    references: Listing
    playbooks: Listing


# --------------------------------------------------------------------------
# What the checkout says the server should serve
# --------------------------------------------------------------------------


def _declared_name(path: Path) -> str:
    """The name the server lists a file under.

    The server uses the frontmatter ``name`` and falls back to the file stem
    (``metadata.py``). Every file has the two equal today; reading the field
    keeps this check right on the day one does not.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CheckoutError(f"cannot read {path}: {exc}") from exc
    if lines and lines[0].strip() == "---":
        for line in lines[1:]:
            if line.strip() == "---":
                break
            if line.startswith("name:"):
                value = line[len("name:") :].strip().strip("\"'")
                if value:
                    return value
    return path.stem


def _names_in(directory: Path, *, skip: frozenset[str] = frozenset()) -> Listing:
    if not directory.is_dir():
        raise CheckoutError(f"{directory} is not a directory")
    names = frozenset(
        _declared_name(path)
        for path in directory.glob("*.md")
        # sync_references.py does not bundle symlinks either.
        if path.name not in skip and not path.is_symlink()
    )
    return Listing(total=len(names), names=names)


def expected_from_checkout(root: Path) -> Catalogue:
    """Read the version and the two catalogues from a checkout of the repository."""
    plugin_json = root / PLUGIN_JSON
    try:
        version = json.loads(plugin_json.read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise CheckoutError(f"cannot read a version from {plugin_json}: {exc}") from exc
    return Catalogue(
        version=str(version),
        references=_names_in(root / REFERENCES_DIR),
        playbooks=_names_in(root / PLAYBOOKS_DIR, skip=PLAYBOOKS_SKIP),
    )


# --------------------------------------------------------------------------
# What the server serves
# --------------------------------------------------------------------------


def _post(url: str, body: bytes, headers: dict[str, str], timeout: float) -> str:
    """One HTTP POST, returning the body as text. The tests replace this."""
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_reply(raw: str, request_id: int) -> dict:
    """Find the JSON-RPC message answering ``request_id`` in a reply body.

    Streamable HTTP answers either with one JSON object or with a server-sent
    event stream whose ``data:`` lines carry the JSON. The hosted server sends
    the stream; a server started with JSON responses sends the object.
    """
    text = raw.strip()
    candidates: list[str] = []
    if text.startswith("{"):
        candidates.append(text)
    else:
        event: list[str] = []
        for line in raw.splitlines() + [""]:
            if line.startswith("data:"):
                event.append(line[len("data:") :].lstrip())
            elif not line.strip() and event:
                candidates.append("\n".join(event))
                event = []
    for candidate in candidates:
        try:
            message = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(message, dict) and message.get("id") == request_id:
            return message
    raise ConnectorError(f"the reply holds no JSON-RPC message for request {request_id}")


def _rpc(url: str, method: str, params: dict, *, request_id: int, timeout: float) -> dict:
    body = json.dumps(
        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
    ).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": USER_AGENT,
    }
    if method != "initialize":
        headers["MCP-Protocol-Version"] = PROTOCOL_VERSION
    label = params.get("name", method)
    try:
        raw = _post(url, body, headers, timeout)
    except urllib.error.HTTPError as exc:
        raise ConnectorError(f"{label}: HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        reason = getattr(exc, "reason", None) or exc
        raise ConnectorError(f"{label}: no answer ({reason})") from exc
    message = parse_reply(raw, request_id)
    if "error" in message:
        raise ConnectorError(f"{label}: the server answered an error: {message['error']}")
    result = message.get("result")
    if not isinstance(result, dict):
        raise ConnectorError(f"{label}: the reply has no result")
    return result


def _listing(url: str, tool: str, key: str, *, request_id: int, timeout: float) -> Listing:
    result = _rpc(
        url,
        "tools/call",
        {"name": tool, "arguments": {}},
        request_id=request_id,
        timeout=timeout,
    )
    if result.get("isError"):
        raise ConnectorError(f"{tool}: the tool returned an error")
    payload = result.get("structuredContent")
    if not isinstance(payload, dict):
        # Older builds returned the listing only as a JSON text block.
        try:
            payload = json.loads(result["content"][0]["text"])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ConnectorError(f"{tool}: the result is not a listing") from exc
    entries = payload.get(key) if isinstance(payload, dict) else None
    total = payload.get("total") if isinstance(payload, dict) else None
    if not isinstance(entries, list) or not isinstance(total, int):
        raise ConnectorError(f"{tool}: the result has no '{key}' list with a 'total'")
    names = frozenset(str(entry.get("name")) for entry in entries if isinstance(entry, dict))
    return Listing(total=total, names=names)


def served_by(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> Catalogue:
    """Ask the server for its version and its two catalogues.

    Each call stands alone: the hosted server runs stateless, so a tool call
    needs no session opened by ``initialize`` first.
    """
    init = _rpc(
        url,
        "initialize",
        {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": "deploy-check", "version": "0"},
        },
        request_id=1,
        timeout=timeout,
    )
    server_info = init.get("serverInfo")
    version = server_info.get("version") if isinstance(server_info, dict) else None
    if not version:
        raise ConnectorError("initialize: the reply has no serverInfo.version")
    return Catalogue(
        version=str(version),
        references=_listing(url, "list_references", "references", request_id=2, timeout=timeout),
        playbooks=_listing(url, "list_playbooks", "playbooks", request_id=3, timeout=timeout),
    )


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------


def _some(names: frozenset[str] | set[str], limit: int = 5) -> str:
    ordered = sorted(names)
    shown = ", ".join(ordered[:limit])
    return shown if len(ordered) <= limit else f"{shown} and {len(ordered) - limit} more"


def _listing_problems(tool: str, expected: Listing, served: Listing) -> list[str]:
    problems: list[str] = []
    if served.total != expected.total:
        problems.append(
            f"{tool} total is {served.total}, the checkout has {expected.total} files"
        )
    if served.total != len(served.names):
        problems.append(f"{tool} total is {served.total} but it lists {len(served.names)} names")
    missing = expected.names - served.names
    extra = served.names - expected.names
    if missing:
        problems.append(f"{tool} does not list {_some(missing)}")
    if extra:
        problems.append(f"{tool} lists {_some(extra)}, absent from the checkout")
    return problems


def differences(expected: Catalogue, served: Catalogue) -> list[str]:
    """Every way the served catalogue differs from the expected one; empty when equal."""
    problems: list[str] = []
    if served.version != expected.version:
        problems.append(
            f"serverInfo.version is {served.version}, plugin.json says {expected.version}"
        )
    problems += _listing_problems("list_references", expected.references, served.references)
    problems += _listing_problems("list_playbooks", expected.playbooks, served.playbooks)
    return problems


def check(
    url: str,
    expected: Catalogue,
    *,
    attempts: int = DEFAULT_ATTEMPTS,
    delay: float = DEFAULT_DELAY,
    timeout: float = DEFAULT_TIMEOUT,
    sleep=time.sleep,
    log=print,
) -> list[str]:
    """Compare until the server matches or the attempts run out.

    Returns the problems seen on the last attempt, empty on a match.
    """
    problems: list[str] = []
    for attempt in range(1, attempts + 1):
        try:
            problems = differences(expected, served_by(url, timeout=timeout))
        except ConnectorError as exc:
            problems = [str(exc)]
        if not problems:
            log(f"attempt {attempt}/{attempts}: the server serves this checkout")
            return []
        log(f"attempt {attempt}/{attempts}: " + "; ".join(problems))
        if attempt < attempts:
            sleep(delay)
    return problems


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def _report(url: str, expected: Catalogue, problems: list[str]) -> None:
    """Annotate the run and write its summary when GitHub Actions is the caller."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        for problem in problems:
            # An annotation is one line; a stray newline would cut it short.
            print(f"::error title=Hosted connector is not on {expected.version}::"
                  + problem.replace("\n", " "))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary:
        return
    verdict = "does not serve" if problems else "serves"
    lines = [
        "### Hosted connector check",
        "",
        f"`{url}` **{verdict}** version {expected.version}, "
        f"{expected.references.total} references and {expected.playbooks.total} playbooks.",
        "",
    ]
    lines += [f"- {problem}" for problem in problems]
    try:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")
    except OSError:
        pass  # The summary is a convenience; the exit code is the result.


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check that the hosted connector serves the version and catalogue of a checkout."
    )
    parser.add_argument("--url", default=DEFAULT_URL, help=f"MCP endpoint (default {DEFAULT_URL})")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="checkout to compare against (default: the one this script is in)",
    )
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help="seconds between attempts")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help="seconds per call")
    args = parser.parse_args(argv)

    try:
        expected = expected_from_checkout(args.repo_root)
    except CheckoutError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 2

    print(
        f"Expecting version {expected.version}, {expected.references.total} references and "
        f"{expected.playbooks.total} playbooks (from {args.repo_root}) at {args.url}"
    )
    problems = check(
        args.url,
        expected,
        attempts=max(1, args.attempts),
        delay=args.delay,
        timeout=args.timeout,
    )
    _report(args.url, expected, problems)
    if problems:
        print(f"FAIL: {args.url} does not serve this checkout:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print(f"OK: {args.url} serves version {expected.version} with the catalogue of this checkout.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
