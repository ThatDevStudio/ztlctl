"""Tests for MCP resource _impl functions (no mcp package needed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.mcp.resources import (
    context_impl,
    overview_impl,
    self_identity_impl,
    self_methodology_impl,
    topics_impl,
    work_queue_impl,
)


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Vault directory structure."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    return Vault(settings)


class TestResources:
    """Tests for resource _impl functions."""

    def test_self_identity_reads_file(self, vault: Vault):
        # Create identity file
        self_dir = vault.root / "self"
        self_dir.mkdir(exist_ok=True)
        (self_dir / "identity.md").write_text("# Test Identity", encoding="utf-8")

        result = self_identity_impl(vault)
        assert "Test Identity" in result

    def test_self_methodology_reads_file(self, vault: Vault):
        self_dir = vault.root / "self"
        self_dir.mkdir(exist_ok=True)
        (self_dir / "methodology.md").write_text("# Test Method", encoding="utf-8")

        result = self_methodology_impl(vault)
        assert "Test Method" in result

    def test_missing_self_files_handled_gracefully(self, vault: Vault):
        result = self_identity_impl(vault)
        assert "No identity file found" in result

        result = self_methodology_impl(vault)
        assert "No methodology file found" in result

    def test_overview_returns_counts(self, vault: Vault):
        from ztlctl.services.create import CreateService

        CreateService(vault).create_note("Overview Note")

        result = overview_impl(vault)
        assert "counts" in result
        assert result["total"] >= 1
        assert result["counts"]["note"] >= 1

    def test_work_queue_returns_data(self, vault: Vault):
        result = work_queue_impl(vault)
        assert "items" in result

    def test_topics_lists_directories(self, vault: Vault):
        (vault.root / "notes" / "math").mkdir()
        (vault.root / "notes" / "physics").mkdir()

        result = topics_impl(vault)
        assert "math" in result
        assert "physics" in result

    def test_topics_empty_vault(self, vault: Vault):
        result = topics_impl(vault)
        assert result == []

    def test_context_combines_all(self, vault: Vault):
        result = context_impl(vault)
        assert "identity" in result
        assert "methodology" in result
        assert "overview" in result
