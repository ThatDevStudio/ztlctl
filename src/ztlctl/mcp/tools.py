"""MCP tool definitions — 12 tools across 4 categories.

Categories: Creation (4), Lifecycle (3), Query (4), Session (1).
Each tool has a ``_<name>_impl`` function testable without the mcp package.
``register_tools()`` wraps them with FastMCP decorators.
(DESIGN.md Section 16)
"""

from __future__ import annotations

from typing import Any

from ztlctl.services.contracts import (
    AgentContextFallbackData,
    AgentContextResultData,
    dump_validated,
)
from ztlctl.services.result import ServiceResult


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
# Creation tools (4)
# ---------------------------------------------------------------------------


def create_note_impl(
    vault: Any,
    title: str,
    *,
    subtype: str | None = None,
    tags: list[str] | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """Create a new note."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_note(title, subtype=subtype, tags=tags, topic=topic)
    return _to_mcp_response(result)


def create_reference_impl(
    vault: Any,
    title: str,
    *,
    url: str | None = None,
    tags: list[str] | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """Create a new reference."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_reference(title, url=url, tags=tags, topic=topic)
    return _to_mcp_response(result)


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
# Query tools (4)
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


# ---------------------------------------------------------------------------
# Session tools (1)
# ---------------------------------------------------------------------------


def session_close_impl(vault: Any, *, summary: str | None = None) -> dict[str, Any]:
    """Close the active session."""
    from ztlctl.services.session import SessionService

    result = SessionService(vault).close(summary=summary)
    return _to_mcp_response(result)


# ---------------------------------------------------------------------------
# Registration — wraps _impl functions with FastMCP decorators
# ---------------------------------------------------------------------------


def register_tools(server: Any, vault: Any) -> None:
    """Register all 12 MCP tools on the FastMCP server."""

    @server.tool()  # type: ignore[untyped-decorator]
    def create_note(
        title: str,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """Create a new note in the vault."""
        return create_note_impl(vault, title, subtype=subtype, tags=tags, topic=topic)

    @server.tool()  # type: ignore[untyped-decorator]
    def create_reference(
        title: str,
        url: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """Create a new reference to an external source."""
        return create_reference_impl(vault, title, url=url, tags=tags, topic=topic)

    @server.tool()  # type: ignore[untyped-decorator]
    def create_task(
        title: str,
        priority: str = "medium",
        impact: str = "medium",
        effort: str = "medium",
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new task with priority/impact/effort matrix."""
        return create_task_impl(
            vault, title, priority=priority, impact=impact, effort=effort, tags=tags
        )

    @server.tool()  # type: ignore[untyped-decorator]
    def create_log(topic: str) -> dict[str, Any]:
        """Start a new session (creates a log entry)."""
        return create_log_impl(vault, topic)

    @server.tool()  # type: ignore[untyped-decorator]
    def update_content(content_id: str, changes: dict[str, Any]) -> dict[str, Any]:
        """Update a content item's fields."""
        return update_content_impl(vault, content_id, changes=changes)

    @server.tool()  # type: ignore[untyped-decorator]
    def close_content(content_id: str) -> dict[str, Any]:
        """Archive/close a content item."""
        return close_content_impl(vault, content_id)

    @server.tool()  # type: ignore[untyped-decorator]
    def reweave(
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        """Run link suggestion and creation on a content item."""
        return reweave_impl(vault, content_id=content_id, dry_run=dry_run)

    @server.tool()  # type: ignore[untyped-decorator]
    def search(
        query: str,
        content_type: str | None = None,
        tag: str | None = None,
        space: str | None = None,
        rank_by: str = "relevance",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Full-text search across the vault."""
        return search_impl(
            vault,
            query,
            content_type=content_type,
            tag=tag,
            space=space,
            rank_by=rank_by,
            limit=limit,
        )

    @server.tool()  # type: ignore[untyped-decorator]
    def get_document(content_id: str) -> dict[str, Any]:
        """Get a single document by its ID."""
        return get_document_impl(vault, content_id)

    @server.tool()  # type: ignore[untyped-decorator]
    def get_related(
        content_id: str,
        depth: int = 2,
        top: int = 20,
    ) -> dict[str, Any]:
        """Get related content via graph traversal."""
        return get_related_impl(vault, content_id, depth=depth, top=top)

    @server.tool()  # type: ignore[untyped-decorator]
    def agent_context(
        query: str | None = None,
        limit: int = 5,
    ) -> dict[str, Any]:
        """Build agent context from vault state."""
        return agent_context_impl(vault, query=query, limit=limit)

    @server.tool()  # type: ignore[untyped-decorator]
    def session_close(summary: str | None = None) -> dict[str, Any]:
        """Close the active session with optional summary."""
        return session_close_impl(vault, summary=summary)
