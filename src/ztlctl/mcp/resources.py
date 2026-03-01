"""MCP resource definitions — 7 URI-based resources.

URIs: ztlctl://context, ztlctl://self/identity, ztlctl://self/methodology,
ztlctl://overview, ztlctl://work-queue, ztlctl://topics,
ztlctl://agent-reference.
Each resource has a ``_<name>_impl`` function testable without the mcp package.
(DESIGN.md Section 16)
"""

from __future__ import annotations

from typing import Any

_RESOURCE_CATALOG: tuple[dict[str, str], ...] = (
    {
        "uri": "ztlctl://context",
        "description": "Full vault context: identity, methodology, and overview.",
    },
    {"uri": "ztlctl://self/identity", "description": "The vault's identity document."},
    {"uri": "ztlctl://self/methodology", "description": "The vault's methodology document."},
    {"uri": "ztlctl://overview", "description": "Vault overview with counts and recent items."},
    {"uri": "ztlctl://work-queue", "description": "Current work queue (scored task list)."},
    {"uri": "ztlctl://topics", "description": "List of topic directories in the vault."},
    {
        "uri": "ztlctl://agent-reference",
        "description": ("Agent reference: tool catalog, workflows, and error recovery."),
    },
)


def resource_catalog() -> tuple[dict[str, str], ...]:
    """Return the MCP resource catalog for validation and docs."""
    return _RESOURCE_CATALOG


# ---------------------------------------------------------------------------
# Resource implementations (testable without mcp)
# ---------------------------------------------------------------------------


def self_identity_impl(vault: Any) -> str:
    """Read self/identity.md from the vault."""
    path = vault.root / "self" / "identity.md"
    if path.exists():
        return str(path.read_text(encoding="utf-8"))
    return "No identity file found. Run `ztlctl init` to generate one."


def self_methodology_impl(vault: Any) -> str:
    """Read self/methodology.md from the vault."""
    path = vault.root / "self" / "methodology.md"
    if path.exists():
        return str(path.read_text(encoding="utf-8"))
    return "No methodology file found. Run `ztlctl init` to generate one."


def overview_impl(vault: Any) -> dict[str, Any]:
    """Return vault overview: node counts by type and recent items."""
    from ztlctl.services.query import QueryService

    svc = QueryService(vault)

    counts: dict[str, int] = {}
    for content_type in ("note", "reference", "task", "log"):
        result = svc.list_items(content_type=content_type, limit=10000)
        if result.ok:
            counts[content_type] = result.data.get("count", 0)

    recent_result = svc.list_items(sort="recency", limit=5)
    recent = recent_result.data.get("items", []) if recent_result.ok else []

    return {
        "vault_name": vault.settings.vault.name,
        "counts": counts,
        "total": sum(counts.values()),
        "recent": recent,
    }


def work_queue_impl(vault: Any) -> dict[str, Any]:
    """Return the work queue as JSON-friendly data."""
    from ztlctl.services.query import QueryService

    result = QueryService(vault).work_queue()
    if result.ok:
        return result.data
    return {"items": [], "count": 0}


def topics_impl(vault: Any) -> list[str]:
    """List topic subdirectories under notes/."""
    notes_dir = vault.root / "notes"
    if not notes_dir.exists():
        return []
    return sorted(d.name for d in notes_dir.iterdir() if d.is_dir())


def context_impl(vault: Any) -> dict[str, Any]:
    """Combined context: identity + methodology + overview."""
    return {
        "identity": self_identity_impl(vault),
        "methodology": self_methodology_impl(vault),
        "overview": overview_impl(vault),
    }


def agent_reference_impl(_vault: Any) -> dict[str, Any]:
    """Agent reference: tool catalog, workflows, and error recovery.

    Single-fetch onboarding payload for agents using the MCP server.
    """
    from ztlctl.mcp.tools import tool_catalog

    # --- tool_categories: group catalog by category ---
    grouped: dict[str, list[dict[str, str]]] = {}
    for tool in tool_catalog():
        grouped.setdefault(tool["category"], []).append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "when_to_use": tool["when_to_use"],
                "avoid_when": tool["avoid_when"],
            }
        )
    tool_categories = {
        cat: sorted(tools, key=lambda t: t["name"]) for cat, tools in sorted(grouped.items())
    }

    # --- workflows: common multi-step patterns ---
    workflows = {
        "capture": [
            "garden_seed",
            "reweave",
        ],
        "research_session": [
            "create_log",
            "create_reference",
            "create_note",
            "reweave",
            "session_close",
        ],
        "search_then_create": [
            "search",
            "get_related",
            "create_note (with links)",
        ],
        "vault_maintenance": [
            "vault_review",
            "graph_gaps",
            "graph_bridges",
            "reweave (dry_run=true)",
        ],
        "decision_documentation": [
            "search",
            "decision_support",
            "create_note (subtype=decision)",
            "reweave",
        ],
    }

    # --- error_recovery: map error codes to recovery ---
    error_recovery = {
        "NOT_FOUND": ("Verify the ID with search() or list_items()."),
        "VALIDATION_FAILED": (
            "Check required params; titles must be non-empty; tags use domain/scope format."
        ),
        "ID_COLLISION": (
            "Use search(title) to find existing item; update it or choose different title."
        ),
        "NO_ACTIVE_SESSION": ("Start a session with create_log(topic) first."),
        "INVALID_TRANSITION": ("Check current status with get_document(id)."),
        "NO_PATH": ("Ensure both IDs exist and are connected; use get_related() to verify."),
        "EMPTY_QUERY": (
            "Provide a non-empty query string; use list_items() to browse without search."
        ),
    }

    return {
        "tool_categories": tool_categories,
        "workflows": workflows,
        "error_recovery": error_recovery,
    }


# ---------------------------------------------------------------------------
# Registration — wraps _impl functions with FastMCP decorators
# ---------------------------------------------------------------------------


def register_resources(server: Any, vault: Any) -> None:
    """Register all 7 MCP resources on the FastMCP server."""

    @server.resource("ztlctl://context")  # type: ignore[untyped-decorator]
    def context_resource() -> str:
        """Full vault context: identity, methodology, and overview."""
        import json

        return json.dumps(context_impl(vault), indent=2)

    @server.resource("ztlctl://self/identity")  # type: ignore[untyped-decorator]
    def identity_resource() -> str:
        """The vault's identity document."""
        return self_identity_impl(vault)

    @server.resource("ztlctl://self/methodology")  # type: ignore[untyped-decorator]
    def methodology_resource() -> str:
        """The vault's methodology document."""
        return self_methodology_impl(vault)

    @server.resource("ztlctl://overview")  # type: ignore[untyped-decorator]
    def overview_resource() -> str:
        """Vault overview with counts and recent items."""
        import json

        return json.dumps(overview_impl(vault), indent=2)

    @server.resource("ztlctl://work-queue")  # type: ignore[untyped-decorator]
    def work_queue_resource() -> str:
        """Current work queue (scored task list)."""
        import json

        return json.dumps(work_queue_impl(vault), indent=2)

    @server.resource("ztlctl://topics")  # type: ignore[untyped-decorator]
    def topics_resource() -> str:
        """List of topic directories in the vault."""
        import json

        return json.dumps(topics_impl(vault), indent=2)

    @server.resource("ztlctl://agent-reference")  # type: ignore[untyped-decorator]
    def agent_reference_resource() -> str:
        """Agent reference: tool catalog, workflows, and error recovery."""
        import json

        return json.dumps(agent_reference_impl(vault), indent=2)
