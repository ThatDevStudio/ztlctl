"""Typed plugin contribution contracts for public extension points."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import click

from ztlctl.catalogs import ToolCatalogEntry


@dataclass(frozen=True)
class CliCommandContribution:
    """One plugin-provided CLI command."""

    name: str
    command: click.Command


@dataclass(frozen=True)
class McpToolContribution:
    """One plugin-provided MCP tool."""

    name: str
    handler: Callable[..., dict[str, Any]]
    catalog_entry: ToolCatalogEntry


@dataclass(frozen=True)
class McpResourceContribution:
    """One plugin-provided MCP resource."""

    uri: str
    description: str
    handler: Callable[[Any], Any]


@dataclass(frozen=True)
class McpPromptContribution:
    """One plugin-provided MCP prompt."""

    name: str
    description: str
    handler: Callable[..., str]
    takes_vault: bool = True


@dataclass(frozen=True)
class WorkflowModuleContribution:
    """One plugin-provided workflow export module."""

    name: str
    render: Callable[[dict[str, Any]], str]


@dataclass(frozen=True)
class WorkspaceProfileContribution:
    """One workspace profile definition exposed by core or plugins.

    ``managed_paths`` identifies the vault roots a profile scaffolds during init
    so ownership and post-init hooks can classify them. It does not imply that
    ztlctl will later validate or rewrite those files.
    """

    profile_id: str
    description: str
    aliases: tuple[str, ...] = ()
    managed_paths: tuple[str, ...] = ()
    init_scaffold: Callable[[Path], list[str]] | None = None


@dataclass(frozen=True)
class VaultInitContext:
    """Normalized context passed to plugin-contributed vault init steps."""

    vault_root: Path
    vault_name: str
    profile: str
    tone: str
    topics: tuple[str, ...] = ()
    no_workflow: bool = False


@dataclass(frozen=True)
class VaultInitInstruction:
    """One user-facing instruction emitted during vault initialization."""

    instruction_id: str
    title: str
    body: str
    items: tuple[str, ...] = ()
    kind: Literal["manual", "install", "verify"] = "manual"


@dataclass(frozen=True)
class VaultInitStepResult:
    """Files, warnings, and user-visible setup guidance from one init step."""

    files_created: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    instructions: tuple[VaultInitInstruction, ...] = ()


@dataclass(frozen=True)
class VaultInitStepContribution:
    """One plugin-contributed step in the ordered vault init pipeline."""

    step_id: str
    description: str
    run: Callable[[VaultInitContext], VaultInitStepResult]
    order: int = 500
    profiles: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceFetchRequest:
    """Normalized source-provider request."""

    content: str
    input_kind: str
    summary: str | None = None
    provider: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SourceFetchResult:
    """Normalized source-provider response."""

    body_text: str
    title: str | None = None
    canonical_url: str | None = None
    content_type: str | None = None
    language: str | None = None
    source_type: str | None = None
    summary_hint: str | None = None
    key_points: tuple[str, ...] = ()
    citations: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class SourceProviderContribution:
    """One plugin-provided source acquisition provider."""

    name: str
    description: str
    schemes: tuple[str, ...]
    fetch: Callable[[SourceFetchRequest], SourceFetchResult]


# ---------------------------------------------------------------------------
# Custom note type rendering (PLUG-06)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderContribution:
    """Plugin-provided rendering for a custom note type.

    Fields
    ------
    note_type
        The note type name this contribution applies to (e.g. ``"sprint"``).
    rich_formatter
        Callable that receives a ``dict[str, Any]`` of note data and returns
        a Rich-formatted string for terminal display.
    mcp_formatter
        Callable that receives a ``dict[str, Any]`` of note data and returns
        a ``dict[str, Any]`` suitable for MCP tool responses.
    """

    note_type: str
    rich_formatter: Callable[[dict[str, Any]], str]
    mcp_formatter: Callable[[dict[str, Any]], dict[str, Any]]


# ---------------------------------------------------------------------------
# Action hook contracts (PLUG-02)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ActionRejection:
    """Returned from ``pre_action`` to abort action execution.

    A plugin's ``pre_action`` implementation can return an instance of this
    class to prevent the registered action handler from running. The caller
    (BaseController._dispatch_pre_action) converts this into an appropriate
    error ServiceResult.
    """

    reason: str
    code: str = "plugin_rejected"
    detail: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Plugin marketplace metadata (PLUG-07)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PluginMetadata:
    """Structured metadata from ``[tool.ztlctl-plugin]`` in a plugin's pyproject.toml.

    Used for future plugin discoverability and marketplace listing. Plugin
    authors include this section in their ``pyproject.toml`` to declare
    compatibility and capabilities.

    Fields
    ------
    name
        Plugin display name.
    version
        Plugin version string (e.g. ``"1.0.0"``).
    author
        Author or organization name.
    capabilities
        Tuple of capability identifiers the plugin provides
        (e.g. ``("register_note_types", "register_cli_commands")``).
    ztlctl_api_version
        The ``PLUGIN_API_VERSION`` integer this plugin was built against.
    description
        Optional human-readable description.
    """

    name: str
    version: str
    author: str
    capabilities: tuple[str, ...]
    ztlctl_api_version: int
    description: str = ""
