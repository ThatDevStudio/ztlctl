"""Tests for UpgradeController — integration tests against a real vault."""

from __future__ import annotations

from ztlctl.controllers.upgrade import UpgradeController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.result import ServiceResult


class TestUpgradeController:
    def test_check_pending_returns_service_result(self, vault: Vault) -> None:
        """UpgradeController.check_pending() returns a ServiceResult."""
        ctrl = UpgradeController(vault)
        result = ctrl.check_pending()
        assert isinstance(result, ServiceResult)
        assert result.ok is True

    def test_check_pending_has_expected_keys(self, vault: Vault) -> None:
        """UpgradeController.check_pending() data contains pending_count, current, head."""
        ctrl = UpgradeController(vault)
        result = ctrl.check_pending()
        assert isinstance(result, ServiceResult)
        assert result.ok is True
        assert "pending_count" in result.data
        assert "current" in result.data
        assert "head" in result.data

    def test_stamp_current_returns_service_result(self, vault: Vault) -> None:
        """UpgradeController.stamp_current() returns a ServiceResult."""
        ctrl = UpgradeController(vault)
        result = ctrl.stamp_current()
        assert isinstance(result, ServiceResult)
        assert result.ok is True

    def test_stamp_current_marks_stamped(self, vault: Vault) -> None:
        """UpgradeController.stamp_current() reports stamped=True in data."""
        ctrl = UpgradeController(vault)
        result = ctrl.stamp_current()
        assert isinstance(result, ServiceResult)
        assert result.ok is True
        assert result.data.get("stamped") is True

    def test_apply_returns_service_result(self, vault: Vault) -> None:
        """UpgradeController.apply() returns a ServiceResult."""
        ctrl = UpgradeController(vault)
        # Stamp first so there's nothing to apply
        ctrl.stamp_current()
        result = ctrl.apply()
        assert isinstance(result, ServiceResult)
        assert result.ok is True
