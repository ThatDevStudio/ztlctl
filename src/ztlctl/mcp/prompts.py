"""MCP prompt definitions — portable workflow prompts.

Prompts: research_session, knowledge_capture, vault_orientation,
decision_record. Available to any MCP client. (DESIGN.md Section 16)
Each prompt has a ``_<name>_impl`` function testable without the mcp package.
"""

from __future__ import annotations

from typing import Any, cast

_PROMPT_CATALOG: tuple[dict[str, str], ...] = (
    {"name": "research_session", "description": "Start a structured research session on a topic."},
    {"name": "knowledge_capture", "description": "Capture knowledge into the vault."},
    {
        "name": "vault_orientation",
        "description": "Get oriented in this vault (reads identity + methodology + overview).",
    },
    {"name": "decision_record", "description": "Document a decision with structured context."},
)


def _plugin_prompt_wrapper(
    vault: Any,
    name: str,
    handler: Any,
    *,
    takes_vault: bool,
) -> Any:
    """Bind a plugin prompt handler to the current vault."""

    if takes_vault:

        def wrapped(*args: Any, **kwargs: Any) -> str:
            return cast(str, handler(vault, *args, **kwargs))
    else:

        def wrapped(*args: Any, **kwargs: Any) -> str:
            return cast(str, handler(*args, **kwargs))

    wrapped.__name__ = name
    return wrapped


def prompt_catalog(vault: Any | None = None) -> tuple[dict[str, str], ...]:
    """Return the MCP prompt catalog for validation and docs."""
    catalog = list(_PROMPT_CATALOG)
    plugin_manager = getattr(vault, "plugin_manager", None) if vault is not None else None
    if plugin_manager is None:
        return tuple(catalog)

    reserved = {entry["name"] for entry in _PROMPT_CATALOG}
    for contribution in plugin_manager.mcp_prompt_contributions(reserved_names=reserved):
        catalog.append({"name": contribution.name, "description": contribution.description})
    return tuple(catalog)


# ---------------------------------------------------------------------------
# Prompt implementations (testable without mcp)
# ---------------------------------------------------------------------------


def research_session_impl(topic: str) -> str:
    """Generate instructions for a research session workflow."""
    return f"""## Research Session: {topic}

You are conducting a structured research session on "{topic}".

### Workflow
1. **Start session**: Use `create_log` with topic "{topic}"
2. **Capture sources**: For each source, use `create_reference` with URL and tags
3. **Create notes**: Synthesize findings into notes with `create_note`
4. **Link knowledge**: Run `reweave` to discover connections
5. **Close session**: Use `session_close` with a summary of findings

### Guidelines
- Tag all items with `research/{topic}` for easy retrieval
- Create decision notes for key choices using subtype="decision"
- Use `get_related` to discover unexpected connections
- Keep notes atomic — one idea per note
"""


def knowledge_capture_impl() -> str:
    """Generate instructions for knowledge capture workflow."""
    return """## Knowledge Capture Workflow

You are capturing knowledge into the vault.

### Workflow
1. **Check existing**: Use `search` to find related content first
2. **Create note**: Use `create_note` with appropriate tags and topic
3. **Add references**: Link to sources with `create_reference`
4. **Connect**: Run `reweave` to automatically link related content
5. **Review**: Use `get_related` to verify connections make sense

### Guidelines
- Use descriptive titles (they power search and linking)
- Apply domain/scope tags (e.g., "math/algebra", "project/alpha")
- Keep notes focused — split complex topics into multiple notes
- Reference sources for all factual claims
"""


def vault_orientation_impl(vault: Any) -> str:
    """Generate onboarding instructions for an agent entering the vault."""
    from ztlctl.mcp.resources import (
        overview_impl,
        resource_catalog,
        self_identity_impl,
        self_methodology_impl,
    )
    from ztlctl.mcp.tools import tool_catalog

    identity = self_identity_impl(vault)
    methodology = self_methodology_impl(vault)
    overview = overview_impl(vault)

    counts = overview.get("counts", {})
    total = overview.get("total", 0)
    grouped_tools: dict[str, list[str]] = {}
    for entry in tool_catalog(vault):
        grouped_tools.setdefault(entry["category"], []).append(entry["name"])

    tool_lines = "\n".join(
        f"- **{category.replace('_', ' ').title()}**: {', '.join(sorted(names))}"
        for category, names in sorted(grouped_tools.items())
    )
    resource_lines = "\n".join(
        f"- `{entry['uri']}` — {entry['description']}" for entry in resource_catalog(vault)
    )

    return f"""## Vault Orientation

### Identity
{identity}

### Methodology
{methodology}

### Current State
- **Total items**: {total}
- **Notes**: {counts.get("note", 0)}
- **References**: {counts.get("reference", 0)}
- **Tasks**: {counts.get("task", 0)}
- **Sessions**: {counts.get("log", 0)}

### Tool Categories
{tool_lines}

### Available Resources
{resource_lines}

### Discovery Rule
If you are unsure which tool to call, start with `discover_tools`; if you know the
name but not the contract, call `describe_tool`.
"""


def decision_record_impl(topic: str) -> str:
    """Generate instructions for documenting a decision."""
    return f"""## Decision Record: {topic}

You are documenting a decision about "{topic}".

### Workflow
1. **Search context**: Use `search` for "{topic}" to find related content
2. **Review related**: Use `get_related` on relevant items
3. **Create decision**: Use `create_note` with subtype="decision"
   - Title: "Decision: {topic}"
   - Include context, options considered, and rationale
4. **Link evidence**: Reference supporting notes and sources
5. **Run reweave**: Connect the decision to related knowledge

### Decision Note Structure
```markdown
## Context
[What situation led to this decision?]

## Options Considered
1. [Option A] — [pros/cons]
2. [Option B] — [pros/cons]

## Decision
[What was decided and why]

## Consequences
[Expected outcomes and trade-offs]
```
"""


# ---------------------------------------------------------------------------
# Registration — wraps _impl functions with FastMCP decorators
# ---------------------------------------------------------------------------


def register_prompts(server: Any, vault: Any) -> None:
    """Register core and plugin MCP prompts on the FastMCP server."""

    @server.prompt()  # type: ignore[untyped-decorator]
    def research_session(topic: str) -> str:
        """Start a structured research session on a topic."""
        return research_session_impl(topic)

    @server.prompt()  # type: ignore[untyped-decorator]
    def knowledge_capture() -> str:
        """Capture knowledge into the vault."""
        return knowledge_capture_impl()

    @server.prompt()  # type: ignore[untyped-decorator]
    def vault_orientation() -> str:
        """Get oriented in this vault (reads identity + methodology + overview)."""
        return vault_orientation_impl(vault)

    @server.prompt()  # type: ignore[untyped-decorator]
    def decision_record(topic: str) -> str:
        """Document a decision with structured context."""
        return decision_record_impl(topic)

    plugin_manager = getattr(vault, "plugin_manager", None)
    if plugin_manager is None:
        return

    reserved = {entry["name"] for entry in _PROMPT_CATALOG}
    for contribution in plugin_manager.mcp_prompt_contributions(reserved_names=reserved):
        handler = _plugin_prompt_wrapper(
            vault,
            contribution.name,
            contribution.handler,
            takes_vault=contribution.takes_vault,
        )
        handler.__name__ = contribution.name
        handler.__doc__ = contribution.description
        server.prompt()(handler)
