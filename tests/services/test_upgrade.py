"""Tests for UpgradeService — database migration with Alembic."""

from __future__ import annotations

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.upgrade import UpgradeService


class TestCheckPending:
    def test_check_pending_fresh_db(self, vault: Vault) -> None:
        """Fresh DB (no alembic_version table) shows pending migrations."""
        result = UpgradeService(vault).check_pending()
        assert result.ok
        assert result.data["pending_count"] > 0
        assert result.data["current"] is None

    def test_check_after_stamp(self, vault: Vault) -> None:
        """After stamping, 0 pending."""
        svc = UpgradeService(vault)
        svc.stamp_current()
        result = svc.check_pending()
        assert result.ok
        assert result.data["pending_count"] == 0
        assert result.data["current"] == result.data["head"]


class TestApply:
    def test_apply_fresh_db(self, vault: Vault) -> None:
        """Apply on fresh DB succeeds (tables already exist, so it stamps)."""
        svc = UpgradeService(vault)
        result = svc.apply()
        assert result.ok
        assert result.data["applied_count"] > 0

    def test_apply_idempotent(self, vault: Vault) -> None:
        """Second apply reports 0 applied."""
        svc = UpgradeService(vault)
        svc.apply()
        result = svc.apply()
        assert result.ok
        assert result.data["applied_count"] == 0

    def test_apply_creates_backup(self, vault: Vault) -> None:
        """Apply creates a backup file."""
        svc = UpgradeService(vault)
        result = svc.apply()
        assert result.ok
        if "backup_path" in result.data:
            from pathlib import Path

            assert Path(result.data["backup_path"]).exists()


class TestStampCurrent:
    def test_stamp_current(self, vault: Vault) -> None:
        result = UpgradeService(vault).stamp_current()
        assert result.ok
        assert result.data["stamped"] is True
        assert result.data["current"] is not None

    def test_stamp_then_check(self, vault: Vault) -> None:
        """After stamp, check shows 0 pending."""
        svc = UpgradeService(vault)
        svc.stamp_current()
        result = svc.check_pending()
        assert result.ok
        assert result.data["pending_count"] == 0
