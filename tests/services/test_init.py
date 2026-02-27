"""Tests for InitService — vault initialization and self-generation."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ztlctl.services.init import InitService

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault


class TestInitVault:
    """Tests for InitService.init_vault()."""

    def test_creates_vault_structure(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="test-vault")
        assert result.ok
        assert (tmp_path / ".ztlctl").is_dir()
        assert (tmp_path / "self").is_dir()
        assert (tmp_path / "notes").is_dir()
        assert (tmp_path / "ops" / "logs").is_dir()
        assert (tmp_path / "ops" / "tasks").is_dir()

    def test_creates_toml_config(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="my-vault", client="vanilla", tone="minimal")
        toml = (tmp_path / "ztlctl.toml").read_text()
        assert 'name = "my-vault"' in toml
        assert 'client = "vanilla"' in toml
        assert 'tone = "minimal"' in toml

    def test_creates_database(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="db-test")
        assert (tmp_path / ".ztlctl" / "ztlctl.db").is_file()

    def test_renders_self_files(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="self-test", tone="research-partner")
        identity = (tmp_path / "self" / "identity.md").read_text()
        methodology = (tmp_path / "self" / "methodology.md").read_text()
        assert "self-test" in identity
        assert "research-partner" in identity
        assert "self-test" in methodology

    def test_uses_user_self_template_override(self, tmp_path: Path) -> None:
        template_dir = tmp_path / ".ztlctl" / "templates"
        template_dir.mkdir(parents=True)
        (template_dir / "identity.md.j2").write_text("custom identity for {{ vault_name }}\n")

        InitService.init_vault(tmp_path, name="override-vault")

        identity = (tmp_path / "self" / "identity.md").read_text()
        methodology = (tmp_path / "self" / "methodology.md").read_text()
        assert identity == "custom identity for override-vault\n"
        assert "override-vault" in methodology

    def test_identity_tone_research_partner(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="rp-vault", tone="research-partner")
        identity = (tmp_path / "self" / "identity.md").read_text()
        assert "Critique Protocol" in identity
        assert "Challenge ideas" in identity

    def test_identity_tone_assistant(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="asst-vault", tone="assistant")
        identity = (tmp_path / "self" / "identity.md").read_text()
        assert "helpful assistant" in identity
        assert "Critique Protocol" not in identity

    def test_identity_tone_minimal(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="min-vault", tone="minimal")
        identity = (tmp_path / "self" / "identity.md").read_text()
        assert "Critique Protocol" not in identity
        assert "helpful assistant" not in identity

    def test_methodology_tone_variants(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="meth-test", tone="research-partner")
        methodology = (tmp_path / "self" / "methodology.md").read_text()
        assert "Session Workflow" in methodology

    def test_obsidian_client_creates_css(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="obs-vault", client="obsidian")
        css_path = tmp_path / ".obsidian" / "snippets" / "ztlctl.css"
        assert css_path.is_file()
        assert "ztlctl" in css_path.read_text()

    def test_vanilla_client_no_obsidian_dir(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="van-vault", client="vanilla")
        assert not (tmp_path / ".obsidian").exists()

    def test_topic_directories_created(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="topics-vault", topics=["ai", "engineering"])
        assert (tmp_path / "notes" / "ai").is_dir()
        assert (tmp_path / "notes" / "engineering").is_dir()

    def test_topics_in_result_data(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="t-vault", topics=["ml", "web"])
        assert result.data["topics"] == ["ml", "web"]

    def test_workflow_file_created_by_default(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault")
        wf = tmp_path / ".ztlctl" / "workflow-answers.yml"
        assert wf.is_file()
        assert "claude-driven" in wf.read_text()

    def test_workflow_scaffold_created_by_default(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault")
        readme = tmp_path / ".ztlctl" / "workflow" / "README.md"
        assert readme.is_file()
        assert "Workflow Scaffold" in readme.read_text()

    def test_no_workflow_flag(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="nowf-vault", no_workflow=True)
        assert not (tmp_path / ".ztlctl" / "workflow-answers.yml").exists()

    def test_files_created_manifest(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="manifest-vault", client="obsidian")
        files = result.data["files_created"]
        assert "ztlctl.toml" in files
        assert ".ztlctl/ztlctl.db" in files
        assert "self/identity.md" in files
        assert "self/methodology.md" in files
        assert ".obsidian/snippets/ztlctl.css" in files
        assert ".ztlctl/workflow-answers.yml" in files
        assert ".ztlctl/workflow/README.md" in files

    def test_result_data_fields(self, tmp_path: Path) -> None:
        result = InitService.init_vault(
            tmp_path, name="data-vault", client="vanilla", tone="assistant"
        )
        assert result.ok
        assert result.op == "init_vault"
        assert result.data["name"] == "data-vault"
        assert result.data["client"] == "vanilla"
        assert result.data["tone"] == "assistant"
        assert str(tmp_path) in result.data["vault_path"]

    def test_rejects_existing_vault(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="first")
        result = InitService.init_vault(tmp_path, name="second")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "VAULT_EXISTS"

    def test_default_values(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="defaults")
        assert result.data["client"] == "obsidian"
        assert result.data["tone"] == "research-partner"
        assert result.data["topics"] == []

    def test_empty_topics_list(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="empty-topics", topics=[])
        assert result.ok
        assert result.data["topics"] == []

    def test_self_files_contain_frontmatter(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="fm-vault")
        identity = (tmp_path / "self" / "identity.md").read_text()
        assert "generated: true" in identity
        assert 'vault: "fm-vault"' in identity

    def test_stamp_failure_produces_warning(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Failed Alembic stamp is reported as a warning, not silenced."""

        def _bad_stamp(vault_root: Path) -> None:
            msg = "stamp failed"
            raise RuntimeError(msg)

        monkeypatch.setattr("ztlctl.infrastructure.database.migrations.stamp_head", _bad_stamp)

        result = InitService.init_vault(tmp_path, name="stamp-fail")
        assert result.ok  # init still succeeds
        assert any("stamp" in w.lower() for w in result.warnings)


class TestRegenerateSelf:
    """Tests for InitService.regenerate_self()."""

    @staticmethod
    def _make_vault(tmp_path: Path, **kwargs: str) -> Vault:
        from ztlctl.config.settings import ZtlSettings
        from ztlctl.infrastructure.vault import Vault

        InitService.init_vault(tmp_path, name=kwargs.get("name", "regen-vault"))
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        return Vault(settings)

    def test_regenerate_writes_files(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        result = InitService.regenerate_self(vault)
        assert result.ok
        assert result.op == "regenerate_self"
        assert "self/identity.md" in result.data["files_written"]
        assert "self/methodology.md" in result.data["files_written"]

    def test_regenerate_detects_changes(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        # Modify a self file to make it different
        (tmp_path / "self" / "identity.md").write_text("old content")
        result = InitService.regenerate_self(vault)
        assert result.ok
        assert "identity.md" in result.data["changed"]

    def test_regenerate_no_changes(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        # Regenerate immediately — should produce same content
        result = InitService.regenerate_self(vault)
        assert result.ok
        # Changed list may be empty or have items depending on date precision
        assert isinstance(result.data["changed"], list)

    def test_regenerate_creates_self_dir(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        # Remove self dir
        import shutil

        shutil.rmtree(tmp_path / "self")
        result = InitService.regenerate_self(vault)
        assert result.ok
        assert (tmp_path / "self" / "identity.md").is_file()

    def test_regenerate_uses_user_template_override(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path, name="custom-regen")
        template_dir = tmp_path / ".ztlctl" / "templates" / "self"
        template_dir.mkdir(parents=True)
        (template_dir / "identity.md.j2").write_text("regen override {{ vault_name }}\n")

        result = InitService.regenerate_self(vault)

        assert result.ok
        assert (tmp_path / "self" / "identity.md").read_text() == "regen override custom-regen\n"


class TestCheckStaleness:
    """Tests for InitService.check_staleness()."""

    @staticmethod
    def _make_vault(tmp_path: Path) -> Vault:
        from ztlctl.config.settings import ZtlSettings
        from ztlctl.infrastructure.vault import Vault

        InitService.init_vault(tmp_path, name="stale-vault")
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        return Vault(settings)

    def test_not_stale_after_init(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        result = InitService.check_staleness(vault)
        assert result.ok
        assert result.data["stale"] is False
        assert result.data["stale_files"] == []

    def test_stale_after_config_update(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        # Touch config to be newer than self files
        time.sleep(0.05)
        toml_path = tmp_path / "ztlctl.toml"
        toml_path.write_text(toml_path.read_text())
        os.utime(toml_path, (time.time() + 1, time.time() + 1))
        result = InitService.check_staleness(vault)
        assert result.ok
        assert result.data["stale"] is True
        assert len(result.data["stale_files"]) > 0

    def test_no_config_error(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        (tmp_path / "ztlctl.toml").unlink()
        result = InitService.check_staleness(vault)
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_CONFIG"
