"""Shared catalogs for public ztlctl surfaces.

This module provides a single access path for runtime metadata about the
CLI, MCP surfaces, and workflow-export assets. Individual modules remain
free to own their implementation details, but validation, docs, and
workflow export should consume these helpers instead of importing each
surface directly.
"""

from __future__ import annotations

import json
from importlib import resources
from typing import Literal, TypedDict, cast

ToolSideEffect = Literal["read", "write"]


class CliCommandCatalogEntry(TypedDict):
    """One externally exposed CLI command or command group."""

    name: str
    kind: Literal["group", "command"]
    summary: str


class ToolCatalogEntry(TypedDict):
    """One MCP tool contract entry."""

    name: str
    category: str
    description: str
    when_to_use: str
    avoid_when: str
    side_effect: ToolSideEffect
    common_errors: tuple[str, ...]
    args_guidance: dict[str, str]


class ResourceCatalogEntry(TypedDict):
    """One MCP resource contract entry."""

    uri: str
    description: str


class PromptCatalogEntry(TypedDict):
    """One MCP prompt contract entry."""

    name: str
    description: str


class WorkflowAssetFileSpec(TypedDict, total=False):
    """One exported workflow asset entry."""

    template: str
    output: str
    schema: str
    executable: bool
    tools: list[str]
    resources: list[str]
    prompts: list[str]


class WorkflowAssetClientSpec(TypedDict):
    """Workflow export files for one client."""

    files: list[WorkflowAssetFileSpec]


class WorkflowAssetManifest(TypedDict):
    """Packaged workflow export manifest."""

    shared_modules: dict[str, str]
    clients: dict[str, WorkflowAssetClientSpec]


def cli_command_catalog() -> tuple[CliCommandCatalogEntry, ...]:
    """Return the core CLI command catalog, derived from ActionRegistry."""
    import ztlctl.actions  # noqa: F401 — ensure registry populated
    from ztlctl.actions.registry import get_action_registry

    registry = get_action_registry()
    seen_groups: set[str] = set()
    entries: list[CliCommandCatalogEntry] = []

    for action in registry.list_actions():
        if action.cli_group and action.cli_group not in seen_groups:
            seen_groups.add(action.cli_group)
            entries.append(
                {
                    "name": action.cli_group,
                    "kind": "group",
                    "summary": action.description,  # First action in group
                }
            )
        elif action.cli_group is None and not action.custom_presentation:
            entries.append(
                {
                    "name": action.name.replace("_", "-"),
                    "kind": "command",
                    "summary": action.description,
                }
            )

    # Add custom_presentation entries that don't come from registry iteration
    for name, kind, summary in [
        ("garden", "group", "Cultivate knowledge with the garden persona."),
        ("init", "command", "Initialize a new ztlctl vault."),
        ("serve", "command", "Start the MCP server."),
        ("update", "command", "Update content metadata or body."),
        ("workflow", "group", "Manage workflow templates and exports."),
    ]:
        if name not in seen_groups and not any(e["name"] == name for e in entries):
            entries.append({"name": name, "kind": kind, "summary": summary})  # type: ignore[typeddict-item]

    return tuple(sorted(entries, key=lambda e: e["name"]))


def mcp_tool_catalog(vault: object | None = None) -> tuple[ToolCatalogEntry, ...]:
    """Return the authoritative MCP tool catalog."""
    from ztlctl.mcp.generator import tool_catalog

    return tool_catalog(vault)  # type: ignore[return-value]


def mcp_resource_catalog(vault: object | None = None) -> tuple[ResourceCatalogEntry, ...]:
    """Return the authoritative MCP resource catalog."""
    from ztlctl.mcp.resources import resource_catalog

    return cast(tuple[ResourceCatalogEntry, ...], resource_catalog(vault))


def mcp_prompt_catalog(vault: object | None = None) -> tuple[PromptCatalogEntry, ...]:
    """Return the authoritative MCP prompt catalog."""
    from ztlctl.mcp.prompts import prompt_catalog

    return cast(tuple[PromptCatalogEntry, ...], prompt_catalog(vault))


def workflow_asset_manifest() -> WorkflowAssetManifest:
    """Return the packaged workflow-export manifest."""
    manifest = resources.files("ztlctl").joinpath("templates/agent_workflow/manifest.json")
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = "Workflow asset manifest must be a JSON object"
        raise ValueError(msg)
    return cast(WorkflowAssetManifest, payload)


def workflow_asset_catalog() -> tuple[WorkflowAssetFileSpec, ...]:
    """Flatten the packaged workflow-export files across all clients."""
    manifest = workflow_asset_manifest()
    files: list[WorkflowAssetFileSpec] = []
    for client_spec in manifest["clients"].values():
        files.extend(client_spec.get("files", []))
    return tuple(files)
