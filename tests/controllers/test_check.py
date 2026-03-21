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


class TestEventPurgeController:
    """Tests for CheckController.event_purge."""

    def test_event_purge_returns_ok_when_no_dead_letters(self, vault: Vault) -> None:
        """event_purge returns ok=True with count=0 when no dead-letter rows exist."""
        vault.init_event_bus(sync=True)
        ctrl = CheckController(vault)
        result = ctrl.event_purge()
        assert isinstance(result, ServiceResult)
        assert result.ok is True
        assert result.data["purged_count"] == 0

    def test_event_purge_returns_count_of_purged_rows(self, vault: Vault) -> None:
        """event_purge deletes dead-letter rows and returns correct count."""
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import insert

        from ztlctl.infrastructure.database.schema import event_wal

        vault.init_event_bus(sync=True)

        old_date = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()

        with vault.engine.begin() as conn:
            conn.execute(
                insert(event_wal).values(
                    hook_name="post_create",
                    payload="{}",
                    status="dead_letter",
                    retries=3,
                    session_id=None,
                    created=old_date,
                )
            )
            conn.execute(
                insert(event_wal).values(
                    hook_name="post_update",
                    payload="{}",
                    status="dead_letter",
                    retries=3,
                    session_id=None,
                    created=old_date,
                )
            )

        ctrl = CheckController(vault)
        result = ctrl.event_purge(older_than_days=30)
        assert isinstance(result, ServiceResult)
        assert result.ok is True
        assert result.data["purged_count"] == 2
        assert result.data["older_than_days"] == 30

    def test_event_purge_returns_error_when_bus_not_initialized(self, vault: Vault) -> None:
        """event_purge returns ok=False when event bus is not initialized."""
        ctrl = CheckController(vault)
        # vault.event_bus is None (not initialized)
        result = ctrl.event_purge()
        assert isinstance(result, ServiceResult)
        assert result.ok is False
        assert result.error is not None
        assert "not initialized" in result.error.message.lower()
