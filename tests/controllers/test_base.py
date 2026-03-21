"""Tests for BaseController — vault storage and event dispatch."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from ztlctl.controllers.base import BaseController
from ztlctl.infrastructure.vault import Vault
from ztlctl.plugins.contracts import ActionRejection
from ztlctl.services.result import ServiceResult


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


class TestRunAction:
    """Tests for BaseController._run_action."""

    def _make_ctrl(self) -> BaseController:
        mock_vault = MagicMock()
        mock_vault.plugin_manager = None  # no plugins
        return BaseController(mock_vault)

    def test_run_action_calls_invoke_on_no_rejection(self) -> None:
        """_run_action calls invoke with kwargs when no plugin rejects."""
        ctrl = self._make_ctrl()

        expected = ServiceResult(ok=True, op="test_op")
        invoke = MagicMock(return_value=expected)

        result = ctrl._run_action("test_op", {"key": "val"}, invoke)

        invoke.assert_called_once_with({"key": "val"})
        assert result is expected

    def test_run_action_returns_rejection_on_pre_action_reject(self) -> None:
        """_run_action returns ACTION_REJECTED ServiceResult when plugin rejects."""
        ctrl = self._make_ctrl()

        rejection = ActionRejection(reason="denied", detail={"info": "not allowed"})
        with patch.object(ctrl, "_dispatch_pre_action", return_value=({"key": "val"}, rejection)):
            result = ctrl._run_action("test_op", {"key": "val"}, MagicMock())

        assert result.ok is False
        assert result.op == "test_op"
        assert result.error is not None
        assert result.error.code == "ACTION_REJECTED"
        assert result.error.message == "denied"

    def test_run_action_passes_modified_kwargs_from_plugin(self) -> None:
        """_run_action passes plugin-modified kwargs to invoke."""
        ctrl = self._make_ctrl()

        modified_kwargs = {"key": "modified"}
        with patch.object(ctrl, "_dispatch_pre_action", return_value=(modified_kwargs, None)):
            invoke = MagicMock(return_value=ServiceResult(ok=True, op="test_op"))
            ctrl._run_action("test_op", {"key": "original"}, invoke)

        invoke.assert_called_once_with({"key": "modified"})

    def test_run_action_invoke_not_called_on_rejection(self) -> None:
        """_run_action does not call invoke when plugin rejects the action."""
        ctrl = self._make_ctrl()

        rejection = ActionRejection(reason="blocked")
        invoke = MagicMock()
        with patch.object(ctrl, "_dispatch_pre_action", return_value=({}, rejection)):
            ctrl._run_action("test_op", {}, invoke)

        invoke.assert_not_called()
