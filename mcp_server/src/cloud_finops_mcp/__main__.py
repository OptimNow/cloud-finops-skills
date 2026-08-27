"""Entry point: ``python -m cloud_finops_mcp`` and ``cloud-finops-mcp`` console script."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from .server import DEFAULT_HTTP_HOST, DEFAULT_HTTP_PORT, run, run_http

logger = logging.getLogger(__name__)


def _env_port() -> int:
    """Read ``$PORT``, falling back to the default when unset or unusable.

    Hosting platforms assign the listening port through this variable. A
    malformed value falls back rather than crashing on boot: a server that
    starts on the wrong port fails its health check with a legible symptom,
    whereas one that refuses to start looks like a build failure.

    Out-of-range values get the same treatment. ``PORT=70000`` and ``PORT=-1``
    parse as integers but blow up at ``bind()`` with an OS-level error that
    reads nothing like "your PORT is wrong", so they are rejected here.
    """
    raw = os.environ.get("PORT")
    if not raw:
        return DEFAULT_HTTP_PORT
    try:
        port = int(raw)
    except ValueError:
        logger.warning(
            "PORT=%r is not an integer; falling back to %d.", raw, DEFAULT_HTTP_PORT
        )
        return DEFAULT_HTTP_PORT
    if not 0 < port < 65536:
        logger.warning(
            "PORT=%r is outside the valid range 1-65535; falling back to %d.",
            raw,
            DEFAULT_HTTP_PORT,
        )
        return DEFAULT_HTTP_PORT
    return port


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cloud-finops-mcp",
        description=(
            "MCP server exposing the OptimNow Cloud FinOps reference library "
            "and named-pattern playbooks."
        ),
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help=(
            "stdio (default) is what a local MCP client spawns. http serves "
            "streamable HTTP on /mcp for a hosted deployment."
        ),
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HTTP_HOST,
        help=f"Interface to bind in http mode (default: {DEFAULT_HTTP_HOST}).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind in http mode. Defaults to $PORT, then 8000.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Synchronous wrapper used by the console-script entry point."""
    args = _parse_args(argv)
    if args.transport == "http":
        port = args.port if args.port is not None else _env_port()
        asyncio.run(run_http(host=args.host, port=port))
    else:
        asyncio.run(run())


if __name__ == "__main__":
    main()
