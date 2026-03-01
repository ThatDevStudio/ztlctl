"""MCP tool definitions — core tools across 7 categories.

Categories: Discovery, Creation, Lifecycle, Query, Graph, Session, Analysis.
Each tool has a ``_<name>_impl`` function testable without the mcp package.
``register_tools()`` wraps them with FastMCP decorators.
(DESIGN.md Section 16)
"""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any, Literal, TypedDict

from ztlctl.services.contracts import (
    AgentContextFallbackData,
    AgentContextResultData,
    dump_validated,
)
from ztlctl.services.result import ServiceResult

ToolSideEffect = Literal["read", "write"]


class ToolCatalogEntry(TypedDict):
    """Authoritative MCP tool guidance used for registration and docs."""

    name: str
    category: str
    description: str
    when_to_use: str
    avoid_when: str
    side_effect: ToolSideEffect
    common_errors: tuple[str, ...]
    args_guidance: dict[str, str]


def _tool_entry(
    *,
    name: str,
    category: str,
    description: str,
    when_to_use: str,
    avoid_when: str,
    side_effect: ToolSideEffect,
    common_errors: tuple[str, ...] = (),
    args_guidance: dict[str, str] | None = None,
) -> ToolCatalogEntry:
    """Create a typed MCP catalog entry."""
    return {
        "name": name,
        "category": category,
        "description": description,
        "when_to_use": when_to_use,
        "avoid_when": avoid_when,
        "side_effect": side_effect,
        "common_errors": common_errors,
        "args_guidance": args_guidance or {},
    }


COMMON_ERROR_RECOVERY: dict[str, str] = {
    "NOT_FOUND": "Verify the target ID with search(), list_items(), or get_document().",
    "VALIDATION_FAILED": (
        "Check required params and field types. Titles must be non-empty and statuses must use "
        "supported values."
    ),
    "ID_COLLISION": (
        "Search for the existing item first, then update it or choose a different title."
    ),
    "NO_ACTIVE_SESSION": "Start a session with create_log(topic) before calling session tools.",
    "ACTIVE_SESSION_EXISTS": (
        "Use session_status() to inspect the active session or close it before starting another."
    ),
    "INVALID_TRANSITION": "Inspect the current item with get_document() before changing status.",
    "EMPTY_QUERY": "Provide a non-empty search string or use list_items() for browsing.",
    "UNKNOWN_TYPE": "Use a supported content type/subtype combination or omit subtype if unsure.",
    "NO_PATH": "Confirm both IDs exist and are connected before requesting a graph path.",
}

_TOOL_CATALOG: tuple[ToolCatalogEntry, ...] = (
    _tool_entry(
        name="discover_tools",
        category="discovery",
        description="List available MCP tools grouped by category.",
        when_to_use="Starting a session or narrowing the available tool surface by category.",
        avoid_when="You already know the tool name and need its contract details.",
        side_effect="read",
        args_guidance={
            "category": (
                "Optional category filter: discovery, creation, lifecycle, query, graph, "
                "session, or analysis."
            ),
        },
    ),
    _tool_entry(
        name="list_tags",
        category="discovery",
        description="List known tags with usage counts.",
        when_to_use="Before creating content, to reuse existing tag conventions and avoid drift.",
        avoid_when="You are searching for content rather than tag taxonomy.",
        side_effect="read",
        args_guidance={
            "prefix": "Optional tag prefix to filter results, such as research/ or project/.",
            "limit": "Maximum number of tags to return.",
        },
    ),
    _tool_entry(
        name="list_source_providers",
        category="discovery",
        description="List registered source providers available for URL ingestion.",
        when_to_use="Before ingesting URLs or when diagnosing missing provider support.",
        avoid_when="You already know the provider you need and are ingesting text or files.",
        side_effect="read",
        args_guidance={},
    ),
    _tool_entry(
        name="create_note",
        category="creation",
        description="Create a new note.",
        when_to_use="Capturing a synthesized idea, knowledge note, decision, or observation.",
        avoid_when="You only need a quick raw capture or a source record.",
        side_effect="write",
        common_errors=("VALIDATION_FAILED", "ID_COLLISION", "UNKNOWN_TYPE"),
        args_guidance={
            "title": "Human-readable note title; used for ID generation and search.",
            "subtype": "Optional note subtype such as decision or knowledge.",
            "tags": "Optional tags. Domain/scope tags are recommended; unscoped tags only warn.",
            "topic": "Optional topic directory under notes/.",
            "body": "Optional markdown body for synthesized content.",
            "key_points": "Optional short bullet-style summary items.",
            "links": "Optional explicit edge map keyed by relation type.",
            "aliases": "Optional alternate names for search and linking.",
        },
    ),
    _tool_entry(
        name="create_reference",
        category="creation",
        description="Create a new reference.",
        when_to_use="Logging an external source such as an article, paper, or spec.",
        avoid_when="The content is your own synthesis rather than an external source.",
        side_effect="write",
        common_errors=("VALIDATION_FAILED", "ID_COLLISION", "UNKNOWN_TYPE"),
        args_guidance={
            "title": "Reference title as it should appear in the vault.",
            "url": "Optional canonical source URL.",
            "subtype": "Optional reference subtype such as spec.",
            "tags": "Optional tags for source categorization.",
            "topic": "Optional topic directory under notes/.",
        },
    ),
    _tool_entry(
        name="create_task",
        category="creation",
        description="Create a new task.",
        when_to_use="Tracking actionable work that should appear in the prioritized queue.",
        avoid_when="You are capturing knowledge or a session log rather than executable work.",
        side_effect="write",
        common_errors=("VALIDATION_FAILED", "ID_COLLISION"),
        args_guidance={
            "title": "Task title phrased as concrete work.",
            "priority": "Priority bucket such as low, medium, or high.",
            "impact": "Expected impact bucket used in queue scoring.",
            "effort": "Estimated effort bucket used in queue scoring.",
            "tags": "Optional tags for routing and filtering.",
        },
    ),
    _tool_entry(
        name="create_log",
        category="creation",
        description="Start a new session.",
        when_to_use="Beginning a focused work session that should be tracked in the vault.",
        avoid_when="A session is already active.",
        side_effect="write",
        common_errors=("ACTIVE_SESSION_EXISTS",),
        args_guidance={
            "topic": "Short session topic used for tracking and later context assembly.",
        },
    ),
    _tool_entry(
        name="update_content",
        category="lifecycle",
        description="Update a content item.",
        when_to_use=(
            "Changing fields on an existing item, including title, tags, topic, body, or status."
        ),
        avoid_when="You need to archive the item or create a new one instead.",
        side_effect="write",
        common_errors=("NOT_FOUND", "VALIDATION_FAILED", "INVALID_TRANSITION", "UNKNOWN_TYPE"),
        args_guidance={
            "content_id": "Existing vault ID to modify.",
            "changes": "Partial field map to merge into frontmatter and content.",
        },
    ),
    _tool_entry(
        name="close_content",
        category="lifecycle",
        description="Archive or close a content item.",
        when_to_use="Marking an item complete or archived.",
        avoid_when="You only need to edit fields without changing lifecycle state.",
        side_effect="write",
        common_errors=("NOT_FOUND",),
        args_guidance={
            "content_id": "Existing vault ID to archive or close.",
        },
    ),
    _tool_entry(
        name="reweave",
        category="lifecycle",
        description="Run reweave on content.",
        when_to_use="After creating or updating content, to discover and add useful links.",
        avoid_when="The vault is still too small for meaningful graph-based suggestions.",
        side_effect="write",
        common_errors=("NOT_FOUND",),
        args_guidance={
            "content_id": "Optional target item ID. Omit to run across the broader vault.",
            "dry_run": "Set true to preview suggestions without mutating the vault.",
        },
    ),
    _tool_entry(
        name="search",
        category="query",
        description="Full-text search.",
        when_to_use="Finding content by keywords with optional type, tag, or space filters.",
        avoid_when="You already have an exact ID or only need a filtered listing.",
        side_effect="read",
        common_errors=("EMPTY_QUERY",),
        args_guidance={
            "query": "Non-empty search string.",
            "content_type": "Optional filter such as note, reference, task, or log.",
            "tag": "Optional tag filter.",
            "space": "Optional space filter if the vault uses spaces.",
            "rank_by": "Ranking mode such as relevance, recency, graph, semantic, or hybrid.",
            "limit": "Maximum number of results to return.",
        },
    ),
    _tool_entry(
        name="get_document",
        category="query",
        description="Get a document by ID.",
        when_to_use="Retrieving the full content of a known item.",
        avoid_when="You still need to discover the correct target item.",
        side_effect="read",
        common_errors=("NOT_FOUND",),
        args_guidance={
            "content_id": "Exact vault ID to fetch.",
        },
    ),
    _tool_entry(
        name="get_related",
        category="query",
        description="Get related content via graph traversal.",
        when_to_use="Exploring neighbors and nearby graph context from a known starting item.",
        avoid_when="You need keyword search rather than graph traversal.",
        side_effect="read",
        common_errors=("NOT_FOUND",),
        args_guidance={
            "content_id": "Starting vault ID for traversal.",
            "depth": "Traversal depth; higher values broaden the neighborhood.",
            "top": "Maximum related items to return.",
        },
    ),
    _tool_entry(
        name="agent_context",
        category="query",
        description="Build agent context from vault state.",
        when_to_use=(
            "Assembling a read-only snapshot of recent items, search results, and work queue."
        ),
        avoid_when="You only need a single document or single-purpose query result.",
        side_effect="read",
        args_guidance={
            "query": "Optional topic or query to enrich the context snapshot.",
            "limit": "Maximum items to include per section in the fallback context.",
        },
    ),
    _tool_entry(
        name="session_close",
        category="session",
        description="Close the active session.",
        when_to_use="Ending a tracked work session and triggering session enrichment.",
        avoid_when="No session is active.",
        side_effect="write",
        common_errors=("NO_ACTIVE_SESSION",),
        args_guidance={
            "summary": "Optional end-of-session summary for the log.",
        },
    ),
    _tool_entry(
        name="session_status",
        category="session",
        description="Get the active session, if any.",
        when_to_use="Checking whether a session is open and what it is tracking.",
        avoid_when="You need the full vault context rather than session state.",
        side_effect="read",
        args_guidance={},
    ),
    _tool_entry(
        name="list_items",
        category="query",
        description=(
            "List vault items with filtering by type, status, tag, topic, maturity, and sort."
        ),
        when_to_use="Browsing and filtering the vault without keyword search.",
        avoid_when="You need ranked full-text results or a single exact document.",
        side_effect="read",
        args_guidance={
            "content_type": "Optional type filter such as note, reference, task, or log.",
            "status": "Optional status filter.",
            "tag": "Optional tag filter.",
            "topic": "Optional topic filter.",
            "subtype": "Optional subtype filter.",
            "maturity": "Optional maturity filter for garden notes.",
            "space": "Optional space filter.",
            "since": "Optional lower bound timestamp or date string.",
            "include_archived": "Set true to include archived items.",
            "sort": "Sort mode such as recency.",
            "limit": "Maximum number of items to return.",
        },
    ),
    _tool_entry(
        name="work_queue",
        category="query",
        description="Get prioritized actionable tasks.",
        when_to_use="Finding the next task to work on from the scored queue.",
        avoid_when="You are looking for notes, references, or broad listings.",
        side_effect="read",
        args_guidance={
            "space": "Optional space filter for scoped task queues.",
        },
    ),
    _tool_entry(
        name="decision_support",
        category="analysis",
        description="Aggregate decision context for a topic.",
        when_to_use="Preparing to make or document a decision with nearby vault evidence.",
        avoid_when="Simple search is enough or the topic has no existing vault content.",
        side_effect="read",
        args_guidance={
            "topic": "Topic to analyze.",
            "space": "Optional space filter.",
        },
    ),
    _tool_entry(
        name="vault_review",
        category="analysis",
        description="Build a review-ready vault health snapshot.",
        when_to_use="Periodic maintenance, triage, and identifying stale or weakly linked areas.",
        avoid_when="You only need a focused document lookup.",
        side_effect="read",
        args_guidance={
            "top": "Maximum items to include in each ranked section.",
            "stale_days": "Age threshold for stale-item reporting.",
        },
    ),
    _tool_entry(
        name="graph_themes",
        category="graph",
        description="Detect knowledge communities via graph clustering.",
        when_to_use="Discovering higher-level topic clusters in a sufficiently connected vault.",
        avoid_when="The graph is still sparse or newly created.",
        side_effect="read",
        args_guidance={},
    ),
    _tool_entry(
        name="graph_rank",
        category="graph",
        description="Rank content by importance via PageRank.",
        when_to_use="Finding the most central nodes in the knowledge graph.",
        avoid_when="The vault has few items or very few edges.",
        side_effect="read",
        args_guidance={
            "top": "Maximum number of ranked items to return.",
        },
    ),
    _tool_entry(
        name="graph_path",
        category="graph",
        description="Find the connection path between two items.",
        when_to_use="Tracing how two specific items are connected.",
        avoid_when="You do not yet know both target IDs.",
        side_effect="read",
        common_errors=("NOT_FOUND", "NO_PATH"),
        args_guidance={
            "source_id": "Starting item ID.",
            "target_id": "Ending item ID.",
        },
    ),
    _tool_entry(
        name="graph_gaps",
        category="graph",
        description="Identify structural holes in the knowledge graph.",
        when_to_use="Looking for disconnected or weakly connected areas that need linking.",
        avoid_when="The vault is small enough that graph gaps are not yet meaningful.",
        side_effect="read",
        args_guidance={
            "top": "Maximum number of gap candidates to return.",
        },
    ),
    _tool_entry(
        name="graph_bridges",
        category="graph",
        description="Find bridge notes via betweenness centrality.",
        when_to_use="Identifying items that connect otherwise separate knowledge clusters.",
        avoid_when="The graph is too small to produce meaningful bridge nodes.",
        side_effect="read",
        args_guidance={
            "top": "Maximum number of bridge candidates to return.",
        },
    ),
    _tool_entry(
        name="garden_seed",
        category="creation",
        description="Quick-capture a seed note with minimal ceremony.",
        when_to_use="Capturing a raw idea or fleeting thought as fast as possible.",
        avoid_when="The idea is already well formed and deserves a full note.",
        side_effect="write",
        common_errors=("VALIDATION_FAILED", "ID_COLLISION"),
        args_guidance={
            "title": "Short seed title for the captured idea.",
            "tags": "Optional tags. Domain/scope is recommended but not required.",
            "topic": "Optional topic directory under notes/.",
        },
    ),
    _tool_entry(
        name="ingest_source",
        category="creation",
        description="Normalize text, files, or provider-backed URLs into notes or references.",
        when_to_use="Capturing external text or source material with provenance and structure.",
        avoid_when="You are authoring a note or reference directly without source normalization.",
        side_effect="write",
        common_errors=("VALIDATION_FAILED", "NO_PROVIDER", "NOT_FOUND", "UNKNOWN_TYPE"),
        args_guidance={
            "input_kind": "One of text, file, or url.",
            "content": "Raw text, a filesystem path, or a URL depending on input_kind.",
            "target_type": "Destination artifact type: reference or note.",
            "provider": "Optional provider name for URL ingestion.",
            "topic": "Optional topic directory under notes/.",
            "tags": "Optional tags applied to the created artifact.",
            "summary": "Optional capture summary hint for the created reference.",
            "dry_run": "Set true to preview normalized capture without writing files.",
        },
    ),
    _tool_entry(
        name="describe_tool",
        category="discovery",
        description="Get detailed usage guidance for a single tool by name.",
        when_to_use="You know the tool name but want the contract before calling it.",
        avoid_when="You already understand the tool or still need to discover candidates.",
        side_effect="read",
        common_errors=("NOT_FOUND",),
        args_guidance={
            "name": "Exact tool name to describe.",
        },
    ),
    _tool_entry(
        name="topic_packet",
        category="query",
        description="Assemble a topic-scoped packet for learning, review, or decision support.",
        when_to_use=(
            "You need a conversational, topic-focused retrieval bundle without an active session."
        ),
        avoid_when="A single document lookup or plain search result list is sufficient.",
        side_effect="read",
        args_guidance={
            "topic": "Topic name or query anchor for the packet.",
            "mode": "Packet mode: learn, review, or decision.",
            "budget": "Approximate token budget for assembled results.",
        },
    ),
)

_TOOL_CATALOG_BY_NAME: dict[str, ToolCatalogEntry] = {tool["name"]: tool for tool in _TOOL_CATALOG}


def tool_catalog(vault: Any | None = None) -> tuple[ToolCatalogEntry, ...]:
    """Return the MCP tool catalog for validation and docs."""
    catalog = list(_TOOL_CATALOG)
    plugin_manager = getattr(vault, "plugin_manager", None) if vault is not None else None
    if plugin_manager is None:
        return tuple(catalog)

    reserved = {entry["name"] for entry in _TOOL_CATALOG}
    for contribution in plugin_manager.mcp_tool_contributions(reserved_names=reserved):
        catalog.append(contribution.catalog_entry)
    return tuple(catalog)


def common_error_recovery() -> dict[str, str]:
    """Return shared recovery guidance for MCP-exposed error codes."""
    return dict(COMMON_ERROR_RECOVERY)


def _catalog_entry(name: str, vault: Any | None = None) -> ToolCatalogEntry:
    """Look up tool metadata by registered name."""
    if vault is None:
        return _TOOL_CATALOG_BY_NAME[name]
    for entry in tool_catalog(vault):
        if entry["name"] == name:
            return entry
    return _TOOL_CATALOG_BY_NAME[name]


def _format_side_effect(side_effect: ToolSideEffect) -> str:
    """Human-readable side-effect guidance for MCP metadata."""
    if side_effect == "write":
        return "write. Mutates vault state."
    return "read. Does not mutate vault state."


def _render_tool_doc(tool: ToolCatalogEntry) -> str:
    """Build a generated MCP tool description from the authoritative catalog."""
    lines = [
        f"What it does: {tool['description']}",
        f"When to use: {tool['when_to_use']}",
        f"Avoid when: {tool['avoid_when']}",
        f"Side effects: {_format_side_effect(tool['side_effect'])}",
    ]
    if tool["args_guidance"]:
        lines.append("Args:")
        for arg_name, guidance in tool["args_guidance"].items():
            lines.append(f"- {arg_name}: {guidance}")
    if tool["common_errors"]:
        lines.append("Common errors:")
        for code in tool["common_errors"]:
            recovery = COMMON_ERROR_RECOVERY.get(code)
            if recovery is None:
                lines.append(f"- {code}")
                continue
            lines.append(f"- {code}: {recovery}")
    return "\n".join(lines)


def _register_tool(
    server: Any,
    fn: Callable[..., dict[str, Any]],
    *,
    entry: ToolCatalogEntry | None = None,
    vault: Any | None = None,
) -> None:
    """Register an MCP tool with generated metadata from the catalog."""
    resolved_entry = entry or _catalog_entry(fn.__name__, vault)
    fn.__doc__ = _render_tool_doc(resolved_entry)
    server.tool()(fn)


def _to_mcp_response(result: ServiceResult) -> dict[str, Any]:
    """Convert a ServiceResult to an MCP-friendly dict."""
    response: dict[str, Any] = {
        "ok": result.ok,
        "op": result.op,
        "data": result.data,
    }
    if result.warnings:
        response["warnings"] = result.warnings
    if result.error is not None:
        response["error"] = {
            "code": result.error.code,
            "message": result.error.message,
        }
    return response


# ---------------------------------------------------------------------------
# Discovery tools (3)
# ---------------------------------------------------------------------------


def discover_tools_impl(_vault: Any, *, category: str | None = None) -> dict[str, Any]:
    """List available MCP tools grouped by category.

    If *category* is provided, only tools in that category are returned.
    """
    selected_category = category.lower().strip() if category else None

    available = tool_catalog(_vault)
    selected = [
        tool
        for tool in available
        if selected_category is None or tool["category"] == selected_category
    ]

    grouped: dict[str, list[dict[str, str]]] = {}
    for tool in selected:
        grouped.setdefault(tool["category"], []).append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "side_effect": tool["side_effect"],
            }
        )

    grouped_items: list[tuple[str, list[dict[str, str]]]] = sorted(
        grouped.items(), key=lambda item: item[0]
    )
    categories: list[dict[str, Any]] = []
    for cat, tools in grouped_items:
        categories.append({"name": cat, "tools": sorted(tools, key=_tool_name_key)})
    return {
        "ok": True,
        "op": "discover_tools",
        "data": {
            "count": len(selected),
            "total_count": len(available),
            "categories": categories,
        },
    }


def _tool_name_key(tool: dict[str, str]) -> str:
    """Sort MCP catalog entries by tool name."""
    return tool["name"]


def list_tags_impl(
    vault: Any,
    *,
    prefix: str | None = None,
    limit: int = 100,
) -> dict[str, Any]:
    """List active tags with usage counts."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).list_tags(prefix=prefix, limit=limit)
    return _to_mcp_response(result)


def describe_tool_impl(_vault: Any, *, name: str) -> dict[str, Any]:
    """Get detailed usage guidance for a single tool by name.

    Pure catalog lookup — no service call needed.
    """
    tool_name = name.lower().strip()
    for tool in tool_catalog(_vault):
        if tool["name"] == tool_name:
            return {
                "ok": True,
                "op": "describe_tool",
                "data": {
                    "name": tool["name"],
                    "category": tool["category"],
                    "description": tool["description"],
                    "when_to_use": tool["when_to_use"],
                    "avoid_when": tool["avoid_when"],
                    "side_effect": tool["side_effect"],
                    "common_errors": list(tool["common_errors"]),
                    "args_guidance": dict(tool["args_guidance"]),
                },
            }
    return {
        "ok": False,
        "op": "describe_tool",
        "error": {
            "code": "NOT_FOUND",
            "message": f"No tool named '{name}'. Use discover_tools() to list available tools.",
        },
    }


# ---------------------------------------------------------------------------
# Creation tools (5)
# ---------------------------------------------------------------------------


def create_note_impl(
    vault: Any,
    title: str,
    *,
    subtype: str | None = None,
    tags: list[str] | None = None,
    topic: str | None = None,
    body: str | None = None,
    key_points: list[str] | None = None,
    links: dict[str, list[str]] | None = None,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new note."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_note(
        title,
        subtype=subtype,
        tags=tags,
        topic=topic,
        body=body,
        key_points=key_points,
        links=links,
        aliases=aliases,
    )
    return _to_mcp_response(result)


def create_reference_impl(
    vault: Any,
    title: str,
    *,
    url: str | None = None,
    subtype: str | None = None,
    tags: list[str] | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """Create a new reference."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_reference(
        title,
        url=url,
        subtype=subtype,
        tags=tags,
        topic=topic,
    )
    return _to_mcp_response(result)


def ingest_source_impl(
    vault: Any,
    *,
    input_kind: str,
    content: str,
    target_type: str,
    title: str | None = None,
    topic: str | None = None,
    tags: list[str] | None = None,
    session: str | None = None,
    provider: str | None = None,
    summary: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Ingest normalized text, file, or URL content into the vault."""
    from pathlib import Path

    from ztlctl.services.ingest import IngestService

    service = IngestService(vault)
    kind = input_kind.strip().lower()
    if kind == "text":
        resolved_title = (title or "Untitled Capture").strip()
        result = service.ingest_text(
            resolved_title,
            content,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            summary=summary,
            dry_run=dry_run,
        )
        return _to_mcp_response(result)
    if kind == "file":
        result = service.ingest_file(
            Path(content),
            title=title,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            summary=summary,
            dry_run=dry_run,
        )
        return _to_mcp_response(result)
    if kind == "url":
        result = service.ingest_url(
            content,
            provider=provider,
            title=title,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            summary=summary,
            dry_run=dry_run,
        )
        return _to_mcp_response(result)
    return {
        "ok": False,
        "op": "ingest_source",
        "error": {
            "code": "VALIDATION_FAILED",
            "message": f"Unsupported input_kind '{input_kind}'. Use text, file, or url.",
        },
    }


def create_task_impl(
    vault: Any,
    title: str,
    *,
    priority: str = "medium",
    impact: str = "medium",
    effort: str = "medium",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new task."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_task(
        title, priority=priority, impact=impact, effort=effort, tags=tags
    )
    return _to_mcp_response(result)


def create_log_impl(vault: Any, topic: str) -> dict[str, Any]:
    """Start a new session (creates a log entry)."""
    from ztlctl.services.session import SessionService

    result = SessionService(vault).start(topic)
    return _to_mcp_response(result)


def garden_seed_impl(
    vault: Any,
    title: str,
    *,
    tags: list[str] | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """Quick-capture a seed note with minimal ceremony."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_note(title, maturity="seed", tags=tags, topic=topic)
    return _to_mcp_response(result)


# ---------------------------------------------------------------------------
# Lifecycle tools (3)
# ---------------------------------------------------------------------------


def update_content_impl(
    vault: Any,
    content_id: str,
    *,
    changes: dict[str, Any],
) -> dict[str, Any]:
    """Update a content item."""
    from ztlctl.services.update import UpdateService

    result = UpdateService(vault).update(content_id, changes=changes)
    return _to_mcp_response(result)


def close_content_impl(vault: Any, content_id: str) -> dict[str, Any]:
    """Archive/close a content item."""
    from ztlctl.services.update import UpdateService

    result = UpdateService(vault).archive(content_id)
    return _to_mcp_response(result)


def reweave_impl(
    vault: Any,
    *,
    content_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run reweave on a content item."""
    from ztlctl.services.reweave import ReweaveService

    result = ReweaveService(vault).reweave(content_id=content_id, dry_run=dry_run)
    return _to_mcp_response(result)


# ---------------------------------------------------------------------------
# Query tools (6)
# ---------------------------------------------------------------------------


def search_impl(
    vault: Any,
    query: str,
    *,
    content_type: str | None = None,
    tag: str | None = None,
    space: str | None = None,
    rank_by: str = "relevance",
    limit: int = 20,
) -> dict[str, Any]:
    """Full-text search."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).search(
        query, content_type=content_type, tag=tag, space=space, rank_by=rank_by, limit=limit
    )
    return _to_mcp_response(result)


def get_document_impl(vault: Any, content_id: str) -> dict[str, Any]:
    """Get a single document by ID."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).get(content_id)
    return _to_mcp_response(result)


def get_related_impl(
    vault: Any,
    content_id: str,
    *,
    depth: int = 2,
    top: int = 20,
) -> dict[str, Any]:
    """Get related content via graph traversal."""
    from ztlctl.services.graph import GraphService

    result = GraphService(vault).related(content_id, depth=depth, top=top)
    return _to_mcp_response(result)


def agent_context_impl(
    vault: Any,
    *,
    query: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    """Build agent context from vault state.

    Delegates to SessionService.context() when a session is active.
    Falls back to QueryService-based context when no session is open.
    """
    from ztlctl.services.session import SessionService

    # Try session-based context first
    result = SessionService(vault).context(topic=query)
    if result.ok:
        payload = dump_validated(AgentContextResultData, result.data)
        return {"ok": True, "op": "agent_context", "data": payload}

    # Fallback: no active session — use QueryService directly
    from ztlctl.services.query import QueryService

    svc = QueryService(vault)

    context: dict[str, Any] = {}

    # Overview: counts by type
    count_result = svc.count_items()
    if count_result.ok:
        context["total_items"] = count_result.data.get("count", 0)

    # Recent items
    recent = svc.list_items(sort="recency", limit=limit)
    if recent.ok:
        context["recent"] = recent.data.get("items", [])

    # Search results if query provided
    if query:
        search_result = svc.search(query, limit=limit)
        if search_result.ok:
            context["search_results"] = search_result.data.get("items", [])

    # Work queue
    work_result = svc.work_queue()
    if work_result.ok:
        context["work_queue"] = work_result.data.get("items", [])

    payload = dump_validated(AgentContextFallbackData, context)
    return {"ok": True, "op": "agent_context", "data": payload}


def list_items_impl(
    vault: Any,
    *,
    content_type: str | None = None,
    status: str | None = None,
    tag: str | None = None,
    topic: str | None = None,
    subtype: str | None = None,
    maturity: str | None = None,
    space: str | None = None,
    since: str | None = None,
    include_archived: bool = False,
    sort: str = "recency",
    limit: int = 20,
) -> dict[str, Any]:
    """List vault items with filtering."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).list_items(
        content_type=content_type,
        status=status,
        tag=tag,
        topic=topic,
        subtype=subtype,
        maturity=maturity,
        space=space,
        since=since,
        include_archived=include_archived,
        sort=sort,
        limit=limit,
    )
    return _to_mcp_response(result)


def topic_packet_impl(
    vault: Any,
    *,
    topic: str,
    mode: str = "learn",
    budget: int = 4000,
) -> dict[str, Any]:
    """Build a topic packet for conversational learning and review."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).topic_packet(topic, mode=mode, budget=budget)
    return _to_mcp_response(result)


def work_queue_impl(
    vault: Any,
    *,
    space: str | None = None,
) -> dict[str, Any]:
    """Get prioritized actionable tasks."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).work_queue(space=space)
    return _to_mcp_response(result)


def decision_support_impl(
    vault: Any,
    *,
    topic: str | None = None,
    space: str | None = None,
) -> dict[str, Any]:
    """Aggregate decision context for a topic."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).decision_support(topic=topic, space=space)
    return _to_mcp_response(result)


def vault_review_impl(
    vault: Any,
    *,
    top: int = 10,
    stale_days: int = 7,
) -> dict[str, Any]:
    """Aggregate a review-ready vault snapshot."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).vault_review(top=top, stale_days=stale_days)
    return _to_mcp_response(result)


# ---------------------------------------------------------------------------
# Graph tools (5)
# ---------------------------------------------------------------------------


def graph_themes_impl(vault: Any) -> dict[str, Any]:
    """Detect knowledge communities via graph clustering."""
    from ztlctl.services.graph import GraphService

    result = GraphService(vault).themes()
    return _to_mcp_response(result)


def graph_rank_impl(vault: Any, *, top: int = 20) -> dict[str, Any]:
    """Rank content by importance via PageRank."""
    from ztlctl.services.graph import GraphService

    result = GraphService(vault).rank(top=top)
    return _to_mcp_response(result)


def graph_path_impl(
    vault: Any,
    source_id: str,
    target_id: str,
) -> dict[str, Any]:
    """Find connection path between two items."""
    from ztlctl.services.graph import GraphService

    result = GraphService(vault).path(source_id, target_id)
    return _to_mcp_response(result)


def graph_gaps_impl(vault: Any, *, top: int = 20) -> dict[str, Any]:
    """Identify structural holes in the knowledge graph."""
    from ztlctl.services.graph import GraphService

    result = GraphService(vault).gaps(top=top)
    return _to_mcp_response(result)


def graph_bridges_impl(vault: Any, *, top: int = 20) -> dict[str, Any]:
    """Find bridge notes via betweenness centrality."""
    from ztlctl.services.graph import GraphService

    result = GraphService(vault).bridges(top=top)
    return _to_mcp_response(result)


# ---------------------------------------------------------------------------
# Session tools (2)
# ---------------------------------------------------------------------------


def session_close_impl(vault: Any, *, summary: str | None = None) -> dict[str, Any]:
    """Close the active session."""
    from ztlctl.services.session import SessionService

    result = SessionService(vault).close(summary=summary)
    return _to_mcp_response(result)


def session_status_impl(vault: Any) -> dict[str, Any]:
    """Get the active session, if any."""
    from ztlctl.services.session import SessionService

    result = SessionService(vault).status()
    return _to_mcp_response(result)


def list_source_providers_impl(vault: Any) -> dict[str, Any]:
    """List registered source providers for ingestion."""
    from ztlctl.services.ingest import IngestService

    result = IngestService(vault).list_providers()
    return _to_mcp_response(result)


# ---------------------------------------------------------------------------
# Registration — wraps _impl functions with FastMCP decorators
# ---------------------------------------------------------------------------


def register_tools(server: Any, vault: Any) -> None:
    """Register all MCP tools on the FastMCP server."""

    def discover_tools(category: str | None = None) -> dict[str, Any]:
        return discover_tools_impl(vault, category=category)

    def list_tags(prefix: str | None = None, limit: int = 100) -> dict[str, Any]:
        return list_tags_impl(vault, prefix=prefix, limit=limit)

    def list_source_providers() -> dict[str, Any]:
        return list_source_providers_impl(vault)

    def describe_tool(name: str) -> dict[str, Any]:
        return describe_tool_impl(vault, name=name)

    def create_note(
        title: str,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        body: str | None = None,
        key_points: list[str] | None = None,
        links: dict[str, list[str]] | None = None,
        aliases: list[str] | None = None,
    ) -> dict[str, Any]:
        return create_note_impl(
            vault,
            title,
            subtype=subtype,
            tags=tags,
            topic=topic,
            body=body,
            key_points=key_points,
            links=links,
            aliases=aliases,
        )

    def create_reference(
        title: str,
        url: str | None = None,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        return create_reference_impl(
            vault,
            title,
            url=url,
            subtype=subtype,
            tags=tags,
            topic=topic,
        )

    def create_task(
        title: str,
        priority: str = "medium",
        impact: str = "medium",
        effort: str = "medium",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        return create_task_impl(
            vault, title, priority=priority, impact=impact, effort=effort, tags=tags
        )

    def create_log(topic: str) -> dict[str, Any]:
        return create_log_impl(vault, topic)

    def garden_seed(
        title: str,
        tags: list[str] | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        return garden_seed_impl(vault, title, tags=tags, topic=topic)

    def ingest_source(
        input_kind: str,
        content: str,
        target_type: str,
        title: str | None = None,
        topic: str | None = None,
        tags: list[str] | None = None,
        session: str | None = None,
        provider: str | None = None,
        summary: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        return ingest_source_impl(
            vault,
            input_kind=input_kind,
            content=content,
            target_type=target_type,
            title=title,
            topic=topic,
            tags=tags,
            session=session,
            provider=provider,
            summary=summary,
            dry_run=dry_run,
        )

    def update_content(content_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        return update_content_impl(vault, content_id, changes=changes)

    def close_content(content_id: str) -> dict[str, Any]:
        return close_content_impl(vault, content_id)

    def reweave(
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        return reweave_impl(vault, content_id=content_id, dry_run=dry_run)

    def search(
        query: str,
        content_type: str | None = None,
        tag: str | None = None,
        space: str | None = None,
        rank_by: str = "relevance",
        limit: int = 20,
    ) -> dict[str, Any]:
        return search_impl(
            vault,
            query,
            content_type=content_type,
            tag=tag,
            space=space,
            rank_by=rank_by,
            limit=limit,
        )

    def get_document(content_id: str) -> dict[str, Any]:
        return get_document_impl(vault, content_id)

    def get_related(
        content_id: str,
        depth: int = 2,
        top: int = 20,
    ) -> dict[str, Any]:
        return get_related_impl(vault, content_id, depth=depth, top=top)

    def agent_context(
        query: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        return agent_context_impl(vault, query=query, limit=limit)

    def session_close(summary: str | None = None) -> dict[str, Any]:
        return session_close_impl(vault, summary=summary)

    def session_status() -> dict[str, Any]:
        return session_status_impl(vault)

    def list_items(
        content_type: str | None = None,
        status: str | None = None,
        tag: str | None = None,
        topic: str | None = None,
        subtype: str | None = None,
        maturity: str | None = None,
        space: str | None = None,
        since: str | None = None,
        include_archived: bool = False,
        sort: str = "recency",
        limit: int = 20,
    ) -> dict[str, Any]:
        return list_items_impl(
            vault,
            content_type=content_type,
            status=status,
            tag=tag,
            topic=topic,
            subtype=subtype,
            maturity=maturity,
            space=space,
            since=since,
            include_archived=include_archived,
            sort=sort,
            limit=limit,
        )

    def work_queue(space: str | None = None) -> dict[str, Any]:
        return work_queue_impl(vault, space=space)

    def topic_packet(
        topic: str,
        mode: str = "learn",
        budget: int = 4000,
    ) -> dict[str, Any]:
        return topic_packet_impl(vault, topic=topic, mode=mode, budget=budget)

    def decision_support(
        topic: str | None = None,
        space: str | None = None,
    ) -> dict[str, Any]:
        return decision_support_impl(vault, topic=topic, space=space)

    def vault_review(top: int = 10, stale_days: int = 7) -> dict[str, Any]:
        return vault_review_impl(vault, top=top, stale_days=stale_days)

    def graph_themes() -> dict[str, Any]:
        return graph_themes_impl(vault)

    def graph_rank(top: int = 20) -> dict[str, Any]:
        return graph_rank_impl(vault, top=top)

    def graph_path(source_id: str, target_id: str) -> dict[str, Any]:
        return graph_path_impl(vault, source_id, target_id)

    def graph_gaps(top: int = 20) -> dict[str, Any]:
        return graph_gaps_impl(vault, top=top)

    def graph_bridges(top: int = 20) -> dict[str, Any]:
        return graph_bridges_impl(vault, top=top)

    for fn in (
        discover_tools,
        list_tags,
        list_source_providers,
        describe_tool,
        create_note,
        create_reference,
        create_task,
        create_log,
        garden_seed,
        ingest_source,
        update_content,
        close_content,
        reweave,
        search,
        get_document,
        get_related,
        agent_context,
        session_close,
        session_status,
        list_items,
        work_queue,
        topic_packet,
        decision_support,
        vault_review,
        graph_themes,
        graph_rank,
        graph_path,
        graph_gaps,
        graph_bridges,
    ):
        _register_tool(server, fn, vault=vault)

    plugin_manager = getattr(vault, "plugin_manager", None)
    if plugin_manager is None:
        return

    reserved = {entry["name"] for entry in _TOOL_CATALOG}
    for contribution in plugin_manager.mcp_tool_contributions(reserved_names=reserved):
        bound = partial(contribution.handler, vault)
        bound.__name__ = contribution.name
        _register_tool(server, bound, entry=contribution.catalog_entry, vault=vault)
