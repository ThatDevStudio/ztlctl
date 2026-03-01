"""Typed plugin contribution contracts for public extension points."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

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
