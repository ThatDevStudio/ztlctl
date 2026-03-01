"""WorkflowService — Copier-backed workflow scaffolding for vaults."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Any, Literal, cast

from copier import run_copy, run_recopy, run_update
from copier.errors import CopierError
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

from ztlctl.catalogs import (
    mcp_prompt_catalog,
    mcp_resource_catalog,
    mcp_tool_catalog,
    workflow_asset_manifest,
)
from ztlctl.infrastructure.templates import build_template_environment
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced

WorkflowMode = Literal["claude-driven", "agent-generic", "manual"]
SkillSet = Literal["research", "engineering", "minimal"]
SourceControl = Literal["git", "none"]
Viewer = Literal["obsidian", "vanilla"]
WorkflowAssetClient = Literal["claude", "codex", "both"]

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
_ASSET_CLIENT_VALUES = {"claude", "codex", "both"}


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
    def _agent_template_root() -> Traversable:
        """Return the packaged cross-client workflow template root."""
        return resources.files("ztlctl").joinpath("templates/agent_workflow")

    @staticmethod
    def _load_agent_manifest() -> dict[str, Any]:
        """Load the packaged agent workflow manifest."""
        return cast(dict[str, Any], workflow_asset_manifest())

    @staticmethod
    def _load_plugin_manager(vault_root: Path) -> Any | None:
        """Load plugin contributions for workflow export and validation."""
        from ztlctl.plugins.manager import PluginManager

        pm = PluginManager()
        pm.discover_and_load(local_dir=vault_root / ".ztlctl" / "plugins")
        return pm

    @staticmethod
    def _surface_catalogs(vault_root: Path) -> dict[str, Any]:
        """Build plugin-aware public surface catalogs for a vault root."""
        plugin_manager = WorkflowService._load_plugin_manager(vault_root)

        tools = list(mcp_tool_catalog())
        resources_catalog = list(mcp_resource_catalog())
        prompts = list(mcp_prompt_catalog())
        workflow_modules: dict[str, Any] = {}

        if plugin_manager is not None:
            tool_reserved = {entry["name"] for entry in tools}
            resource_reserved = {entry["uri"] for entry in resources_catalog}
            prompt_reserved = {entry["name"] for entry in prompts}
            for contribution in plugin_manager.mcp_tool_contributions(reserved_names=tool_reserved):
                tools.append(contribution.catalog_entry)
            for contribution in plugin_manager.mcp_resource_contributions(
                reserved_uris=resource_reserved
            ):
                resources_catalog.append(
                    {"uri": contribution.uri, "description": contribution.description}
                )
            for contribution in plugin_manager.mcp_prompt_contributions(
                reserved_names=prompt_reserved
            ):
                prompts.append({"name": contribution.name, "description": contribution.description})
            workflow_modules = {
                contribution.name: contribution.render
                for contribution in plugin_manager.workflow_module_contributions()
            }

        return {
            "tools": tools,
            "resources": resources_catalog,
            "prompts": prompts,
            "workflow_modules": workflow_modules,
        }

    @staticmethod
    def _selected_clients(client: WorkflowAssetClient) -> list[str]:
        """Expand the client selector into concrete client names."""
        if client not in _ASSET_CLIENT_VALUES:
            msg = f"Unsupported client export target: {client}"
            raise ValueError(msg)
        return ["claude", "codex"] if client == "both" else [client]

    @staticmethod
    def _asset_context(vault_root: Path) -> dict[str, Any]:
        """Build the render context for portable workflow assets."""
        env = build_template_environment("agent_workflow", vault_root=vault_root)
        manifest = WorkflowService._load_agent_manifest()
        surfaces = WorkflowService._surface_catalogs(vault_root)
        tool_names = [entry["name"] for entry in surfaces["tools"]]
        resource_names = [entry["uri"] for entry in surfaces["resources"]]
        prompt_names = [entry["name"] for entry in surfaces["prompts"]]
        context: dict[str, Any] = {
            "tool_names": tool_names,
            "resource_names": resource_names,
            "prompt_names": prompt_names,
            "tool_count": len(tool_names),
            "resource_count": len(resource_names),
            "prompt_count": len(prompt_names),
            "vault_name": vault_root.name,
        }
        modules: dict[str, str] = {}
        shared = manifest.get("shared_modules", {})
        for module_name, template_name in shared.items():
            modules[module_name] = env.get_template(str(template_name)).render(**context).strip()
        for module_name, render in surfaces["workflow_modules"].items():
            if module_name in modules:
                continue
            modules[module_name] = str(render(context)).strip()
        context["modules"] = modules
        return context

    @staticmethod
    def _write_asset(path: Path, content: str, *, executable: bool = False) -> None:
        """Write a rendered asset file and apply executable permissions when needed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")
        if executable:
            path.chmod(0o755)

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
    def validate_export_target(vault_root: Path, *, op: str) -> ServiceResult | None:
        """Validate that workflow assets can be exported or validated for a vault."""
        vault_root = vault_root.resolve()
        return WorkflowService._validate_vault_root(vault_root, op=op)

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

    @staticmethod
    @traced
    def export_assets(vault_root: Path, *, client: WorkflowAssetClient = "both") -> ServiceResult:
        """Render portable client workflow assets into a vault."""
        vault_root = vault_root.resolve()
        validation_error = WorkflowService.validate_export_target(vault_root, op="workflow_export")
        if validation_error is not None:
            return validation_error

        manifest = WorkflowService._load_agent_manifest()
        env = build_template_environment("agent_workflow", vault_root=vault_root)
        context = WorkflowService._asset_context(vault_root)
        files_written: list[str] = []
        selected = WorkflowService._selected_clients(client)

        for client_name in selected:
            client_spec = manifest["clients"][client_name]
            for file_spec in client_spec["files"]:
                template = env.get_template(str(file_spec["template"]))
                rendered = template.render(**context)
                output_path = vault_root / str(file_spec["output"])
                WorkflowService._write_asset(
                    output_path,
                    rendered,
                    executable=bool(file_spec.get("executable", False)),
                )
                files_written.append(str(file_spec["output"]))

        return ServiceResult(
            ok=True,
            op="workflow_export",
            data={
                "vault_path": str(vault_root),
                "clients": selected,
                "files_written": files_written,
            },
        )

    @staticmethod
    def _validate_json_schema(path: Path, schema_name: str, errors: list[str]) -> None:
        """Validate a generated JSON config file against a minimal schema."""
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{path}: invalid JSON ({exc})")
            return

        if schema_name == "mcp_config":
            server = payload.get("mcpServers", {}).get("ztlctl")
            if not isinstance(server, dict):
                errors.append(f"{path}: missing mcpServers.ztlctl")
                return
            if server.get("command") != "ztlctl":
                errors.append(f"{path}: mcpServers.ztlctl.command must be 'ztlctl'")
            args = server.get("args")
            if not isinstance(args, list) or "serve" not in args:
                errors.append(f"{path}: mcpServers.ztlctl.args must include 'serve'")
            return

        if schema_name == "claude_settings":
            hooks = payload.get("hooks")
            if not isinstance(hooks, dict):
                errors.append(f"{path}: missing top-level 'hooks' object")
                return
            session_start = hooks.get("SessionStart")
            if not isinstance(session_start, list) or not session_start:
                errors.append(f"{path}: hooks.SessionStart must be a non-empty list")
                return
            first_rule = session_start[0]
            rule_hooks = first_rule.get("hooks") if isinstance(first_rule, dict) else None
            if not isinstance(rule_hooks, list) or not rule_hooks:
                errors.append(f"{path}: hooks.SessionStart[0].hooks must be a non-empty list")
                return
            first_hook = rule_hooks[0]
            if not isinstance(first_hook, dict) or first_hook.get("type") != "command":
                errors.append(f"{path}: first SessionStart hook must be a command hook")
                return
            command = str(first_hook.get("command", ""))
            if ".claude/hooks/session-context.sh" not in command:
                errors.append(f"{path}: SessionStart hook must invoke session-context.sh")

    @staticmethod
    @traced
    def validate_assets(vault_root: Path, *, client: WorkflowAssetClient = "both") -> ServiceResult:
        """Validate the packaged workflow spec and generated client assets."""
        vault_root = vault_root.resolve()
        validation_error = WorkflowService.validate_export_target(
            vault_root, op="workflow_validate"
        )
        if validation_error is not None:
            return validation_error

        manifest = WorkflowService._load_agent_manifest()
        surfaces = WorkflowService._surface_catalogs(vault_root)
        available_tools = {entry["name"] for entry in surfaces["tools"]}
        available_resources = {entry["uri"] for entry in surfaces["resources"]}
        available_prompts = {entry["name"] for entry in surfaces["prompts"]}
        selected = WorkflowService._selected_clients(client)

        errors: list[str] = []
        warnings: list[str] = []
        validated_files = 0
        seen_outputs: set[str] = set()

        for client_name in selected:
            client_spec = manifest["clients"][client_name]
            for file_spec in client_spec["files"]:
                output_name = str(file_spec["output"])
                if output_name in seen_outputs:
                    errors.append(f"Duplicate generated asset output: {output_name}")
                seen_outputs.add(output_name)
                for tool_name in file_spec.get("tools", []):
                    if tool_name not in available_tools:
                        errors.append(f"{file_spec['output']}: unknown MCP tool '{tool_name}'")
                for resource_uri in file_spec.get("resources", []):
                    if resource_uri not in available_resources:
                        errors.append(
                            f"{file_spec['output']}: unknown MCP resource '{resource_uri}'"
                        )
                for prompt_name in file_spec.get("prompts", []):
                    if prompt_name not in available_prompts:
                        errors.append(f"{file_spec['output']}: unknown MCP prompt '{prompt_name}'")

                template_path = WorkflowService._agent_template_root().joinpath(
                    str(file_spec["template"])
                )
                if not template_path.is_file():
                    errors.append(f"Missing packaged template: {file_spec['template']}")

                output_path = vault_root / str(file_spec["output"])
                if not output_path.exists():
                    errors.append(f"Missing generated asset: {file_spec['output']}")
                    continue

                validated_files += 1
                if output_path.read_text(encoding="utf-8").strip() == "":
                    warnings.append(f"{file_spec['output']}: generated file is empty")

                schema_name = file_spec.get("schema")
                if isinstance(schema_name, str):
                    WorkflowService._validate_json_schema(output_path, schema_name, errors)

        if errors:
            return ServiceResult(
                ok=False,
                op="workflow_validate",
                error=ServiceError(
                    code="WORKFLOW_VALIDATION_FAILED",
                    message="Workflow assets failed validation",
                    detail={"issues": errors},
                ),
                warnings=warnings,
            )

        return ServiceResult(
            ok=True,
            op="workflow_validate",
            data={
                "vault_path": str(vault_root),
                "clients": selected,
                "validated_files": validated_files,
            },
            warnings=warnings,
        )
