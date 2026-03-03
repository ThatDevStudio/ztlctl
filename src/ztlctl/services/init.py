"""InitService — vault initialization and self-generation.

Unlike other services, InitService does NOT extend BaseService because it
operates *before* a Vault exists.  All public methods are @staticmethod
(init_vault) or take a Vault parameter (regenerate_self, check_staleness).
"""

from __future__ import annotations

import os
from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from ztlctl.infrastructure.templates import build_template_environment
from ztlctl.plugins.contracts import (
    VaultInitContext,
    VaultInitInstruction,
    VaultInitStepContribution,
    VaultInitStepResult,
)
from ztlctl.plugins.manager import PluginManager
from ztlctl.services._helpers import today_iso
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced
from ztlctl.workspace_profiles import (
    UnknownWorkspaceProfileError,
    WorkspaceProfileRegistry,
    discover_init_profiles,
    discover_vault_profiles,
    profile_to_legacy_client,
    resolve_profile_selection,
    resolve_workspace_profile,
)

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault

# ── Template rendering ────────────────────────────────────────────────


def _render_self_files(
    *,
    vault_name: str,
    tone: str,
    profile: str,
    client: str,
    topics: list[str],
    created: str,
    vault_root: Path | None = None,
) -> dict[str, str]:
    """Render identity.md and methodology.md from Jinja2 templates.

    Returns a dict mapping filename -> rendered content.
    """
    env = build_template_environment("self", vault_root=vault_root)
    context = {
        "vault_name": vault_name,
        "tone": tone,
        "profile": profile,
        "client": client,
        "topics": topics,
        "created": created,
    }
    return {
        "identity.md": env.get_template("identity.md.j2").render(context),
        "methodology.md": env.get_template("methodology.md.j2").render(context),
    }


def _dispatch_post_init(
    *,
    vault_path: Path,
    name: str,
    profile: str,
    client: str,
    tone: str,
    managed_paths: list[str],
) -> list[str]:
    """Dispatch post-init hooks against the freshly created vault."""
    warnings: list[str] = []

    try:
        from ztlctl.config.settings import ZtlSettings
        from ztlctl.infrastructure.vault import Vault

        settings = ZtlSettings.from_cli(vault_root=vault_path)
        vault = Vault(settings)
        try:
            vault.init_event_bus(sync=True)
            bus = vault.event_bus
            if bus is not None:
                bus.dispatch(
                    "post_init",
                    {
                        "vault_name": name,
                        "client": client,
                        "tone": tone,
                    },
                )
                bus.dispatch(
                    "post_init_profile",
                    {
                        "vault_name": name,
                        "profile": profile,
                        "tone": tone,
                        "managed_paths": managed_paths,
                    },
                )
        finally:
            vault.close(wait_for_events=True)
    except Exception as exc:
        warnings.append(f"post_init hooks skipped ({exc})")

    return warnings


def _serialize_instruction(instruction: VaultInitInstruction) -> dict[str, str | list[str]]:
    """Convert a vault init instruction into JSON-safe result data."""
    return {
        "instruction_id": instruction.instruction_id,
        "title": instruction.title,
        "body": instruction.body,
        "items": list(instruction.items),
        "kind": instruction.kind,
    }


def _legacy_scaffold_step(
    profile_id: str,
    scaffold: Callable[[Path], list[str]],
) -> VaultInitStepContribution:
    """Wrap the deprecated profile `init_scaffold` into a vault init step."""

    def _run(context: VaultInitContext) -> VaultInitStepResult:
        return VaultInitStepResult(files_created=tuple(scaffold(context.vault_root)))

    return VaultInitStepContribution(
        step_id=f"legacy_profile_scaffold__{profile_id}",
        description=f"Legacy scaffold wrapper for workspace profile `{profile_id}`.",
        run=_run,
        order=150,
        profiles=(profile_id,),
    )


def _step_applies_to_profile(step: VaultInitStepContribution, profile: str) -> bool:
    """Whether a step applies to the selected profile."""
    if not step.profiles:
        return True
    return profile in {item.strip().lower() for item in step.profiles}


def _collect_init_steps(
    profile_registry: WorkspaceProfileRegistry,
) -> list[VaultInitStepContribution]:
    """Discover init steps from entry-point plugins plus legacy scaffolds."""
    plugin_manager = PluginManager()
    plugin_manager.discover_and_load(local_dir=None, include_entrypoints=True)
    steps = list(plugin_manager.vault_init_step_contributions())
    for profile_id, contribution in profile_registry.profiles.items():
        scaffold = contribution.init_scaffold
        if scaffold is None:
            continue
        steps.append(_legacy_scaffold_step(profile_id, scaffold))
    return sorted(steps, key=lambda item: (item.order, item.step_id))


def _run_init_steps(
    *,
    vault_path: Path,
    name: str,
    profile: str,
    tone: str,
    topics: list[str],
    no_workflow: bool,
    profile_registry: WorkspaceProfileRegistry,
    existing_files: list[str],
) -> tuple[list[str], list[str], list[dict[str, str | list[str]]], list[str]] | ServiceResult:
    """Execute ordered init steps and aggregate their outputs."""
    files_created: list[str] = []
    warnings: list[str] = []
    instructions: list[dict[str, str | list[str]]] = []
    step_ids_executed: list[str] = []
    context = VaultInitContext(
        vault_root=vault_path,
        vault_name=name,
        profile=profile,
        tone=tone,
        topics=tuple(topics),
        no_workflow=no_workflow,
    )

    for step in _collect_init_steps(profile_registry):
        if not _step_applies_to_profile(step, profile):
            continue
        try:
            result = step.run(context)
        except Exception as exc:
            return ServiceResult(
                ok=False,
                op="init_vault",
                warnings=warnings,
                error=ServiceError(
                    code="INIT_STEP_FAILED",
                    message=f"Vault init step `{step.step_id}` failed: {exc}",
                    detail={
                        "step_id": step.step_id,
                        "profile": profile,
                        "error": str(exc),
                    },
                ),
            )
        if not isinstance(result, VaultInitStepResult):
            return ServiceResult(
                ok=False,
                op="init_vault",
                warnings=warnings,
                error=ServiceError(
                    code="INIT_STEP_FAILED",
                    message=(
                        f"Vault init step `{step.step_id}` returned an invalid result type: "
                        f"{type(result).__name__}"
                    ),
                    detail={
                        "step_id": step.step_id,
                        "profile": profile,
                        "error": f"expected VaultInitStepResult, got {type(result).__name__}",
                    },
                ),
            )

        step_ids_executed.append(step.step_id)
        warnings.extend(result.warnings)
        for path in result.files_created:
            if path not in files_created and path not in existing_files:
                files_created.append(path)
        instructions.extend(_serialize_instruction(item) for item in result.instructions)

    return files_created, warnings, instructions, step_ids_executed


# ── TOML generation ──────────────────────────────────────────────────


def _generate_toml(*, name: str, profile: str, tone: str) -> str:
    """Generate a sparse ztlctl.toml with only the user-chosen overrides."""
    return (
        f'[vault]\nname = "{name}"\n\n'
        f'[workspace]\nprofile = "{profile}"\n\n'
        f'[agent]\ntone = "{tone}"\n'
    )


def _profile_error(
    *,
    op: str,
    code: str,
    message: str,
    requested_profile: str | None,
    registry_profiles: list[str],
    discovery_scope: str,
    vault_root: Path | None = None,
) -> ServiceResult:
    """Build a structured workspace-profile error result."""
    detail: dict[str, str | list[str]] = {
        "requested_profile": requested_profile or "",
        "available_profiles": registry_profiles,
        "discovery_scope": discovery_scope,
    }
    if vault_root is not None:
        detail["vault_root"] = str(vault_root)
    return ServiceResult(
        ok=False,
        op=op,
        error=ServiceError(code=code, message=message, detail=detail),
    )


# ── Public API ────────────────────────────────────────────────────────


class InitService:
    """Vault initialization and self-generation (all static methods)."""

    @staticmethod
    @traced
    def init_vault(
        path: Path,
        *,
        name: str,
        profile: str | None = None,
        client: str | None = None,
        tone: str = "research-partner",
        topics: list[str] | None = None,
        no_workflow: bool = False,
    ) -> ServiceResult:
        """Create a new ztlctl vault at *path*.

        Pipeline:
        1. VALIDATE — reject if ztlctl.toml already exists
        2. CREATE STRUCTURE — dirs from DESIGN.md Section 11
        3. GENERATE CONFIG — sparse ztlctl.toml
        4. INITIALIZE DB — SQLite + FTS5
        5. RENDER SELF — identity.md + methodology.md via Jinja2
        6. RUN INIT STEPS — ordered plugin steps plus legacy scaffold wrappers
        7. WORKFLOW — .ztlctl/workflow-answers.yml (unless --no-workflow)
        8. RESPOND — ServiceResult with created file manifest
        """
        vault_path = path.resolve()
        topics = topics or []
        profile_registry = discover_init_profiles()
        try:
            profile, selection_warnings, legacy_client = resolve_profile_selection(
                profile=profile,
                client=client,
                registry=profile_registry,
            )
        except UnknownWorkspaceProfileError as exc:
            requested = profile if profile is not None else client
            return _profile_error(
                op="init_vault",
                code="PROFILE_NOT_FOUND",
                message=str(exc),
                requested_profile=requested,
                registry_profiles=exc.available_profiles,
                discovery_scope="init",
            )
        except ValueError as exc:
            return ServiceResult(
                ok=False,
                op="init_vault",
                error=ServiceError(
                    code="INVALID_PROFILE",
                    message=str(exc),
                    detail={"profile": profile, "client": client},
                ),
            )

        # 1. VALIDATE
        toml_path = vault_path / "ztlctl.toml"
        if toml_path.exists():
            return ServiceResult(
                ok=False,
                op="init_vault",
                error=ServiceError(
                    code="VAULT_EXISTS",
                    message=f"Vault already exists at {vault_path}",
                    detail={"path": str(vault_path)},
                ),
            )

        files_created: list[str] = []
        warnings: list[str] = list(selection_warnings)
        profile_contribution = profile_registry.profiles[profile]
        setup_steps: list[dict[str, str | list[str]]] = []
        step_ids_executed: list[str] = []

        # 2. CREATE STRUCTURE
        dirs = [
            vault_path / ".ztlctl",
            vault_path / "self",
            vault_path / "notes",
            vault_path / "ops" / "logs",
            vault_path / "ops" / "tasks",
        ]
        for topic in topics:
            dirs.append(vault_path / "notes" / topic)
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        # 3. GENERATE CONFIG
        toml_content = _generate_toml(name=name, profile=profile, tone=tone)
        toml_path.write_text(toml_content, encoding="utf-8")
        files_created.append("ztlctl.toml")

        # 4. INITIALIZE DB
        from ztlctl.infrastructure.database.engine import init_database

        init_database(vault_path)
        files_created.append(".ztlctl/ztlctl.db")

        # 4b. STAMP ALEMBIC VERSION
        try:
            from ztlctl.infrastructure.database.migrations import stamp_head

            stamp_head(vault_path)
        except Exception as exc:
            warnings.append(f"Alembic stamp failed ({exc}); run 'ztlctl upgrade' to fix")

        # 5. RENDER SELF
        created = today_iso()
        rendered = _render_self_files(
            vault_name=name,
            tone=tone,
            profile=profile,
            client=legacy_client,
            topics=topics,
            created=created,
            vault_root=vault_path,
        )
        self_dir = vault_path / "self"
        for filename, content in rendered.items():
            (self_dir / filename).write_text(content, encoding="utf-8")
            files_created.append(f"self/{filename}")

        # 6. RUN INIT STEPS
        init_step_result = _run_init_steps(
            vault_path=vault_path,
            name=name,
            profile=profile,
            tone=tone,
            topics=topics,
            no_workflow=no_workflow,
            profile_registry=profile_registry,
            existing_files=files_created,
        )
        if isinstance(init_step_result, ServiceResult):
            return init_step_result.model_copy(
                update={"warnings": [*warnings, *init_step_result.warnings]}
            )
        step_files, step_warnings, setup_steps, step_ids_executed = init_step_result
        files_created.extend(step_files)
        warnings.extend(step_warnings)

        # 7. WORKFLOW
        if not no_workflow:
            from ztlctl.services.workflow import WorkflowService

            workflow_result = WorkflowService.init_workflow(
                vault_path,
                WorkflowService.default_choices(profile=profile),
            )
            if workflow_result.ok:
                files_created.extend(
                    [
                        path
                        for path in workflow_result.data.get("files_written", [])
                        if path not in files_created
                    ]
                )
            elif workflow_result.error is not None:
                warnings.append(
                    f"Workflow scaffolding skipped ({workflow_result.error.message}); "
                    "run 'ztlctl workflow init' to retry"
                )

        warnings.extend(
            _dispatch_post_init(
                vault_path=vault_path,
                name=name,
                profile=profile,
                client=legacy_client,
                tone=tone,
                managed_paths=list(profile_contribution.managed_paths),
            )
        )

        return ServiceResult(
            ok=True,
            op="init_vault",
            data={
                "vault_path": str(vault_path),
                "name": name,
                "profile": profile,
                "client": legacy_client,
                "tone": tone,
                "topics": topics,
                "files_created": files_created,
                "setup_steps": setup_steps,
                "step_ids_executed": step_ids_executed,
            },
            warnings=warnings,
        )

    @staticmethod
    @traced
    def regenerate_self(vault: Vault) -> ServiceResult:
        """Re-render self/ files from current vault settings.

        Reads config from the vault's ZtlSettings and overwrites
        self/identity.md and self/methodology.md with fresh renders.
        """
        config_path = vault.settings.config_path
        if config_path is None or not config_path.exists():
            return ServiceResult(
                ok=False,
                op="regenerate_self",
                error=ServiceError(
                    code="NO_CONFIG",
                    message="No ztlctl.toml found",
                ),
            )

        settings = vault.settings
        profile_registry = discover_vault_profiles(vault.root)
        try:
            resolved_profile, profile_warning = resolve_workspace_profile(
                settings.workspace.profile,
                profile_registry,
            )
        except UnknownWorkspaceProfileError as exc:
            return _profile_error(
                op="regenerate_self",
                code="PROFILE_NOT_FOUND",
                message=str(exc),
                requested_profile=exc.requested_profile,
                registry_profiles=exc.available_profiles,
                discovery_scope="vault",
                vault_root=vault.root,
            )

        self_dir = vault.root / "self"
        self_dir.mkdir(exist_ok=True)

        rendered = _render_self_files(
            vault_name=settings.vault.name,
            tone=settings.agent.tone,
            profile=resolved_profile,
            client=profile_to_legacy_client(resolved_profile),
            topics=[],  # topics are directory-based, not in config
            created=today_iso(),
            vault_root=vault.root,
        )

        files_written: list[str] = []
        changed: list[str] = []
        for filename, content in rendered.items():
            target = self_dir / filename
            old_content = target.read_text(encoding="utf-8") if target.exists() else ""
            target.write_text(content, encoding="utf-8")
            files_written.append(f"self/{filename}")
            if content != old_content:
                changed.append(filename)

        return ServiceResult(
            ok=True,
            op="regenerate_self",
            data={
                "files_written": files_written,
                "changed": changed,
                "vault_path": str(vault.root),
            },
            warnings=[
                *profile_registry.warnings,
                *([profile_warning] if profile_warning is not None else []),
            ],
        )

    @staticmethod
    @traced
    def check_staleness(vault: Vault) -> ServiceResult:
        """Compare ztlctl.toml mtime vs self/*.md mtimes.

        Returns stale=True if any self/ file is older than the config.
        """
        config_path = vault.root / "ztlctl.toml"
        self_dir = vault.root / "self"

        if not config_path.exists():
            return ServiceResult(
                ok=False,
                op="check_staleness",
                error=ServiceError(
                    code="NO_CONFIG",
                    message="No ztlctl.toml found",
                ),
            )

        config_mtime = os.path.getmtime(config_path)
        stale_files: list[str] = []

        for md_file in sorted(self_dir.glob("*.md")):
            if os.path.getmtime(md_file) < config_mtime:
                stale_files.append(md_file.name)

        return ServiceResult(
            ok=True,
            op="check_staleness",
            data={
                "stale": len(stale_files) > 0,
                "stale_files": stale_files,
                "config_mtime": config_mtime,
            },
        )
