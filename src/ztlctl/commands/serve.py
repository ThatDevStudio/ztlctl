"""serve — start the MCP server (requires ztlctl[mcp] extra)."""

from __future__ import annotations

import click

from ztlctl.commands._base import ZtlCommand


@click.command(
    cls=ZtlCommand,
    examples="""\
  # Start the MCP server (stdio transport, default)
  ztlctl serve

  # Streamable HTTP on custom host/port
  ztlctl serve --transport streamable-http --host 0.0.0.0 --port 9000

  # SSE transport on default address
  ztlctl serve --transport sse""",
)
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    help="MCP transport protocol.",
)
@click.option("--host", default="127.0.0.1", help="Bind address (HTTP transports only).")
@click.option("--port", default=8000, type=int, help="Listen port (HTTP transports only).")
@click.pass_obj
def serve(app: object, transport: str, host: str, port: int) -> None:
    """Start the MCP server (requires ztlctl[mcp] extra)."""
    from ztlctl.mcp.server import create_server, mcp_available

    if not mcp_available:
        click.echo("MCP not installed. Install with: pip install ztlctl[mcp]", err=True)
        raise SystemExit(1)

    from ztlctl.commands._context import AppContext

    assert isinstance(app, AppContext)
    server = create_server(vault_root=app.settings.vault_root, host=host, port=port)
    server.run(transport=transport)
