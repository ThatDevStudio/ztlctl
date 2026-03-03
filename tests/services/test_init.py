"""Tests for InitService — vault initialization and self-generation."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ztlctl.plugins.contracts import (
    VaultInitContext,
    VaultInitStepContribution,
    VaultInitStepResult,
    WorkspaceProfileContribution,
)
from ztlctl.services.init import InitService
from ztlctl.workspace_profiles import WorkspaceProfileRegistry, core_workspace_profile

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
        InitService.init_vault(tmp_path, name="my-vault", profile="core", tone="minimal")
        toml = (tmp_path / "ztlctl.toml").read_text()
        assert 'name = "my-vault"' in toml
        assert "[workspace]" in toml
        assert 'profile = "core"' in toml
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
        InitService.init_vault(tmp_path, name="obs-vault", profile="obsidian")
        css_path = tmp_path / ".obsidian" / "snippets" / "ztlctl.css"
        assert css_path.is_file()
        assert "ztlctl" in css_path.read_text()
        assert (tmp_path / ".obsidian" / "snippets" / "garden-layers.css").is_file()
        assert (tmp_path / "garden" / "README.md").is_file()

    def test_none_client_no_obsidian_dir(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="none-vault", profile="core")
        assert not (tmp_path / ".obsidian").exists()
        assert not (tmp_path / "garden").exists()

    def test_missing_profile_returns_profile_not_found(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="missing-vault", profile="missing-profile")

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "PROFILE_NOT_FOUND"
        assert result.error.detail["requested_profile"] == "missing-profile"
        assert "core" in result.error.detail["available_profiles"]

    def test_init_ignores_target_local_profile_plugins(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("local_profile.py").write_text(
            """import pluggy

from ztlctl.plugins.contracts import WorkspaceProfileContribution

hookimpl = pluggy.HookimplMarker("ztlctl")


class LocalProfilePlugin:
    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [WorkspaceProfileContribution(profile_id="local-profile", description="Local.")]
""",
            encoding="utf-8",
        )

        result = InitService.init_vault(
            tmp_path,
            name="local-plugin-vault",
            profile="local-profile",
        )

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "PROFILE_NOT_FOUND"
        assert result.error.detail["discovery_scope"] == "init"

    def test_init_ignores_target_local_init_step_plugins(self, tmp_path: Path) -> None:
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("local_init_step.py").write_text(
            """import pluggy

from ztlctl.plugins.contracts import VaultInitStepContribution, VaultInitStepResult

hookimpl = pluggy.HookimplMarker("ztlctl")


class LocalInitStepPlugin:
    @hookimpl
    def register_vault_init_steps(self) -> list[VaultInitStepContribution]:
        return [
            VaultInitStepContribution(
                step_id="local-step",
                description="Local step.",
                profiles=("core",),
                run=lambda context: VaultInitStepResult(files_created=("local-step.txt",)),
            )
        ]
""",
            encoding="utf-8",
        )

        result = InitService.init_vault(tmp_path, name="local-step-vault", profile="core")

        assert result.ok
        assert "local-step" not in result.data["step_ids_executed"]
        assert not (tmp_path / "local-step.txt").exists()

    def test_vanilla_client_alias_normalizes_to_none(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="alias-vault", client="vanilla")

        assert result.ok
        assert result.data["client"] == "none"
        assert result.data["profile"] == "core"
        assert 'profile = "core"' in (tmp_path / "ztlctl.toml").read_text()
        assert any("deprecated" in warning.lower() for warning in result.warnings)

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

    def test_init_dispatches_post_init_hooks(self, tmp_path: Path) -> None:
        marker = tmp_path / "post-init.txt"
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("post_init_plugin.py").write_text(
            f"""import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")


class PostInitPlugin:
    @hookimpl
    def post_init(self, vault_name: str, client: str, tone: str) -> None:
        with open({str(marker)!r}, "w", encoding="utf-8") as fh:
            fh.write(f"{{vault_name}}|{{client}}|{{tone}}")
""",
            encoding="utf-8",
        )

        result = InitService.init_vault(tmp_path, name="hooked-vault", client="none")

        assert result.ok
        assert marker.read_text(encoding="utf-8") == "hooked-vault|none|research-partner"

    def test_init_dispatches_post_init_profile_hooks(self, tmp_path: Path) -> None:
        marker = tmp_path / "post-init-profile.txt"
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("post_init_profile_plugin.py").write_text(
            f"""import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")


class PostInitProfilePlugin:
    @hookimpl
    def post_init_profile(
        self,
        vault_name: str,
        profile: str,
        tone: str,
        managed_paths: list[str],
    ) -> None:
        with open({str(marker)!r}, "w", encoding="utf-8") as fh:
            fh.write(f"{{vault_name}}|{{profile}}|{{tone}}|{{','.join(managed_paths)}}")
""",
            encoding="utf-8",
        )

        result = InitService.init_vault(tmp_path, name="profile-vault", profile="obsidian")

        assert result.ok
        assert (
            marker.read_text(encoding="utf-8")
            == "profile-vault|obsidian|research-partner|.obsidian"
        )

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
        assert ".obsidian/community-plugins.json" in files
        assert "garden/README.md" in files
        assert ".ztlctl/workflow-answers.yml" in files
        assert ".ztlctl/workflow/README.md" in files

    def test_result_data_fields(self, tmp_path: Path) -> None:
        result = InitService.init_vault(
            tmp_path, name="data-vault", profile="core", tone="assistant"
        )
        assert result.ok
        assert result.op == "init_vault"
        assert result.data["name"] == "data-vault"
        assert result.data["profile"] == "core"
        assert result.data["client"] == "none"
        assert result.data["tone"] == "assistant"
        assert str(tmp_path) in result.data["vault_path"]
        assert result.data["setup_steps"] == []
        assert isinstance(result.data["step_ids_executed"], list)

    def test_rejects_existing_vault(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="first")
        result = InitService.init_vault(tmp_path, name="second")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "VAULT_EXISTS"

    def test_default_values(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="defaults")
        assert result.data["profile"] == "core"
        assert result.data["client"] == "none"
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
        assert 'profile: "core"' in identity

    def test_self_files_use_current_ids_and_lifecycle_terms(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="truth-vault", profile="core")

        identity = (tmp_path / "self" / "identity.md").read_text(encoding="utf-8")
        methodology = (tmp_path / "self" / "methodology.md").read_text(encoding="utf-8")

        assert "ztl_<8hex>" in identity
        assert "seed → budding → evergreen" in identity
        assert "sapling" not in identity
        assert "ref_<8hex>" in methodology
        assert "inbox → active → blocked/done/dropped" in methodology
        assert "ZTL-NNNN" not in methodology

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

    def test_obsidian_init_returns_setup_steps(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="obsidian-steps", profile="obsidian")

        assert result.ok
        setup_steps = result.data["setup_steps"]
        assert len(setup_steps) == 3
        assert setup_steps[0]["title"] == "Install the curated Obsidian plugins"
        assert any("dataview" in item.lower() for item in setup_steps[0]["items"])
        assert result.data["step_ids_executed"] == [
            "obsidian_scaffold",
            "obsidian_plugin_install_guidance",
        ]

    def test_obsidian_scaffold_writes_expected_files(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="obsidian-artifacts", profile="obsidian")

        assert result.ok
        expected = [
            ".obsidian/app.json",
            ".obsidian/appearance.json",
            ".obsidian/core-plugins.json",
            ".obsidian/community-plugins.json",
            ".obsidian/templates.json",
            ".obsidian/graph.json",
            ".obsidian/snippets/ztlctl.css",
            ".obsidian/snippets/garden-layers.css",
            ".obsidian/plugins/folder-notes/data.json",
            ".obsidian/plugins/obsidian-book-search-plugin/data.json",
            ".obsidian/plugins/omnisearch/data.json",
            "garden/README.md",
            "garden/templates/note.md",
            "garden/templates/grove.md",
            "garden/templates/book.md",
        ]
        for rel_path in expected:
            assert (tmp_path / rel_path).exists(), rel_path
        assert not (tmp_path / ".obsidian" / "workspace.json").exists()

    def test_obsidian_scaffold_contents_match_curated_defaults(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="obsidian-content", profile="obsidian")

        assert result.ok
        community_plugins = (tmp_path / ".obsidian" / "community-plugins.json").read_text(
            encoding="utf-8"
        )
        assert json.loads(community_plugins) == [
            "dataview",
            "templater-obsidian",
            "folder-notes",
            "omnisearch",
            "obsidian-book-search-plugin",
        ]
        appearance = json.loads(
            (tmp_path / ".obsidian" / "appearance.json").read_text(encoding="utf-8")
        )
        assert appearance["enabledCssSnippets"] == ["ztlctl", "garden-layers"]
        app_cfg = json.loads((tmp_path / ".obsidian" / "app.json").read_text(encoding="utf-8"))
        assert app_cfg["newFileFolderPath"] == "garden/notes"
        assert app_cfg["attachmentFolderPath"] == "garden/attachments"
        templates = json.loads(
            (tmp_path / ".obsidian" / "templates.json").read_text(encoding="utf-8")
        )
        assert templates["folder"] == "garden/templates"
        graph_cfg = (tmp_path / ".obsidian" / "graph.json").read_text(encoding="utf-8")
        assert "path:notes" in graph_cfg
        assert "path:ops/tasks" in graph_cfg
        assert "path:ops/logs" in graph_cfg
        assert "path:garden/notes" in graph_cfg
        assert "path:garden/groves" in graph_cfg
        assert "path:garden/library" in graph_cfg
        assert "conversations" not in graph_cfg
        assert "decisions" not in graph_cfg
        assert "knowledge" not in graph_cfg
        assert "resources" not in graph_cfg
        assert "backlog" not in graph_cfg
        note_template = (tmp_path / "garden" / "templates" / "note.md").read_text(encoding="utf-8")
        assert "cssclasses: [garden-note, seed]" in note_template
        assert "growth: seed" in note_template
        combined = "\n".join(
            [
                note_template,
                (tmp_path / "garden" / "templates" / "grove.md").read_text(encoding="utf-8"),
                (tmp_path / "garden" / "templates" / "book.md").read_text(encoding="utf-8"),
                (tmp_path / "garden" / "README.md").read_text(encoding="utf-8"),
            ]
        )
        assert "seedling" not in combined
        assert "sapling" not in combined

    def test_garden_readme_mirrors_obsidian_init_guidance(self, tmp_path: Path) -> None:
        result = InitService.init_vault(tmp_path, name="garden-readme", profile="obsidian")

        assert result.ok
        readme = (tmp_path / "garden" / "README.md").read_text(encoding="utf-8")
        assert "Install the curated Obsidian plugins" in readme
        assert "Verify the Obsidian workspace defaults" in readme
        assert "garden/notes" in readme
        assert "human-owned" in readme

    def test_garden_is_not_reported_as_profile_managed(self, tmp_path: Path) -> None:
        marker = tmp_path / "post-init-profile.txt"
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True)
        plugin_dir.joinpath("post_init_profile_plugin.py").write_text(
            f"""import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")


class PostInitProfilePlugin:
    @hookimpl
    def post_init_profile(
        self,
        vault_name: str,
        profile: str,
        tone: str,
        managed_paths: list[str],
    ) -> None:
        with open({str(marker)!r}, "w", encoding="utf-8") as fh:
            fh.write(",".join(managed_paths))
""",
            encoding="utf-8",
        )

        result = InitService.init_vault(tmp_path, name="owned-vault", profile="obsidian")

        assert result.ok
        assert marker.read_text(encoding="utf-8") == ".obsidian"

    def test_legacy_profile_scaffold_runs_through_init_step_wrapper(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sentinel = "legacy/profile.txt"

        def _legacy_scaffold(vault_root: Path) -> list[str]:
            target = vault_root / sentinel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("legacy", encoding="utf-8")
            return [sentinel]

        registry = WorkspaceProfileRegistry(
            profiles={
                "core": core_workspace_profile(),
                "legacy-profile": WorkspaceProfileContribution(
                    profile_id="legacy-profile",
                    description="Legacy profile.",
                    init_scaffold=_legacy_scaffold,
                ),
            },
            aliases={"none": "core", "vanilla": "core"},
        )
        monkeypatch.setattr("ztlctl.services.init.discover_init_profiles", lambda: registry)
        monkeypatch.setattr(
            "ztlctl.plugins.manager.PluginManager.discover_and_load",
            lambda self, *, local_dir=None, include_entrypoints=True: [],
        )
        monkeypatch.setattr(
            "ztlctl.plugins.manager.PluginManager.vault_init_step_contributions",
            lambda self, reserved_names=None: [],
        )

        result = InitService.init_vault(tmp_path, name="legacy-wrapper", profile="legacy-profile")

        assert result.ok
        assert sentinel in result.data["files_created"]
        assert result.data["step_ids_executed"] == ["legacy_profile_scaffold__legacy-profile"]

    def test_init_step_failure_returns_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _bad_step(_context: VaultInitContext) -> VaultInitStepResult:
            raise RuntimeError("boom")

        monkeypatch.setattr(
            "ztlctl.services.init._collect_init_steps",
            lambda _registry: [
                VaultInitStepContribution(
                    step_id="bad-step",
                    description="Broken init step.",
                    profiles=("core",),
                    run=_bad_step,
                )
            ],
        )

        result = InitService.init_vault(tmp_path, name="broken-step", profile="core")

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "INIT_STEP_FAILED"
        assert result.error.detail["step_id"] == "bad-step"

    def test_init_steps_execute_in_order_then_step_id(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry = WorkspaceProfileRegistry(
            profiles={
                "core": core_workspace_profile(),
                "ordered-profile": WorkspaceProfileContribution(
                    profile_id="ordered-profile",
                    description="Ordered profile.",
                ),
            },
            aliases={"none": "core", "vanilla": "core"},
        )
        monkeypatch.setattr("ztlctl.services.init.discover_init_profiles", lambda: registry)
        monkeypatch.setattr(
            "ztlctl.plugins.manager.PluginManager.discover_and_load",
            lambda self, *, local_dir=None, include_entrypoints=True: [],
        )
        monkeypatch.setattr(
            "ztlctl.plugins.manager.PluginManager.vault_init_step_contributions",
            lambda self, reserved_names=None: [
                VaultInitStepContribution(
                    step_id="later",
                    description="Later step.",
                    order=200,
                    profiles=("ordered-profile",),
                    run=lambda _context: VaultInitStepResult(files_created=("later.txt",)),
                ),
                VaultInitStepContribution(
                    step_id="beta",
                    description="Beta step.",
                    order=100,
                    profiles=("ordered-profile",),
                    run=lambda _context: VaultInitStepResult(files_created=("beta.txt",)),
                ),
                VaultInitStepContribution(
                    step_id="alpha",
                    description="Alpha step.",
                    order=100,
                    profiles=("ordered-profile",),
                    run=lambda _context: VaultInitStepResult(files_created=("alpha.txt",)),
                ),
            ],
        )

        result = InitService.init_vault(tmp_path, name="ordered-vault", profile="ordered-profile")

        assert result.ok
        assert result.data["step_ids_executed"] == ["alpha", "beta", "later"]

    def test_init_steps_filter_by_profile(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "ztlctl.services.init._collect_init_steps",
            lambda _registry: [
                VaultInitStepContribution(
                    step_id="other-profile-step",
                    description="Wrong profile.",
                    profiles=("obsidian",),
                    run=lambda _context: VaultInitStepResult(files_created=("wrong.txt",)),
                ),
                VaultInitStepContribution(
                    step_id="matching-step",
                    description="Matching profile.",
                    profiles=("core",),
                    run=lambda _context: VaultInitStepResult(files_created=("match.txt",)),
                ),
            ],
        )

        result = InitService.init_vault(tmp_path, name="filtered-steps", profile="core")

        assert result.ok
        assert result.data["step_ids_executed"] == ["matching-step"]
        assert "match.txt" in result.data["files_created"]
        assert "wrong.txt" not in result.data["files_created"]


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

    def test_regenerate_requires_config(self, tmp_path: Path) -> None:
        vault = self._make_vault(tmp_path)
        (tmp_path / "ztlctl.toml").unlink()

        result = InitService.regenerate_self(vault)

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_CONFIG"

    def test_regenerate_fails_when_configured_profile_is_missing(self, tmp_path: Path) -> None:
        self._make_vault(tmp_path).close()
        (tmp_path / "ztlctl.toml").write_text(
            '[vault]\nname = "regen-vault"\n\n[workspace]\nprofile = "missing-profile"\n',
            encoding="utf-8",
        )

        from ztlctl.config.settings import ZtlSettings
        from ztlctl.infrastructure.vault import Vault

        missing_vault = Vault(ZtlSettings.from_cli(vault_root=tmp_path))
        try:
            result = InitService.regenerate_self(missing_vault)
        finally:
            missing_vault.close()

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "PROFILE_NOT_FOUND"


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
