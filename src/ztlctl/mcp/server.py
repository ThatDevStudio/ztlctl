"""FastMCP server setup.

Optional extra — guarded behind try/except ImportError.
Transport: stdio default (sub-ms latency), streamable HTTP optional.
(DESIGN.md Section 16)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

mcp_available = False
_FastMCP: Any = None

try:
    from mcp.server.fastmcp import FastMCP as _FastMCP  # type: ignore[no-redef,import-not-found]

    mcp_available = True
except ImportError:
    pass

__all__ = ["create_server", "mcp_available"]


def create_server(*, vault_root: Path | None = None) -> Any:
    """Create and configure the MCP server.

    Creates a Vault from *vault_root* (or CWD) and registers all tools,
    resources, and prompts. Returns the FastMCP instance.

    Raises RuntimeError if the mcp extra is not installed.
    """
    if not mcp_available or _FastMCP is None:
        msg = "MCP extra not installed. Install with: pip install ztlctl[mcp]"
        raise RuntimeError(msg)

    from ztlctl.config.settings import ZtlSettings
    from ztlctl.infrastructure.vault import Vault
    from ztlctl.mcp.prompts import register_prompts
    from ztlctl.mcp.resources import register_resources
    from ztlctl.mcp.tools import register_tools

    settings = ZtlSettings.from_cli(vault_root=vault_root)
    vault = Vault(settings)

    server = _FastMCP("ztlctl")

    register_tools(server, vault)
    register_resources(server, vault)
    register_prompts(server, vault)

    return server
