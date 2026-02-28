"""Tests for MCP server creation."""

from __future__ import annotations

from unittest.mock import patch

from ztlctl.mcp.server import mcp_available


class TestServerAvailability:
    """Test MCP server availability detection."""

    def test_mcp_available_is_bool(self):
        assert isinstance(mcp_available, bool)

    def test_create_server_without_mcp_raises(self):
        """If mcp is not installed, create_server raises RuntimeError."""
        if mcp_available:
            # mcp IS installed — skip this test
            return

        import pytest

        from ztlctl.mcp.server import create_server

        with pytest.raises(RuntimeError, match="MCP extra not installed"):
            create_server()

    def test_create_server_initializes_event_bus(self, tmp_path):
        """create_server wires Vault.init_event_bus for parity with CLI path."""
        from ztlctl.mcp.server import create_server

        class DummyFastMCP:
            def __init__(self, *_args, **_kwargs):
                pass

        with (
            patch("ztlctl.mcp.server.mcp_available", True),
            patch("ztlctl.mcp.server._FastMCP", DummyFastMCP),
            patch("ztlctl.infrastructure.vault.Vault.init_event_bus") as init_bus,
            patch("ztlctl.mcp.tools.register_tools"),
            patch("ztlctl.mcp.resources.register_resources"),
            patch("ztlctl.mcp.prompts.register_prompts"),
        ):
            create_server(vault_root=tmp_path)

        init_bus.assert_called_once()
