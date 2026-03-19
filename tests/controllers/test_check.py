"""Tests for CheckController — integration tests against a real vault."""

from __future__ import annotations

from ztlctl.controllers.check import CheckController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.result import ServiceResult


class TestCheckController:
    def test_check_returns_service_result(self, vault: Vault) -> None:
        """CheckController.check() returns a ServiceResult."""
        ctrl = CheckController(vault)
        result = ctrl.check()
        assert isinstance(result, ServiceResult)

    def test_check_ok_on_empty_vault(self, vault: Vault) -> None:
        """CheckController.check() returns ok=True on a healthy empty vault."""
        ctrl = CheckController(vault)
        result = ctrl.check()
        assert result.ok is True
        assert result.data["healthy"] is True
        assert result.data["error_count"] == 0

    def test_check_accepts_min_severity(self, vault: Vault) -> None:
        """CheckController.check() accepts and passes through min_severity."""
        ctrl = CheckController(vault)
        result = ctrl.check(min_severity="error")
        assert isinstance(result, ServiceResult)
        assert result.ok is True

    def test_rebuild_returns_service_result(self, vault: Vault) -> None:
        """CheckController.rebuild() returns a ServiceResult."""
        ctrl = CheckController(vault)
        result = ctrl.rebuild()
        assert isinstance(result, ServiceResult)
        assert result.ok is True

    def test_rebuild_reports_nodes_indexed(self, vault: Vault) -> None:
        """CheckController.rebuild() reports nodes_indexed in data."""
        ctrl = CheckController(vault)
        result = ctrl.rebuild()
        assert isinstance(result, ServiceResult)
        assert "nodes_indexed" in result.data

    def test_fix_returns_service_result(self, vault: Vault) -> None:
        """CheckController.fix() returns a ServiceResult."""
        ctrl = CheckController(vault)
        result = ctrl.fix()
        assert isinstance(result, ServiceResult)
        assert result.ok is True

    def test_rollback_returns_service_result_on_no_backup(self, vault: Vault) -> None:
        """CheckController.rollback() returns a ServiceResult (ok=False when no backups)."""
        ctrl = CheckController(vault)
        result = ctrl.rollback()
        assert isinstance(result, ServiceResult)
        # No backups exist yet — rollback should fail gracefully
        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "NO_BACKUPS"
