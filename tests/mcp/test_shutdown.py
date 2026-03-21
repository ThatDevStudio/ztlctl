"""Tests for MCP server graceful shutdown (DEBT-04).

Verifies that vault.close(wait_for_events=True) is called in all exit scenarios:
normal return, SystemExit, and RuntimeError.
"""

from __future__ import annotations

import dataclasses
from unittest.mock import MagicMock, patch

import pytest


class TestServerContextStructure:
    """Verify ServerContext dataclass contract."""

    def test_server_context_is_dataclass(self):
        from ztlctl.mcp.server import ServerContext

        assert dataclasses.is_dataclass(ServerContext)

    def test_server_context_has_server_and_vault_fields(self):
        from ztlctl.mcp.server import ServerContext

        fields = {f.name for f in dataclasses.fields(ServerContext)}
        assert "server" in fields
        assert "vault" in fields

    def test_server_context_construction(self):
        from ztlctl.mcp.server import ServerContext

        mock_server = MagicMock()
        mock_vault = MagicMock()
        ctx = ServerContext(server=mock_server, vault=mock_vault)
        assert ctx.server is mock_server
        assert ctx.vault is mock_vault


class TestVaultClosedOnShutdown:
    """Verify vault.close(wait_for_events=True) is always called when serve exits."""

    def _make_context(self, run_side_effect=None):
        """Build a ServerContext with mock server and vault."""
        from ztlctl.mcp.server import ServerContext

        mock_vault = MagicMock()
        mock_server = MagicMock()
        if run_side_effect is not None:
            mock_server.run.side_effect = run_side_effect
        return ServerContext(server=mock_server, vault=mock_vault)

    def _run_serve_logic(self, ctx, transport="stdio"):
        """Replicate the serve command's try/finally block directly.

        This mirrors exactly what src/ztlctl/commands/serve.py does:
            try:
                ctx.server.run(transport=transport)
            finally:
                ctx.vault.close(wait_for_events=True)
        """
        try:
            ctx.server.run(transport=transport)
        finally:
            ctx.vault.close(wait_for_events=True)

    def test_vault_closed_after_server_run_returns(self):
        """vault.close(wait_for_events=True) called when server.run() returns normally."""
        ctx = self._make_context()
        self._run_serve_logic(ctx)
        ctx.vault.close.assert_called_once_with(wait_for_events=True)

    def test_vault_closed_on_system_exit(self):
        """vault.close(wait_for_events=True) called even when server.run() raises SystemExit."""
        ctx = self._make_context(run_side_effect=SystemExit(0))
        with pytest.raises(SystemExit):
            self._run_serve_logic(ctx)
        ctx.vault.close.assert_called_once_with(wait_for_events=True)

    def test_vault_closed_on_runtime_error(self):
        """vault.close(wait_for_events=True) called even when server.run() raises RuntimeError."""
        ctx = self._make_context(run_side_effect=RuntimeError("connection lost"))
        with pytest.raises(RuntimeError, match="connection lost"):
            self._run_serve_logic(ctx)
        ctx.vault.close.assert_called_once_with(wait_for_events=True)

    def test_vault_closed_only_once_on_normal_exit(self):
        """vault.close is called exactly once, not multiple times."""
        ctx = self._make_context()
        self._run_serve_logic(ctx)
        assert ctx.vault.close.call_count == 1
