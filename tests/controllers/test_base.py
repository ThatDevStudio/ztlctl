"""Tests for BaseController — vault storage and event dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock

from ztlctl.controllers.base import BaseController
from ztlctl.infrastructure.vault import Vault


class TestBaseController:
    def test_init_stores_vault(self, vault: Vault) -> None:
        """BaseController.__init__ stores vault as _vault."""
        ctrl = BaseController(vault)
        assert ctrl._vault is vault

    def test_dispatch_event_noop_when_no_bus(self, vault: Vault) -> None:
        """_dispatch_event returns None when vault.event_bus is None."""
        mock_vault = MagicMock()
        mock_vault.event_bus = None

        ctrl = BaseController(mock_vault)
        warnings: list[str] = []
        result = ctrl._dispatch_event("test_hook", {"key": "value"}, warnings)

        assert result is None
        assert warnings == []

    def test_dispatch_event_catches_exception_and_appends_warning(self, vault: Vault) -> None:
        """_dispatch_event catches exceptions and appends to warnings list."""
        mock_vault = MagicMock()
        mock_bus = MagicMock()
        mock_bus.dispatch.side_effect = RuntimeError("bus error")
        mock_vault.event_bus = mock_bus

        ctrl = BaseController(mock_vault)
        warnings: list[str] = []
        result = ctrl._dispatch_event("test_hook", {}, warnings)

        assert result is None
        assert len(warnings) == 1
        assert "test_hook" in warnings[0]

    def test_dispatch_event_returns_result_on_success(self, vault: Vault) -> None:
        """_dispatch_event returns the bus dispatch result on success."""
        mock_vault = MagicMock()
        mock_bus = MagicMock()
        mock_bus.dispatch.return_value = 42
        mock_vault.event_bus = mock_bus

        ctrl = BaseController(mock_vault)
        warnings: list[str] = []
        result = ctrl._dispatch_event("test_hook", {"data": 1}, warnings)

        assert result == 42
        assert warnings == []
