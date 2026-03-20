"""Tests for WorkflowService — Copier-backed workflow scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from ruamel.yaml import YAML

from ztlctl.services.init import InitService
from ztlctl.services.workflow import WorkflowChoices, WorkflowService


class TestWorkflowService:
    def test_agent_workflow_templates_are_packaged(self) -> None:
        agent_root = WorkflowService._agent_template_root()

        assert agent_root.joinpath("manifest.json").is_file()
        assert agent_root.joinpath("claude/.claude/settings.json.jinja").is_file()
        assert agent_root.joinpath("codex/AGENTS.md.jinja").is_file()
        assert agent_root.joinpath("codex/.ztlctl/codex/skills/methodology.md.jinja").is_file()
        assert agent_root.joinpath("codex/.ztlctl/codex/skills/session-workflow.md.jinja").is_file()
        assert agent_root.joinpath(
            "codex/.ztlctl/codex/skills/graph-intelligence.md.jinja"
        ).is_file()

    def test_init_workflow_creates_answers_and_notes(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)

        result = WorkflowService.init_workflow(
            tmp_path,
            WorkflowChoices(
                source_control="git",
                profile="obsidian",
                workflow="claude-driven",
                skill_set="research",
            ),
        )

        assert result.ok
        assert (tmp_path / ".ztlctl" / "workflow-answers.yml").is_file()
        assert (tmp_path / ".ztlctl" / "workflow" / "README.md").is_file()
        assert "claude-driven" in (tmp_path / ".ztlctl" / "workflow" / "README.md").read_text()

    def test_init_workflow_rejects_duplicate(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        WorkflowService.init_workflow(tmp_path, WorkflowService.default_choices())

        result = WorkflowService.init_workflow(tmp_path, WorkflowService.default_choices())

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "WORKFLOW_EXISTS"

    def test_update_workflow_falls_back_to_recopy_for_non_git_vault(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        WorkflowService.init_workflow(tmp_path, WorkflowService.default_choices())

        result = WorkflowService.update_workflow(
            tmp_path,
            choices=WorkflowChoices(
                source_control="none",
                profile="core",
                workflow="manual",
                skill_set="minimal",
            ),
        )

        assert result.ok
        assert result.data["mode"] == "recopy"
        assert result.warnings
        operating_mode = (tmp_path / ".ztlctl" / "workflow" / "operating-mode.md").read_text()
        assert "Manual mode" in operating_mode

    def test_read_answers_returns_choices(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        WorkflowService.init_workflow(
            tmp_path,
            WorkflowChoices(
                source_control="git",
                profile="core",
                workflow="agent-generic",
                skill_set="engineering",
            ),
        )

        answers = WorkflowService.read_answers(tmp_path)

        assert answers is not None
        assert answers.profile == "core"
        assert answers.workflow == "agent-generic"
        assert answers.skill_set == "engineering"

    def test_init_workflow_normalizes_vanilla_alias(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)

        result = WorkflowService.init_workflow(
            tmp_path,
            WorkflowChoices(
                source_control="git",
                profile="vanilla",
                workflow="manual",
                skill_set="minimal",
            ),
        )

        assert result.ok
        assert result.data["choices"]["profile"] == "core"
        assert any("deprecated" in warning.lower() for warning in result.warnings)
        answers = (tmp_path / ".ztlctl" / "workflow-answers.yml").read_text(encoding="utf-8")
        assert "profile: core" in answers

    def test_read_answers_normalizes_legacy_vanilla_value(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        answers_path = tmp_path / ".ztlctl" / "workflow-answers.yml"
        answers_path.write_text(
            "source_control: none\nviewer: vanilla\nworkflow: manual\nskill_set: minimal\n",
            encoding="utf-8",
        )

        answers = WorkflowService.read_answers(tmp_path)

        assert answers is not None
        assert answers.profile == "core"

    def test_read_answers_preserves_unknown_profile_ids(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        answers_path = tmp_path / ".ztlctl" / "workflow-answers.yml"
        answers_path.write_text(
            (
                "source_control: git\n"
                "profile: local-profile\n"
                "workflow: agent-generic\n"
                "skill_set: engineering\n"
            ),
            encoding="utf-8",
        )

        answers = WorkflowService.read_answers(tmp_path)

        assert answers is not None
        assert answers.profile == "local-profile"

    def test_update_workflow_rewrites_legacy_viewer_answers_to_profile(
        self, tmp_path: Path
    ) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        WorkflowService.init_workflow(tmp_path, WorkflowService.default_choices())
        answers_path = tmp_path / ".ztlctl" / "workflow-answers.yml"
        yaml = YAML()
        payload = yaml.load(answers_path.read_text(encoding="utf-8"))
        assert isinstance(payload, dict)
        payload["source_control"] = "none"
        payload["viewer"] = "none"
        payload.pop("profile", None)
        payload["workflow"] = "manual"
        payload["skill_set"] = "minimal"
        with answers_path.open("w", encoding="utf-8") as handle:
            yaml.dump(payload, handle)

        result = WorkflowService.update_workflow(tmp_path)

        assert result.ok
        rewritten = answers_path.read_text(encoding="utf-8")
        assert "profile: core" in rewritten
        assert "viewer:" not in rewritten
        assert not (tmp_path / ".ztlctl" / "workflow" / "viewer.md").exists()

    def test_init_workflow_accepts_local_profile_plugin(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        plugin_dir = tmp_path / ".ztlctl" / "plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        plugin_dir.joinpath("profile_plugin.py").write_text(
            """import pluggy

from ztlctl.plugins.contracts import WorkspaceProfileContribution

hookimpl = pluggy.HookimplMarker("ztlctl")


class LocalProfilePlugin:
    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [
            WorkspaceProfileContribution(
                profile_id="local-profile",
                description="Local profile.",
            )
        ]
""",
            encoding="utf-8",
        )

        result = WorkflowService.init_workflow(
            tmp_path,
            WorkflowChoices(
                source_control="git",
                profile="local-profile",
                workflow="manual",
                skill_set="minimal",
            ),
        )

        assert result.ok
        answers = (tmp_path / ".ztlctl" / "workflow-answers.yml").read_text(encoding="utf-8")
        profile_layer = (tmp_path / ".ztlctl" / "workflow" / "profile.md").read_text(
            encoding="utf-8"
        )
        assert "profile: local-profile" in answers
        assert "plugin-provided profile `local-profile`" in profile_layer

    def test_update_workflow_fails_when_stored_profile_is_missing(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        answers_path = tmp_path / ".ztlctl" / "workflow-answers.yml"
        answers_path.write_text(
            (
                "source_control: git\n"
                "profile: missing-profile\n"
                "workflow: manual\n"
                "skill_set: minimal\n"
            ),
            encoding="utf-8",
        )

        result = WorkflowService.update_workflow(tmp_path)

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "PROFILE_NOT_FOUND"
        assert result.error.detail["requested_profile"] == "missing-profile"

    def test_read_answers_returns_none_for_invalid_yaml(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        answers_path = tmp_path / ".ztlctl" / "workflow-answers.yml"
        answers_path.write_text("source_control: [\n", encoding="utf-8")

        assert WorkflowService.read_answers(tmp_path) is None

    def test_read_answers_returns_none_for_read_errors(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)
        answers_path = tmp_path / ".ztlctl" / "workflow-answers.yml"
        answers_path.write_text("source_control: git\n", encoding="utf-8")

        original_read_text = Path.read_text

        def _raise_permission_error(path: Path, *args: Any, **kwargs: Any) -> str:
            if path == answers_path:
                raise PermissionError("denied")
            return original_read_text(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", _raise_permission_error)

        assert WorkflowService.read_answers(tmp_path) is None


class TestWorkflowServiceForceTrust:
    """Tests for SECU-01: force_trust parameter for plugin template safety."""

    def test_init_workflow_force_trust_default_false(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """init_workflow accepts force_trust parameter and defaults to False."""

        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)

        # Confirm the parameter exists and defaults to False without error
        import inspect

        sig = inspect.signature(WorkflowService.init_workflow)
        assert "force_trust" in sig.parameters
        assert sig.parameters["force_trust"].default is False

    def test_run_plugin_copy_method_exists(self) -> None:
        """_run_plugin_copy static method exists on WorkflowService."""
        assert hasattr(WorkflowService, "_run_plugin_copy")

    def test_run_plugin_copy_unsafe_false_by_default(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_run_plugin_copy passes unsafe=False to copier.run_copy when force_trust=False."""
        from unittest.mock import patch

        captured: dict[str, Any] = {}

        def mock_run_copy(*args: Any, **kwargs: Any) -> None:
            captured.update(kwargs)

        with patch("ztlctl.services.workflow.run_copy", mock_run_copy):
            WorkflowService._run_plugin_copy(
                template_path="/fake/template",
                vault_root=tmp_path,
                choices=WorkflowChoices(
                    source_control="git",
                    profile="core",
                    workflow="claude-driven",
                    skill_set="research",
                ),
                force_trust=False,
            )

        assert captured.get("unsafe") is False

    def test_run_plugin_copy_unsafe_true_with_force_trust(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_run_plugin_copy passes unsafe=True to copier.run_copy when force_trust=True."""
        from unittest.mock import patch

        captured: dict[str, Any] = {}

        def mock_run_copy(*args: Any, **kwargs: Any) -> None:
            captured.update(kwargs)

        with patch("ztlctl.services.workflow.run_copy", mock_run_copy):
            WorkflowService._run_plugin_copy(
                template_path="/fake/template",
                vault_root=tmp_path,
                choices=WorkflowChoices(
                    source_control="git",
                    profile="core",
                    workflow="claude-driven",
                    skill_set="research",
                ),
                force_trust=True,
            )

        assert captured.get("unsafe") is True

    def test_builtin_run_copy_always_safe(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Built-in _run_copy does not accept force_trust — always uses unsafe=False."""
        import inspect

        sig = inspect.signature(WorkflowService._run_copy)
        # force_trust must NOT be in _run_copy signature
        assert "force_trust" not in sig.parameters

    def test_builtin_run_update_always_safe(self) -> None:
        """Built-in _run_update does not accept force_trust — always uses unsafe=False."""
        import inspect

        sig = inspect.signature(WorkflowService._run_update)
        assert "force_trust" not in sig.parameters

    def test_update_workflow_force_trust_parameter_exists(self) -> None:
        """update_workflow accepts force_trust parameter and defaults to False."""
        import inspect

        sig = inspect.signature(WorkflowService.update_workflow)
        assert "force_trust" in sig.parameters
        assert sig.parameters["force_trust"].default is False
