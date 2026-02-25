"""Tests for MCP server creation."""

from __future__ import annotations

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
