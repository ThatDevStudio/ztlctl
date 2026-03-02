"""InitService — vault initialization and self-generation.

Unlike other services, InitService does NOT extend BaseService because it
operates *before* a Vault exists.  All public methods are @staticmethod
(init_vault) or take a Vault parameter (regenerate_self, check_staleness).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from ztlctl.infrastructure.templates import build_template_environment
from ztlctl.services._helpers import today_iso
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced
from ztlctl.workspace_profiles import (
    UnknownWorkspaceProfileError,
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
        6. APPLY PROFILE SCAFFOLD — profile-managed files such as .obsidian/snippets/ztlctl.css
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

        # 6. APPLY PROFILE SCAFFOLD
        if profile_contribution.init_scaffold is not None:
            try:
                files_created.extend(profile_contribution.init_scaffold(vault_path))
            except Exception as exc:
                return ServiceResult(
                    ok=False,
                    op="init_vault",
                    error=ServiceError(
                        code="PROFILE_SCAFFOLD_FAILED",
                        message=(
                            f"Workspace profile `{profile}` failed during scaffold setup: {exc}"
                        ),
                        detail={
                            "profile": profile,
                            "managed_paths": list(profile_contribution.managed_paths),
                            "error": str(exc),
                        },
                    ),
                    warnings=warnings,
                )

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
