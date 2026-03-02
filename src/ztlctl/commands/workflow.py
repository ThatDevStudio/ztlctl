"""Command group: workflow init and update (Copier templates)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import click

from ztlctl.commands._base import DynamicProfileOption, ZtlCommand, ZtlGroup
from ztlctl.config.settings import ZtlSettings
from ztlctl.services.workflow import (
    SkillSet,
    SourceControl,
    WorkflowAssetClient,
    WorkflowChoices,
    WorkflowMode,
    WorkflowService,
)
from ztlctl.workspace_profiles import (
    DEFAULT_PROFILE,
    UnknownWorkspaceProfileError,
    discover_vault_profiles,
    resolve_workspace_profile,
)

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_WORKFLOW_CHOICES = ["claude-driven", "agent-generic", "manual"]
_SKILL_CHOICES = ["research", "engineering", "minimal"]
_SOURCE_CONTROL_CHOICES = ["git", "none"]
_ASSET_CLIENT_CHOICES = ["claude", "codex", "both"]


def _default_profile_for_prompt(
    vault_root: Path,
    *,
    existing: WorkflowChoices | None,
) -> str:
    """Choose the best default profile for workflow prompts."""
    registry = discover_vault_profiles(vault_root)
    candidates: list[str] = []
    if existing is not None:
        candidates.append(existing.profile)
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    candidates.append(settings.workspace.profile)
    candidates.append(DEFAULT_PROFILE)

    for candidate in candidates:
        try:
            resolved, _warning = resolve_workspace_profile(candidate, registry)
            return resolved
        except (UnknownWorkspaceProfileError, ValueError):
            continue
    return DEFAULT_PROFILE


def _resolve_workflow_choices(
    app: AppContext,
    *,
    vault_root: Path,
    source_control: str | None,
    profile: str | None,
    workflow_name: str | None,
    skill_set: str | None,
    existing: WorkflowChoices | None = None,
) -> WorkflowChoices:
    """Resolve workflow selections from flags or interactive prompts."""
    interactive = not app.settings.no_interact
    defaults = existing or WorkflowService.default_choices()
    profile_choices = WorkflowService.profile_choices(vault_root)
    profile_default = _default_profile_for_prompt(vault_root, existing=existing)

    if source_control is None:
        source_control = (
            click.prompt(
                "Source control",
                type=click.Choice(_SOURCE_CONTROL_CHOICES, case_sensitive=False),
                default=defaults.source_control,
            )
            if interactive
            else defaults.source_control
        )

    if profile is None:
        profile = (
            click.prompt(
                "Profile",
                type=click.Choice(profile_choices, case_sensitive=False),
                default=profile_default if interactive else defaults.profile,
            )
            if interactive
            else profile_default
        )

    if workflow_name is None:
        workflow_name = (
            click.prompt(
                "Workflow mode",
                type=click.Choice(_WORKFLOW_CHOICES, case_sensitive=False),
                default=defaults.workflow,
            )
            if interactive
            else defaults.workflow
        )

    if skill_set is None:
        skill_set = (
            click.prompt(
                "Skill set",
                type=click.Choice(_SKILL_CHOICES, case_sensitive=False),
                default=defaults.skill_set,
            )
            if interactive
            else defaults.skill_set
        )

    return WorkflowChoices(
        source_control=cast(SourceControl, source_control),
        profile=profile,
        workflow=cast(WorkflowMode, workflow_name),
        skill_set=cast(SkillSet, skill_set),
    )


@click.group(
    cls=ZtlGroup,
    examples="""\
  ztlctl workflow init
  ztlctl workflow init --profile obsidian --workflow claude-driven
  ztlctl workflow init --profile core --workflow manual
  ztlctl workflow export --client both
  ztlctl workflow validate --client claude
  ztlctl workflow update
  ztlctl workflow update --skill-set engineering""",
)
@click.pass_obj
def workflow(app: AppContext) -> None:
    """Manage workflow templates and configuration."""


@workflow.command("init", cls=ZtlCommand, examples="ztlctl workflow init --profile obsidian")
@click.argument("path", required=False, default=".")
@click.option(
    "--source-control",
    type=click.Choice(_SOURCE_CONTROL_CHOICES, case_sensitive=False),
    default=None,
    help="Source control layer.",
)
@click.option(
    "--profile",
    cls=DynamicProfileOption,
    discovery_scope="vault",
    type=str,
    default=None,
    metavar="TEXT",
    help=(
        "Workspace profile for the workflow scaffold. "
        "`none` and `vanilla` remain deprecated compatibility aliases for `core`."
    ),
)
@click.option(
    "--viewer",
    type=str,
    default=None,
    metavar="TEXT",
    help="Deprecated compatibility alias for --profile.",
)
@click.option(
    "--workflow",
    "workflow_name",
    type=click.Choice(_WORKFLOW_CHOICES, case_sensitive=False),
    default=None,
    help="Workflow mode layer.",
)
@click.option(
    "--skill-set",
    type=click.Choice(_SKILL_CHOICES, case_sensitive=False),
    default=None,
    help="Skill set layer.",
)
@click.pass_obj
def workflow_init(
    app: AppContext,
    path: str,
    source_control: str | None,
    profile: str | None,
    viewer: str | None,
    workflow_name: str | None,
    skill_set: str | None,
) -> None:
    """Initialize workflow scaffolding for a vault."""
    vault_root = Path(path).resolve()
    validation_error = WorkflowService.validate_init_target(vault_root)
    if validation_error is not None:
        app.emit(validation_error)
        return

    defaults = WorkflowService.read_answers(vault_root)
    choices = _resolve_workflow_choices(
        app,
        vault_root=vault_root,
        source_control=source_control,
        profile=profile if profile is not None else viewer,
        workflow_name=workflow_name,
        skill_set=skill_set,
        existing=defaults,
    )
    result = WorkflowService.init_workflow(vault_root, choices)
    if viewer is not None:
        result = result.model_copy(
            update={
                "warnings": [
                    *result.warnings,
                    "The workflow --viewer flag is deprecated for init; use --profile instead.",
                ]
            }
        )
    app.emit(result)


@workflow.command(
    "update",
    cls=ZtlCommand,
    examples="ztlctl workflow update --workflow agent-generic --skill-set minimal",
)
@click.argument("path", required=False, default=".")
@click.option(
    "--source-control",
    type=click.Choice(_SOURCE_CONTROL_CHOICES, case_sensitive=False),
    default=None,
    help="Override source control layer.",
)
@click.option(
    "--profile",
    cls=DynamicProfileOption,
    discovery_scope="vault",
    type=str,
    default=None,
    metavar="TEXT",
    help="Override the workflow scaffold workspace profile.",
)
@click.option(
    "--viewer",
    type=str,
    default=None,
    metavar="TEXT",
    help="Deprecated compatibility alias for --profile.",
)
@click.option(
    "--workflow",
    "workflow_name",
    type=click.Choice(_WORKFLOW_CHOICES, case_sensitive=False),
    default=None,
    help="Override workflow mode layer.",
)
@click.option(
    "--skill-set",
    type=click.Choice(_SKILL_CHOICES, case_sensitive=False),
    default=None,
    help="Override skill set layer.",
)
@click.pass_obj
def workflow_update(
    app: AppContext,
    path: str,
    source_control: str | None,
    profile: str | None,
    viewer: str | None,
    workflow_name: str | None,
    skill_set: str | None,
) -> None:
    """Update workflow scaffolding for a vault."""
    vault_root = Path(path).resolve()
    validation_error = WorkflowService.validate_update_target(vault_root)
    if validation_error is not None:
        app.emit(validation_error)
        return

    current = WorkflowService.read_answers(vault_root)
    choices = None
    if any(
        option is not None for option in (source_control, profile, viewer, workflow_name, skill_set)
    ):
        choices = _resolve_workflow_choices(
            app,
            vault_root=vault_root,
            source_control=source_control,
            profile=profile if profile is not None else viewer,
            workflow_name=workflow_name,
            skill_set=skill_set,
            existing=current,
        )
    result = WorkflowService.update_workflow(vault_root, choices=choices)
    if viewer is not None:
        result = result.model_copy(
            update={
                "warnings": [
                    *result.warnings,
                    "The workflow --viewer flag is deprecated for update; use --profile instead.",
                ]
            }
        )
    app.emit(result)


@workflow.command(
    "export",
    cls=ZtlCommand,
    examples="""\
  ztlctl workflow export --client both
  ztlctl workflow export . --client claude
  ztlctl --json workflow export --client codex""",
)
@click.argument("path", required=False, default=".")
@click.option(
    "--client",
    type=click.Choice(_ASSET_CLIENT_CHOICES, case_sensitive=False),
    default="both",
    show_default=True,
    help="Client asset bundle to render.",
)
@click.pass_obj
def workflow_export(app: AppContext, path: str, client: str) -> None:
    """Export generated Claude and/or Codex workflow assets."""
    vault_root = Path(path).resolve()
    app.emit(WorkflowService.export_assets(vault_root, client=cast(WorkflowAssetClient, client)))


@workflow.command(
    "validate",
    cls=ZtlCommand,
    examples="""\
  ztlctl workflow validate
  ztlctl workflow validate --client claude
  ztlctl --json workflow validate --client codex""",
)
@click.argument("path", required=False, default=".")
@click.option(
    "--client",
    type=click.Choice(_ASSET_CLIENT_CHOICES, case_sensitive=False),
    default="both",
    show_default=True,
    help="Client asset bundle to validate.",
)
@click.pass_obj
def workflow_validate(app: AppContext, path: str, client: str) -> None:
    """Validate generated workflow assets against the MCP catalog."""
    vault_root = Path(path).resolve()
    app.emit(WorkflowService.validate_assets(vault_root, client=cast(WorkflowAssetClient, client)))
