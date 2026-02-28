"""Command group: workflow init and update (Copier templates)."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import click

from ztlctl.commands._base import ZtlCommand, ZtlGroup
from ztlctl.services.workflow import (
    SkillSet,
    SourceControl,
    Viewer,
    WorkflowChoices,
    WorkflowMode,
    WorkflowService,
)

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_VIEWER_CHOICES = ["obsidian", "vanilla"]
_WORKFLOW_CHOICES = ["claude-driven", "agent-generic", "manual"]
_SKILL_CHOICES = ["research", "engineering", "minimal"]
_SOURCE_CONTROL_CHOICES = ["git", "none"]


def _resolve_workflow_choices(
    app: AppContext,
    *,
    source_control: str | None,
    viewer: str | None,
    workflow_name: str | None,
    skill_set: str | None,
    existing: WorkflowChoices | None = None,
) -> WorkflowChoices:
    """Resolve workflow selections from flags or interactive prompts."""
    interactive = not app.settings.no_interact
    defaults = existing or WorkflowService.default_choices()

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

    if viewer is None:
        viewer = (
            click.prompt(
                "Viewer",
                type=click.Choice(_VIEWER_CHOICES, case_sensitive=False),
                default=defaults.viewer,
            )
            if interactive
            else defaults.viewer
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
        viewer=cast(Viewer, viewer),
        workflow=cast(WorkflowMode, workflow_name),
        skill_set=cast(SkillSet, skill_set),
    )


@click.group(
    cls=ZtlGroup,
    examples="""\
  ztlctl workflow init
  ztlctl workflow init --viewer obsidian --workflow claude-driven
  ztlctl workflow update
  ztlctl workflow update --skill-set engineering""",
)
@click.pass_obj
def workflow(app: AppContext) -> None:
    """Manage workflow templates and configuration."""


@workflow.command("init", cls=ZtlCommand, examples="ztlctl workflow init --viewer obsidian")
@click.argument("path", required=False, default=".")
@click.option(
    "--source-control",
    type=click.Choice(_SOURCE_CONTROL_CHOICES, case_sensitive=False),
    default=None,
    help="Source control layer.",
)
@click.option(
    "--viewer",
    type=click.Choice(_VIEWER_CHOICES, case_sensitive=False),
    default=None,
    help="Viewer layer.",
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
        source_control=source_control,
        viewer=viewer,
        workflow_name=workflow_name,
        skill_set=skill_set,
        existing=defaults,
    )
    app.emit(WorkflowService.init_workflow(vault_root, choices))


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
    "--viewer",
    type=click.Choice(_VIEWER_CHOICES, case_sensitive=False),
    default=None,
    help="Override viewer layer.",
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
    if any(option is not None for option in (source_control, viewer, workflow_name, skill_set)):
        choices = _resolve_workflow_choices(
            app,
            source_control=source_control,
            viewer=viewer,
            workflow_name=workflow_name,
            skill_set=skill_set,
            existing=current,
        )
    app.emit(WorkflowService.update_workflow(vault_root, choices=choices))
