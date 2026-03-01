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


_CLI_COMMAND_CATALOG: tuple[CliCommandCatalogEntry, ...] = (
    {"name": "agent", "kind": "group", "summary": "Manage sessions, context, and agent workflows."},
    {"name": "archive", "kind": "command", "summary": "Archive a content item by ID."},
    {"name": "check", "kind": "command", "summary": "Check vault integrity and repair issues."},
    {"name": "create", "kind": "group", "summary": "Create notes, references, and tasks."},
    {"name": "export", "kind": "group", "summary": "Export vault content and dashboards."},
    {
        "name": "extract",
        "kind": "command",
        "summary": "Extract a decision note from a session log.",
    },
    {"name": "garden", "kind": "group", "summary": "Cultivate knowledge with the garden persona."},
    {"name": "graph", "kind": "group", "summary": "Traverse and analyze the knowledge graph."},
    {
        "name": "ingest",
        "kind": "group",
        "summary": "Ingest text and source material into the vault.",
    },
    {"name": "init", "kind": "command", "summary": "Initialize a new ztlctl vault."},
    {"name": "query", "kind": "group", "summary": "Search, list, and query vault content."},
    {"name": "reweave", "kind": "command", "summary": "Densify the knowledge graph with links."},
    {"name": "serve", "kind": "command", "summary": "Start the MCP server."},
    {"name": "supersede", "kind": "command", "summary": "Supersede an accepted decision."},
    {"name": "update", "kind": "command", "summary": "Update content metadata or body."},
    {"name": "upgrade", "kind": "command", "summary": "Run pending database migrations."},
    {"name": "vector", "kind": "group", "summary": "Manage semantic search indexing."},
    {"name": "workflow", "kind": "group", "summary": "Manage workflow templates and exports."},
)


def cli_command_catalog() -> tuple[CliCommandCatalogEntry, ...]:
    """Return the core CLI command catalog."""
    return _CLI_COMMAND_CATALOG


def mcp_tool_catalog(vault: object | None = None) -> tuple[ToolCatalogEntry, ...]:
    """Return the authoritative MCP tool catalog."""
    from ztlctl.mcp.tools import tool_catalog

    return tool_catalog(vault)


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
