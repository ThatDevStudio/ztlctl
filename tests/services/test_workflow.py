"""Tests for WorkflowService — Copier-backed workflow scaffolding."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ztlctl.services.init import InitService
from ztlctl.services.workflow import WorkflowChoices, WorkflowService


class TestWorkflowService:
    def test_init_workflow_creates_answers_and_notes(self, tmp_path: Path) -> None:
        InitService.init_vault(tmp_path, name="wf-vault", no_workflow=True)

        result = WorkflowService.init_workflow(
            tmp_path,
            WorkflowChoices(
                source_control="git",
                viewer="obsidian",
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
                viewer="vanilla",
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
                viewer="vanilla",
                workflow="agent-generic",
                skill_set="engineering",
            ),
        )

        answers = WorkflowService.read_answers(tmp_path)

        assert answers is not None
        assert answers.viewer == "vanilla"
        assert answers.workflow == "agent-generic"
        assert answers.skill_set == "engineering"

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
