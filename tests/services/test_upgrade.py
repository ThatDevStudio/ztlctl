"""Tests for UpgradeService — database migration with Alembic."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from sqlalchemy import create_engine

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.upgrade import UpgradeService

# ---------------------------------------------------------------------------
# check_pending()
# ---------------------------------------------------------------------------


class TestCheckPending:
    def test_check_pending_on_fresh_vault(self, vault: Vault) -> None:
        """Freshly initialized vault (stamped at head) has 0 pending."""
        svc = UpgradeService(vault)
        # Stamp so the vault is "freshly initialized" at head
        svc.stamp_current()

        result = svc.check_pending()
        assert result.ok
        assert result.data["pending_count"] == 0
        assert result.data["current"] == result.data["head"]

    def test_check_pending_unstamped_db(self, vault: Vault) -> None:
        """Unstamped vault (tables exist, no alembic_version) shows pending migrations."""
        result = UpgradeService(vault).check_pending()
        assert result.ok
        assert result.data["current"] is None
        assert result.data["pending_count"] > 0

    def test_check_pending_reports_head_revision(self, vault: Vault) -> None:
        """check_pending() always reports the head revision."""
        result = UpgradeService(vault).check_pending()
        assert result.ok
        assert result.data["head"] == "001_baseline"


# ---------------------------------------------------------------------------
# apply()
# ---------------------------------------------------------------------------


class TestApply:
    def test_apply_already_current(self, vault: Vault) -> None:
        """Applying on an up-to-date vault returns 0 applied."""
        svc = UpgradeService(vault)
        # First apply (or stamp) to bring vault to head
        svc.stamp_current()

        result = svc.apply()
        assert result.ok
        assert result.data["applied_count"] == 0
        assert "already up to date" in result.data["message"].lower()

    def test_apply_fresh_db(self, vault: Vault) -> None:
        """Apply on fresh DB succeeds (tables already exist, so it stamps)."""
        svc = UpgradeService(vault)
        result = svc.apply()
        assert result.ok
        assert result.data["applied_count"] > 0

    def test_apply_creates_backup(self, vault: Vault) -> None:
        """Apply creates a backup file."""
        svc = UpgradeService(vault)
        result = svc.apply()
        assert result.ok
        assert "backup_path" in result.data
        assert Path(result.data["backup_path"]).exists()


# ---------------------------------------------------------------------------
# stamp_current()
# ---------------------------------------------------------------------------


class TestStampCurrent:
    def test_stamp_current(self, vault: Vault) -> None:
        """stamp_current() succeeds and reports stamped revision."""
        result = UpgradeService(vault).stamp_current()
        assert result.ok
        assert result.data["stamped"] is True
        assert result.data["current"] is not None


# ---------------------------------------------------------------------------
# _tables_exist()
# ---------------------------------------------------------------------------


class TestTablesExist:
    def test_tables_exist_true(self, vault: Vault) -> None:
        """On a vault with initialized DB, _tables_exist() returns True."""
        svc = UpgradeService(vault)
        assert svc._tables_exist() is True

    def test_tables_exist_false_on_empty_db(self, tmp_path: Path) -> None:
        """On a database with no tables, _tables_exist() returns False."""
        mock_vault = MagicMock()
        mock_vault.engine = create_engine(f"sqlite:///{tmp_path / 'empty.db'}")
        mock_vault.root = tmp_path
        svc = UpgradeService(mock_vault)
        assert svc._tables_exist() is False
