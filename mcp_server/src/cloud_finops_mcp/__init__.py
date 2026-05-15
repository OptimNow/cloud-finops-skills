"""Cloud FinOps MCP server.

Exposes the OptimNow Cloud FinOps skill (28 references + 23 named-pattern
playbooks) as queryable tools via the Model Context Protocol.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cloud-finops-mcp")
except PackageNotFoundError:  # pragma: no cover - editable / not installed
    __version__ = "0.0.0+dev"

__all__ = ["__version__"]
