"""FastMCP server setup.

Optional extra — guarded behind try/except ImportError.
Transport: stdio default (sub-ms latency), streamable HTTP optional.
(DESIGN.md Section 16)
"""

from __future__ import annotations

from typing import Any

mcp_available = False
_FastMCP: Any = None

try:
    from mcp.server.fastmcp import FastMCP as _FastMCP  # type: ignore[no-redef,import-not-found]

    mcp_available = True
except ImportError:
    pass

__all__ = ["mcp_available"]


def create_server() -> Any:
    """Create and configure the MCP server.

    Returns the FastMCP instance, or raises if mcp extra is not installed.
    """
    if not mcp_available or _FastMCP is None:
        msg = "MCP extra not installed. Install with: pip install ztlctl[mcp]"
        raise RuntimeError(msg)
    server = _FastMCP("ztlctl")
    # Tool, resource, and prompt registration deferred to MCP feature
    return server
