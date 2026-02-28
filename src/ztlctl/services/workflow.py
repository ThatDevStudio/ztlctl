"""WorkflowService — Copier-backed workflow scaffolding for vaults."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Literal, cast

from copier import run_copy, run_recopy, run_update
from copier.errors import CopierError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced

WorkflowMode = Literal["claude-driven", "agent-generic", "manual"]
SkillSet = Literal["research", "engineering", "minimal"]
SourceControl = Literal["git", "none"]
Viewer = Literal["obsidian", "vanilla"]

_ANSWERS_RELATIVE_PATH = Path(".ztlctl") / "workflow-answers.yml"
_GENERATED_FILES = [
    ".ztlctl/workflow-answers.yml",
    ".ztlctl/workflow/README.md",
    ".ztlctl/workflow/source-control.md",
    ".ztlctl/workflow/viewer.md",
    ".ztlctl/workflow/operating-mode.md",
    ".ztlctl/workflow/skill-set.md",
]
_SOURCE_CONTROL_VALUES = {"git", "none"}
_VIEWER_VALUES = {"obsidian", "vanilla"}
_WORKFLOW_VALUES = {"claude-driven", "agent-generic", "manual"}
_SKILL_SET_VALUES = {"research", "engineering", "minimal"}


@dataclass(frozen=True)
class WorkflowChoices:
    """Resolved workflow selections used for Copier rendering."""

    source_control: SourceControl
    viewer: Viewer
    workflow: WorkflowMode
    skill_set: SkillSet

    def as_data(self) -> dict[str, str]:
        """Convert to Copier's expected mapping."""
        return {
            "source_control": self.source_control,
            "viewer": self.viewer,
            "workflow": self.workflow,
            "skill_set": self.skill_set,
        }


class WorkflowService:
    """Apply or update workflow scaffolding in a vault."""

    @staticmethod
    def default_choices(*, viewer: Viewer = "obsidian") -> WorkflowChoices:
        """Return the default workflow selection set."""
        return WorkflowChoices(
            source_control="git",
            viewer=viewer,
            workflow="claude-driven",
            skill_set="research",
        )

    @staticmethod
    def read_answers(vault_root: Path) -> WorkflowChoices | None:
        """Read the stored workflow answers file if present."""
        answers_path = vault_root / _ANSWERS_RELATIVE_PATH
        if not answers_path.exists():
            return None

        try:
            data = YAML(typ="safe").load(answers_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, YAMLError):
            return None
        if not isinstance(data, dict):
            return None

        try:
            source_control = cast(SourceControl, str(data["source_control"]))
            viewer = cast(Viewer, str(data["viewer"]))
            workflow = cast(WorkflowMode, str(data["workflow"]))
            skill_set = cast(SkillSet, str(data["skill_set"]))
        except KeyError:
            return None
        if source_control not in _SOURCE_CONTROL_VALUES:
            return None
        if viewer not in _VIEWER_VALUES:
            return None
        if workflow not in _WORKFLOW_VALUES:
            return None
        if skill_set not in _SKILL_SET_VALUES:
            return None

        return WorkflowChoices(
            source_control=source_control,
            viewer=viewer,
            workflow=workflow,
            skill_set=skill_set,
        )

    @staticmethod
    def _validate_vault_root(vault_root: Path, *, op: str) -> ServiceResult | None:
        """Ensure the workflow service operates on a vault-like directory."""
        if (vault_root / "ztlctl.toml").exists() or (vault_root / ".ztlctl").exists():
            return None
        return ServiceResult(
            ok=False,
            op=op,
            error=ServiceError(
                code="NOT_A_VAULT",
                message=f"No ztlctl vault found at {vault_root}",
                detail={"path": str(vault_root)},
            ),
        )

    @staticmethod
    def _template_root() -> Traversable:
        """Return the packaged Copier template root."""
        return resources.files("ztlctl").joinpath("templates/workflow")

    @staticmethod
    def validate_init_target(vault_root: Path) -> ServiceResult | None:
        """Validate that a vault can accept initial workflow scaffolding."""
        vault_root = vault_root.resolve()
        validation_error = WorkflowService._validate_vault_root(vault_root, op="workflow_init")
        if validation_error is not None:
            return validation_error

        answers_path = vault_root / _ANSWERS_RELATIVE_PATH
        if answers_path.exists():
            return ServiceResult(
                ok=False,
                op="workflow_init",
                error=ServiceError(
                    code="WORKFLOW_EXISTS",
                    message="Workflow scaffolding already exists. Use `ztlctl workflow update`.",
                    detail={"path": str(answers_path)},
                ),
            )

        return None

    @staticmethod
    def validate_update_target(vault_root: Path) -> ServiceResult | None:
        """Validate that a vault can update existing workflow scaffolding."""
        vault_root = vault_root.resolve()
        validation_error = WorkflowService._validate_vault_root(vault_root, op="workflow_update")
        if validation_error is not None:
            return validation_error

        answers_path = vault_root / _ANSWERS_RELATIVE_PATH
        if not answers_path.exists():
            return ServiceResult(
                ok=False,
                op="workflow_update",
                error=ServiceError(
                    code="WORKFLOW_NOT_INITIALIZED",
                    message="Workflow scaffolding has not been initialized for this vault.",
                    detail={"path": str(answers_path)},
                ),
            )

        return None

    @staticmethod
    def _run_copy(vault_root: Path, choices: WorkflowChoices) -> None:
        with resources.as_file(WorkflowService._template_root()) as template_root:
            run_copy(
                str(template_root),
                dst_path=vault_root,
                answers_file=str(_ANSWERS_RELATIVE_PATH),
                data=choices.as_data(),
                defaults=True,
                overwrite=True,
                quiet=True,
            )

    @staticmethod
    def _run_update(vault_root: Path, choices: WorkflowChoices | None) -> tuple[str, list[str]]:
        warnings: list[str] = []
        update_data = None if choices is None else choices.as_data()

        try:
            run_update(
                dst_path=vault_root,
                answers_file=str(_ANSWERS_RELATIVE_PATH),
                data=update_data,
                defaults=True,
                overwrite=True,
                quiet=True,
            )
            return "update", warnings
        except CopierError as exc:
            warnings.append(
                f"Copier update fallback to recopy ({exc}); local merge metadata unavailable."
            )
            run_recopy(
                dst_path=vault_root,
                answers_file=str(_ANSWERS_RELATIVE_PATH),
                data=update_data,
                defaults=True,
                overwrite=True,
                quiet=True,
            )
            return "recopy", warnings

    @staticmethod
    @traced
    def init_workflow(vault_root: Path, choices: WorkflowChoices) -> ServiceResult:
        """Initialize Copier-backed workflow scaffolding for a vault."""
        vault_root = vault_root.resolve()
        validation_error = WorkflowService.validate_init_target(vault_root)
        if validation_error is not None:
            return validation_error

        try:
            WorkflowService._run_copy(vault_root, choices)
        except CopierError as exc:
            return ServiceResult(
                ok=False,
                op="workflow_init",
                error=ServiceError(
                    code="WORKFLOW_INIT_FAILED",
                    message=f"Failed to initialize workflow template: {exc}",
                ),
            )

        return ServiceResult(
            ok=True,
            op="workflow_init",
            data={
                "vault_path": str(vault_root),
                "files_written": list(_GENERATED_FILES),
                "choices": choices.as_data(),
            },
        )

    @staticmethod
    @traced
    def update_workflow(
        vault_root: Path,
        *,
        choices: WorkflowChoices | None = None,
    ) -> ServiceResult:
        """Update workflow scaffolding using stored answers plus optional overrides."""
        vault_root = vault_root.resolve()
        validation_error = WorkflowService.validate_update_target(vault_root)
        if validation_error is not None:
            return validation_error

        try:
            mode, warnings = WorkflowService._run_update(vault_root, choices)
        except CopierError as exc:
            return ServiceResult(
                ok=False,
                op="workflow_update",
                error=ServiceError(
                    code="WORKFLOW_UPDATE_FAILED",
                    message=f"Failed to update workflow template: {exc}",
                ),
            )

        final_choices = WorkflowService.read_answers(vault_root)
        data = {
            "vault_path": str(vault_root),
            "files_written": list(_GENERATED_FILES),
            "mode": mode,
            "choices": final_choices.as_data() if final_choices is not None else {},
        }
        return ServiceResult(ok=True, op="workflow_update", data=data, warnings=warnings)
