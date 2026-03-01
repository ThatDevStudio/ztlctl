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
    """Agent reference: onboarding flow, tool catalog, workflows, and errors.

    Single-fetch onboarding payload for agents using the MCP server.
    """
    from ztlctl.mcp.tools import common_error_recovery, tool_catalog

    grouped: dict[str, list[dict[str, Any]]] = {}
    for tool in tool_catalog():
        grouped.setdefault(tool["category"], []).append(
            {
                "name": tool["name"],
                "description": tool["description"],
                "when_to_use": tool["when_to_use"],
                "avoid_when": tool["avoid_when"],
                "side_effect": tool["side_effect"],
                "common_errors": list(tool["common_errors"]),
                "args_guidance": dict(tool["args_guidance"]),
            }
        )
    tool_categories = {
        cat: sorted(tools, key=lambda t: t["name"]) for cat, tools in sorted(grouped.items())
    }

    recommended_start = {
        "when_unsure": {
            "tool": "discover_tools",
            "notes": "Start here to browse the available tool surface by category.",
            "recommended_args": {},
        },
        "when_name_known_but_contract_unclear": {
            "tool": "describe_tool",
            "notes": "Use this before a first call, especially for write tools.",
            "recommended_args": {"name": "create_note"},
        },
        "when_you_need_a_quick_read_only_snapshot": {
            "tool": "agent_context",
            "notes": "Use after discovery if you need vault state before taking action.",
            "recommended_args": {"limit": 5},
        },
    }

    workflow_examples = {
        "capture": [
            {
                "tool": "garden_seed",
                "notes": (
                    "Fastest path for a raw idea. Domain/scope tags are recommended but "
                    "not required."
                ),
                "recommended_args": {"title": "Quick idea"},
            },
            {
                "tool": "reweave",
                "notes": (
                    "Preview link suggestions before writing them when the vault is already "
                    "populated."
                ),
                "recommended_args": {"dry_run": True},
            },
        ],
        "research_session": [
            {
                "tool": "create_log",
                "notes": "Open a tracked session before recording sources and synthesis.",
                "recommended_args": {"topic": "research-topic"},
            },
            {
                "tool": "create_reference",
                "notes": "Capture external sources as they are reviewed.",
                "recommended_args": {"title": "Source title", "url": "https://example.com/source"},
            },
            {
                "tool": "create_note",
                "notes": "Synthesize findings into notes and use links to connect evidence.",
                "recommended_args": {
                    "title": "Synthesis note",
                    "links": {"supports": ["REF-0001"]},
                },
            },
            {
                "tool": "reweave",
                "notes": "Run after synthesis to add additional connections.",
                "recommended_args": {},
            },
            {
                "tool": "session_close",
                "notes": "Close the session with a short summary when done.",
                "recommended_args": {"summary": "Key findings and next actions."},
            },
        ],
        "search_then_create": [
            {
                "tool": "search",
                "notes": "Look for existing related content before creating anything new.",
                "recommended_args": {"query": "topic keywords", "limit": 10},
            },
            {
                "tool": "get_related",
                "notes": "Inspect nearby graph context around a promising result.",
                "recommended_args": {"content_id": "NOTE-0001", "depth": 2, "top": 10},
            },
            {
                "tool": "create_note",
                "notes": (
                    "Create the new note only after checking for overlap. Use explicit links "
                    "if you already know the evidence to connect."
                ),
                "recommended_args": {
                    "title": "New note",
                    "links": {"related": ["NOTE-0001"]},
                },
            },
        ],
        "vault_maintenance": [
            {
                "tool": "vault_review",
                "notes": "Start with a broad health snapshot.",
                "recommended_args": {"top": 10, "stale_days": 7},
            },
            {
                "tool": "graph_gaps",
                "notes": "Find disconnected areas that likely need linking.",
                "recommended_args": {"top": 20},
            },
            {
                "tool": "graph_bridges",
                "notes": "Identify notes that already connect clusters well.",
                "recommended_args": {"top": 20},
            },
            {
                "tool": "reweave",
                "notes": "Use preview mode first during maintenance sweeps.",
                "recommended_args": {"dry_run": True},
            },
        ],
        "decision_documentation": [
            {
                "tool": "search",
                "notes": "Collect nearby evidence on the decision topic first.",
                "recommended_args": {"query": "decision topic", "limit": 10},
            },
            {
                "tool": "decision_support",
                "notes": "Build topic-specific decision context from the vault.",
                "recommended_args": {"topic": "decision topic"},
            },
            {
                "tool": "create_note",
                "notes": (
                    "Store the decision as a structured note subtype and link supporting evidence."
                ),
                "recommended_args": {
                    "title": "Decision: topic",
                    "subtype": "decision",
                },
            },
            {
                "tool": "reweave",
                "notes": "Connect the recorded decision back into the graph.",
                "recommended_args": {},
            },
        ],
    }

    return {
        "recommended_start": recommended_start,
        "tool_categories": tool_categories,
        "workflow_examples": workflow_examples,
        "common_errors": common_error_recovery(),
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
        """Agent reference: onboarding flow, tool catalog, workflows, and errors."""
        import json

        return json.dumps(agent_reference_impl(vault), indent=2)
