"""MCP resource definitions — 6 URI-based resources.

URIs: ztlctl://context, ztlctl://self/identity, ztlctl://self/methodology,
ztlctl://overview, ztlctl://work-queue, ztlctl://topics.
Each resource has a ``_<name>_impl`` function testable without the mcp package.
(DESIGN.md Section 16)
"""

from __future__ import annotations

from typing import Any

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


# ---------------------------------------------------------------------------
# Registration — wraps _impl functions with FastMCP decorators
# ---------------------------------------------------------------------------


def register_resources(server: Any, vault: Any) -> None:
    """Register all 6 MCP resources on the FastMCP server."""

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
