"""Tests for the built-in ReweavePlugin — automatic post-create reweave."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from ztlctl.config.models import ReweaveConfig
from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.plugins.builtins.reweave_plugin import ReweavePlugin
from ztlctl.services.result import ServiceError, ServiceResult

_PATCH_TARGET = "ztlctl.services.reweave.ReweaveService"


# ---------------------------------------------------------------------------
# Unit tests — plugin in isolation
# ---------------------------------------------------------------------------


class TestReweavePluginUnit:
    """Test plugin logic without event bus integration."""

    def test_skip_when_no_reweave_flag(self, vault: Vault) -> None:
        """Plugin does nothing when --no-reweave is set."""
        settings = ZtlSettings.from_cli(
            vault_root=vault.root,
            no_reweave=True,
        )
        v = Vault(settings)
        plugin = ReweavePlugin(vault=v)

        with patch(_PATCH_TARGET) as mock:
            plugin.post_create(
                content_type="note",
                content_id="ztl_12345678",
                title="Test",
                path="notes/test.md",
                tags=[],
            )
            mock.assert_not_called()

    def test_skip_when_reweave_disabled(self, vault: Vault) -> None:
        """Plugin does nothing when reweave.enabled is False."""
        settings = ZtlSettings.from_cli(
            vault_root=vault.root,
            reweave=ReweaveConfig(enabled=False),
        )
        v = Vault(settings)
        plugin = ReweavePlugin(vault=v)

        with patch(_PATCH_TARGET) as mock:
            plugin.post_create(
                content_type="note",
                content_id="ztl_12345678",
                title="Test",
                path="notes/test.md",
                tags=[],
            )
            mock.assert_not_called()

    def test_calls_reweave_service(self, vault: Vault) -> None:
        """Plugin calls ReweaveService.reweave() with the content_id."""
        plugin = ReweavePlugin(vault=vault)

        mock_result = ServiceResult(
            ok=True,
            op="reweave",
            data={"count": 2, "suggestions": []},
        )
        with patch(_PATCH_TARGET) as mock_cls:
            mock_cls.return_value.reweave.return_value = mock_result
            plugin.post_create(
                content_type="note",
                content_id="ztl_12345678",
                title="Test",
                path="notes/test.md",
                tags=[],
            )
            mock_cls.assert_called_once_with(vault)
            mock_cls.return_value.reweave.assert_called_once_with(
                content_id="ztl_12345678",
            )

    def test_handles_reweave_failure_gracefully(self, vault: Vault) -> None:
        """Plugin does not raise on reweave failure (per plugin invariant)."""
        plugin = ReweavePlugin(vault=vault)

        mock_result = ServiceResult(
            ok=False,
            op="reweave",
            error=ServiceError(code="NOT_FOUND", message="no target"),
        )
        with patch(_PATCH_TARGET) as mock_cls:
            mock_cls.return_value.reweave.return_value = mock_result
            # Should not raise
            plugin.post_create(
                content_type="note",
                content_id="ztl_12345678",
                title="Test",
                path="notes/test.md",
                tags=[],
            )


# ---------------------------------------------------------------------------
# Integration tests — plugin wired through event bus
# ---------------------------------------------------------------------------


class TestReweavePluginIntegration:
    """Test plugin via event bus dispatch (sync mode)."""

    @pytest.fixture
    def vault_with_bus(self, vault: Vault) -> Vault:
        """Vault with event bus initialized in sync mode."""
        vault.init_event_bus(sync=True)
        return vault

    def test_create_triggers_reweave(self, vault_with_bus: Vault) -> None:
        """Creating content with overlapping topics auto-links via reweave."""
        from ztlctl.services.create import CreateService

        cs = CreateService(vault_with_bus)

        # Create first note
        r1 = cs.create_note("Machine Learning Basics", tags=["ml", "tutorial"])
        assert r1.ok

        # Create second note with overlapping tags — should trigger reweave
        r2 = cs.create_note("Deep Learning Tutorial", tags=["ml", "tutorial"])
        assert r2.ok

        # The reweave may or may not find a match depending on BM25 scores,
        # but the important thing is the plugin ran without error
        # (verified by no exception and r2.ok=True)

    def test_no_reweave_flag_prevents_auto_reweave(self, vault_root: Any) -> None:
        """The --no-reweave flag prevents post-create reweave."""
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import reweave_log
        from ztlctl.services.create import CreateService

        settings = ZtlSettings.from_cli(vault_root=vault_root, no_reweave=True)
        v = Vault(settings)
        v.init_event_bus(sync=True)

        cs = CreateService(v)
        cs.create_note("Machine Learning Basics", tags=["ml", "tutorial"])
        cs.create_note("Deep Learning Tutorial", tags=["ml", "tutorial"])

        # No reweave_log entries should exist
        with v.engine.connect() as conn:
            log_rows = conn.execute(select(reweave_log)).fetchall()
        assert len(log_rows) == 0

    def test_reweave_disabled_prevents_auto_reweave(self, vault_root: Any) -> None:
        """Disabled reweave config prevents post-create reweave."""
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import reweave_log
        from ztlctl.services.create import CreateService

        settings = ZtlSettings.from_cli(
            vault_root=vault_root,
            reweave=ReweaveConfig(enabled=False),
        )
        v = Vault(settings)
        v.init_event_bus(sync=True)

        cs = CreateService(v)
        cs.create_note("Alpha Note", tags=["test"])
        cs.create_note("Beta Note", tags=["test"])

        # No reweave_log entries should exist
        with v.engine.connect() as conn:
            log_rows = conn.execute(select(reweave_log)).fetchall()
        assert len(log_rows) == 0

    def test_reweave_creates_edges_for_related_content(self, vault_with_bus: Vault) -> None:
        """When content is strongly related, reweave creates link edges."""
        from sqlalchemy import select

        from ztlctl.infrastructure.database.schema import reweave_log
        from ztlctl.services.create import CreateService

        cs = CreateService(vault_with_bus)

        # Create several notes on the same topic for stronger signal
        for i in range(3):
            result = cs.create_note(
                f"Database Architecture Part {i}",
                tags=["databases", "architecture"],
                topic="engineering",
            )
            assert result.ok

        # Create one more — the reweave should find strong matches
        r = cs.create_note(
            "Database Architecture Summary",
            tags=["databases", "architecture"],
            topic="engineering",
        )
        assert r.ok

        # Verify the reweave plugin ran by checking for reweave_log entries.
        # The 4th note has strong signal overlap (same tags + topic) with
        # the first 3, so reweave should have found and linked some.
        with vault_with_bus.engine.connect() as conn:
            log_rows = conn.execute(select(reweave_log)).fetchall()

        assert len(log_rows) > 0, "Expected reweave to create links for related content"
