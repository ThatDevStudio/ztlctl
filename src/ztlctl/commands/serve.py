"""serve — start the MCP server (requires ztlctl[mcp] extra)."""

from __future__ import annotations

import click

from ztlctl.commands._base import ZtlCommand


@click.command(
    cls=ZtlCommand,
    examples="""\
  # Start the MCP server (stdio transport)
  ztlctl serve

  # Specify transport explicitly
  ztlctl serve --transport stdio""",
)
@click.option(
    "--transport",
    default="stdio",
    type=click.Choice(["stdio"]),
    help="MCP transport protocol.",
)
@click.pass_obj
def serve(app: object, transport: str) -> None:
    """Start the MCP server (requires ztlctl[mcp] extra)."""
    from ztlctl.mcp.server import create_server, mcp_available

    if not mcp_available:
        click.echo("MCP not installed. Install with: pip install ztlctl[mcp]", err=True)
        raise SystemExit(1)

    from ztlctl.commands._context import AppContext

    assert isinstance(app, AppContext)
    server = create_server(vault_root=app.settings.vault_root)
    server.run(transport=transport)
