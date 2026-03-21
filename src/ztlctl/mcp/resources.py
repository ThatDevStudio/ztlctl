"""MCP resource definitions — URI-based resources.

URIs: ztlctl://context, ztlctl://polaris, ztlctl://self/identity,
ztlctl://self/methodology, ztlctl://overview, ztlctl://work-queue,
ztlctl://review/dashboard, ztlctl://garden/backlog, ztlctl://decision-queue,
ztlctl://capture/spec, ztlctl://topics, ztlctl://agent-reference.
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
    {"uri": "ztlctl://recipes", "description": "Index of available agent orchestration recipes."},
    {
        "uri": "ztlctl://recipes/research-capture",
        "description": "Research-capture workflow: search, create notes, link evidence.",
    },
    {
        "uri": "ztlctl://recipes/review-triage",
        "description": "Review-triage workflow: work queue, inspect, update, archive stale.",
    },
    {
        "uri": "ztlctl://recipes/knowledge-synthesis",
        "description": "Knowledge-synthesis workflow: search, find gaps, draft, reweave.",
    },
    {"uri": "ztlctl://polaris", "description": "The vault's polaris priorities document."},
    {"uri": "ztlctl://self/identity", "description": "The vault's identity document."},
    {"uri": "ztlctl://self/methodology", "description": "The vault's methodology document."},
    {"uri": "ztlctl://overview", "description": "Vault overview with counts and recent items."},
    {"uri": "ztlctl://work-queue", "description": "Current work queue (scored task list)."},
    {
        "uri": "ztlctl://review/dashboard",
        "description": (
            "External review workbench snapshot with work queues, review signals, "
            "and topic dossiers."
        ),
    },
    {
        "uri": "ztlctl://garden/backlog",
        "description": "Enrichment backlog signals focused on stale seeds and orphan notes.",
    },
    {
        "uri": "ztlctl://decision-queue",
        "description": "Recent decision notes and related review queue.",
    },
    {
        "uri": "ztlctl://capture/spec",
        "description": "Agent capture contract for source bundles and ingest_source.",
    },
    {"uri": "ztlctl://topics", "description": "List of topic directories in the vault."},
    {
        "uri": "ztlctl://agent-reference",
        "description": ("Agent reference: tool catalog, workflows, and error recovery."),
    },
    {
        "uri": "ztlctl://docs/index",
        "description": "Navigation map of all ztlctl documentation pages.",
    },
    {
        "uri": "ztlctl://docs/search",
        "description": (
            "Documentation search guidance. "
            "Use the docs_search tool to search the corpus by query string."
        ),
    },
)


def resource_catalog(vault: Any | None = None) -> tuple[dict[str, str], ...]:
    """Return the MCP resource catalog for validation and docs."""
    catalog = list(_RESOURCE_CATALOG)
    plugin_manager = getattr(vault, "plugin_manager", None) if vault is not None else None
    if plugin_manager is None:
        return tuple(catalog)

    reserved = {entry["uri"] for entry in _RESOURCE_CATALOG}
    for contribution in plugin_manager.mcp_resource_contributions(reserved_uris=reserved):
        catalog.append({"uri": contribution.uri, "description": contribution.description})
    return tuple(catalog)


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


def polaris_impl(vault: Any) -> str:
    """Read garden/groves/polaris.md from the vault."""
    path = vault.root / "garden" / "groves" / "polaris.md"
    if path.exists():
        return str(path.read_text(encoding="utf-8"))
    return (
        "No polaris file found. Run `ztlctl init` to generate one, "
        "or create garden/groves/polaris.md manually."
    )


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


def review_dashboard_impl(vault: Any) -> dict[str, Any]:
    """Return a review-oriented enrichment dashboard payload."""
    from ztlctl.services.query import QueryService

    review = QueryService(vault).vault_review(top=10)
    if review.ok:
        return review.data
    return {}


def garden_backlog_impl(vault: Any) -> dict[str, Any]:
    """Return stale and orphan machine-layer items that feed enrichment review."""
    from ztlctl.services.query import QueryService

    review = QueryService(vault).vault_review(top=10)
    if not review.ok:
        return {"items": [], "count": 0, "title_improvement_candidates": []}

    backlog = [
        *review.data.get("stale_seeds", []),
        *review.data.get("orphan_notes", []),
    ]
    seen: set[str] = set()
    items: list[dict[str, Any]] = []
    for item in backlog:
        item_id = str(item.get("id", ""))
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        items.append(item)

    # Title improvement candidates (from check at info severity)
    from ztlctl.services.check import CAT_STRUCTURAL, SEVERITY_INFO, CheckService

    check_result = CheckService(vault).check(min_severity="info")
    title_candidates: list[dict[str, Any]] = []
    if check_result.ok:
        for issue in check_result.data.get("issues", []):
            if (
                issue.get("category") == CAT_STRUCTURAL
                and issue.get("severity") == SEVERITY_INFO
                and "Title quality" in str(issue.get("message", ""))
            ):
                title_candidates.append(
                    {
                        "id": issue.get("node_id"),
                        "message": issue.get("message"),
                    }
                )

    return {
        "items": items,
        "count": len(items),
        "title_improvement_candidates": title_candidates,
    }


def decision_queue_impl(vault: Any) -> dict[str, Any]:
    """Return recent decision items plus the current work queue."""
    from ztlctl.services.query import QueryService

    svc = QueryService(vault)
    decisions = svc.list_items(content_type="note", subtype="decision", sort="recency", limit=10)
    work_queue = svc.work_queue()
    return {
        "decisions": decisions.data.get("items", []) if decisions.ok else [],
        "work_queue": work_queue.data.get("items", []) if work_queue.ok else [],
    }


def capture_spec_impl(_vault: Any) -> dict[str, Any]:
    """Return the agent-facing capture contract for source bundle ingest."""
    return {
        "version": 1,
        "workflow": [
            "Fetch or extract the source outside ztlctl.",
            "Normalize the capture into plain text plus a source_bundle object.",
            (
                "Call ingest_source with input_kind=text or url, "
                "content=<normalized text>, and source_bundle=<bundle>."
            ),
            (
                "Use topic_packet or draft_from_topic after ingest to review "
                "or synthesize the captured material."
            ),
        ],
        "bundle_fields": {
            "title": "Optional display title for the captured source.",
            "source_kind": "Optional source class such as web, pdf, image, audio, or video.",
            "modalities": "Optional list of evidence modalities present in the capture.",
            "capture_agent": "Agent, model, or tool that performed the acquisition.",
            "capture_method": "Short note on how the source was fetched or extracted.",
            "captured_at": "Optional ISO timestamp for the acquisition event.",
            "summary_hint": "Optional top-level summary of the captured source.",
            "key_points": "Optional distilled bullet points extracted by the agent.",
            "provenance": "Optional provenance lines preserved alongside the reference.",
            "source_title": (
                "Optional canonical source title if different from the reference title."
            ),
            "url": "Optional original source URL.",
            "canonical_url": "Optional canonical URL after redirects or cleanup.",
            "provider": "Optional fetch or extraction provider identifier.",
            "source_type": "Optional source or mime classification such as article or transcript.",
            "language": "Optional language code for the captured text.",
            "citations": "Optional list of strings or {text, locator, source} objects.",
            "excerpts": "Optional list of strings or {text, locator, modality, citation} objects.",
            "artifacts": "Optional list of {kind, label, uri, mime_type, metadata} objects.",
            "metadata": "Optional freeform JSON object for agent-specific details.",
        },
        "minimal_example": {
            "input_kind": "text",
            "content": "Normalized body text from the source.",
            "target_type": "reference",
            "title": "Example Source",
            "topic": "example-topic",
            "source_bundle": {
                "source_kind": "web",
                "modalities": ["text", "image"],
                "capture_agent": "codex",
                "capture_method": "browser fetch plus screenshot review",
                "canonical_url": "https://example.com/article",
                "citations": [{"text": "Example quote", "locator": "paragraph 4"}],
                "excerpts": [{"text": "Important excerpt", "locator": "paragraph 4"}],
                "artifacts": [
                    {
                        "kind": "screenshot",
                        "label": "header",
                        "uri": "https://example.com/header.png",
                    }
                ],
            },
        },
    }


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
    from ztlctl.mcp.generator import common_error_recovery, tool_catalog

    grouped: dict[str, list[dict[str, Any]]] = {}
    for tool in tool_catalog(_vault):
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
                "tool": "create_note",
                "notes": (
                    "Fastest path for a raw idea. Use maturity='seed' for quick captures. "
                    "Domain/scope tags are recommended but not required."
                ),
                "recommended_args": {"title": "Quick idea"},
            },
            {
                "tool": "ingest_text",
                "notes": (
                    "When an agent fetched or extracted a source externally, normalize it into "
                    "a source bundle and ingest it as a structured reference."
                ),
                "recommended_args": {
                    "title": "Captured Source",
                    "body_text": "Normalized source text",
                    "target_type": "reference",
                },
            },
            {
                "tool": "topic_packet",
                "notes": "Use after capture to turn source material into a conversational bundle.",
                "recommended_args": {"topic": "research-topic", "mode": "learn"},
            },
        ],
        "research_session": [
            {
                "tool": "start",
                "notes": "Open a tracked session before recording sources and synthesis.",
                "recommended_args": {"topic": "research-topic"},
            },
            {
                "tool": "create_reference",
                "notes": "Capture external sources as they are reviewed.",
                "recommended_args": {"title": "Source title", "url": "https://example.com/source"},
            },
            {
                "tool": "ingest_text",
                "notes": (
                    "Prefer this when the agent already has normalized text and structured "
                    "bundle metadata from web or multimodal capture."
                ),
                "recommended_args": {
                    "title": "Captured Source",
                    "body_text": "Normalized source text",
                    "target_type": "reference",
                },
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
                "tool": "close",
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
                "tool": "related",
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
            {
                "tool": "draft_from_topic",
                "notes": "Draft a synthesis artifact once the topic packet is strong enough.",
                "recommended_args": {"topic": "topic keywords", "target": "note"},
            },
        ],
        "vault_maintenance": [
            {
                "tool": "vault_review",
                "notes": "Start with a broad health snapshot.",
                "recommended_args": {"top": 10, "stale_days": 7},
            },
            {
                "tool": "gaps",
                "notes": "Find disconnected areas that likely need linking.",
                "recommended_args": {"top": 20},
            },
            {
                "tool": "bridges",
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
# Orchestration recipe resources (AGNT-03)
# ---------------------------------------------------------------------------


def recipe_research_capture_impl(_vault: Any) -> dict[str, Any]:
    """Return the research-capture orchestration recipe."""
    return {
        "name": "research-capture",
        "description": (
            "Capture research findings: search existing content, "
            "create synthesis notes, link evidence."
        ),
        "steps": [
            {
                "step": 1,
                "action": "search",
                "params": {"query": "{topic}", "limit": 10},
                "description": ("Search for existing content on the topic to avoid duplication."),
                "conditions": [],
            },
            {
                "step": 2,
                "action": "create_note",
                "params": {"title": "{synthesis_title}", "maturity": "seed"},
                "description": "Create a seed note to capture the synthesis.",
                "conditions": ["skip if step 1 returns a note with identical title"],
            },
            {
                "step": 3,
                "action": "reweave",
                "params": {"content_id": "{step_2.content_id}"},
                "description": ("Connect the new note to related content found in step 1."),
                "conditions": [],
            },
        ],
    }


def recipe_review_triage_impl(_vault: Any) -> dict[str, Any]:
    """Return the review-triage orchestration recipe."""
    return {
        "name": "review-triage",
        "description": (
            "Triage the work queue: inspect items, update stale notes, "
            "archive completed or obsolete ones."
        ),
        "steps": [
            {
                "step": 1,
                "action": "work_queue",
                "params": {},
                "description": "Fetch the scored work queue to find items needing attention.",
                "conditions": [],
            },
            {
                "step": 2,
                "action": "get_document",
                "params": {"content_id": "{step_1.items[0].id}"},
                "description": "Inspect the top-priority item in detail.",
                "conditions": ["repeat for each item in the work queue"],
            },
            {
                "step": 3,
                "action": "update",
                "params": {"content_id": "{step_2.id}", "changes": {}},
                "description": ("Update the item (e.g. advance maturity, correct tags, add body)."),
                "conditions": ["skip if item needs no changes"],
            },
            {
                "step": 4,
                "action": "archive",
                "params": {"content_id": "{step_2.id}"},
                "description": "Archive items that are complete or no longer relevant.",
                "conditions": ["only if item is complete or stale beyond recovery"],
            },
        ],
    }


def recipe_knowledge_synthesis_impl(_vault: Any) -> dict[str, Any]:
    """Return the knowledge-synthesis orchestration recipe."""
    return {
        "name": "knowledge-synthesis",
        "description": (
            "Synthesize knowledge from existing content: search, find gaps, "
            "draft a synthesis note, reweave connections."
        ),
        "steps": [
            {
                "step": 1,
                "action": "search",
                "params": {"query": "{topic}", "limit": 20},
                "description": "Gather existing content on the synthesis topic.",
                "conditions": [],
            },
            {
                "step": 2,
                "action": "gaps",
                "params": {"top": 10},
                "description": "Identify structural holes that the synthesis could bridge.",
                "conditions": [],
            },
            {
                "step": 3,
                "action": "draft_from_topic",
                "params": {"topic": "{topic}", "target": "note"},
                "description": "Draft a synthesis note from the accumulated topic material.",
                "conditions": ["skip if step 1 already returned a mature synthesis note"],
            },
            {
                "step": 4,
                "action": "reweave",
                "params": {"content_id": "{step_3.content_id}"},
                "description": "Connect the synthesis note into the knowledge graph.",
                "conditions": [],
            },
        ],
    }


def recipe_index_impl(_vault: Any) -> dict[str, Any]:
    """Return an index of all available orchestration recipes."""
    return {
        "recipes": [
            {
                "name": "research-capture",
                "uri": "ztlctl://recipes/research-capture",
                "description": (
                    "Capture research findings: search existing content, "
                    "create synthesis notes, link evidence."
                ),
            },
            {
                "name": "review-triage",
                "uri": "ztlctl://recipes/review-triage",
                "description": (
                    "Triage the work queue: inspect items, update stale notes, "
                    "archive completed or obsolete ones."
                ),
            },
            {
                "name": "knowledge-synthesis",
                "uri": "ztlctl://recipes/knowledge-synthesis",
                "description": (
                    "Synthesize knowledge from existing content: search, find gaps, "
                    "draft a synthesis note, reweave connections."
                ),
            },
        ]
    }


def docs_index_impl(_vault: Any = None) -> str:
    """Return navigation map of all documentation pages (content of docs/llms.txt)."""
    from ztlctl.services.docs import _docs_index_impl

    return _docs_index_impl()


def docs_search_resource_impl(_vault: Any = None) -> dict[str, Any]:
    """Return documentation search guidance for agents."""
    return {
        "info": (
            "To search the documentation corpus, use the 'docs_search' MCP tool. "
            "Call: docs_search(query='your question', limit=5)."
        ),
        "tool": "docs_search",
        "params": {
            "query": "string (required) — search terms",
            "limit": "int (default: 5) — maximum results",
        },
    }


# ---------------------------------------------------------------------------
# Registration — wraps _impl functions with FastMCP decorators
# ---------------------------------------------------------------------------


def register_resources(server: Any, vault: Any) -> None:
    """Register core and plugin MCP resources on the FastMCP server."""

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

    @server.resource("ztlctl://polaris")  # type: ignore[untyped-decorator]
    def polaris_resource() -> str:
        """The vault's polaris priorities document."""
        return polaris_impl(vault)

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

    @server.resource("ztlctl://review/dashboard")  # type: ignore[untyped-decorator]
    def review_dashboard_resource() -> str:
        """Review-oriented dashboard snapshot with work, gaps, and bridges."""
        import json

        return json.dumps(review_dashboard_impl(vault), indent=2)

    @server.resource("ztlctl://garden/backlog")  # type: ignore[untyped-decorator]
    def garden_backlog_resource() -> str:
        """Garden backlog focused on stale seeds and orphan notes."""
        import json

        return json.dumps(garden_backlog_impl(vault), indent=2)

    @server.resource("ztlctl://decision-queue")  # type: ignore[untyped-decorator]
    def decision_queue_resource() -> str:
        """Recent decision notes and related review queue."""
        import json

        return json.dumps(decision_queue_impl(vault), indent=2)

    @server.resource("ztlctl://capture/spec")  # type: ignore[untyped-decorator]
    def capture_spec_resource() -> str:
        """Agent capture contract for source bundles and ingest_source."""
        import json

        return json.dumps(capture_spec_impl(vault), indent=2)

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

    @server.resource("ztlctl://recipes")  # type: ignore[untyped-decorator]
    def recipes_index_resource() -> str:
        """Index of available agent orchestration recipes."""
        import json

        return json.dumps(recipe_index_impl(vault), indent=2)

    @server.resource("ztlctl://recipes/research-capture")  # type: ignore[untyped-decorator]
    def recipe_research_capture_resource() -> str:
        """Research-capture workflow: search, create notes, link evidence."""
        import json

        return json.dumps(recipe_research_capture_impl(vault), indent=2)

    @server.resource("ztlctl://recipes/review-triage")  # type: ignore[untyped-decorator]
    def recipe_review_triage_resource() -> str:
        """Review-triage workflow: work queue, inspect, update, archive stale."""
        import json

        return json.dumps(recipe_review_triage_impl(vault), indent=2)

    @server.resource("ztlctl://recipes/knowledge-synthesis")  # type: ignore[untyped-decorator]
    def recipe_knowledge_synthesis_resource() -> str:
        """Knowledge-synthesis workflow: search, find gaps, draft, reweave."""
        import json

        return json.dumps(recipe_knowledge_synthesis_impl(vault), indent=2)

    @server.resource("ztlctl://docs/index")  # type: ignore[untyped-decorator]
    def docs_index_resource() -> str:
        """Navigation map of all ztlctl documentation pages."""
        return docs_index_impl(vault)

    @server.resource("ztlctl://docs/search")  # type: ignore[untyped-decorator]
    def docs_search_guide_resource() -> str:
        """Documentation search guidance — use docs_search tool for queries."""
        import json

        return json.dumps(docs_search_resource_impl(vault), indent=2)

    plugin_manager = getattr(vault, "plugin_manager", None)
    if plugin_manager is None:
        return

    reserved = {entry["uri"] for entry in _RESOURCE_CATALOG}
    for contribution in plugin_manager.mcp_resource_contributions(reserved_uris=reserved):

        def _plugin_resource(
            uri: str = contribution.uri,
            handler: Any = contribution.handler,
        ) -> str:
            import json

            payload = handler(vault)
            if isinstance(payload, str):
                return payload
            return json.dumps(payload, indent=2)

        _plugin_resource.__name__ = contribution.uri.replace("://", "_").replace("/", "_")
        _plugin_resource.__doc__ = contribution.description
        server.resource(contribution.uri)(_plugin_resource)
