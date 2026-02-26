"""MCP prompt definitions — 4 portable workflow prompts.

Prompts: research_session, knowledge_capture, vault_orientation,
decision_record. Available to any MCP client. (DESIGN.md Section 16)
Each prompt has a ``_<name>_impl`` function testable without the mcp package.
"""

from __future__ import annotations

from typing import Any

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
    from ztlctl.mcp.resources import overview_impl, self_identity_impl, self_methodology_impl

    identity = self_identity_impl(vault)
    methodology = self_methodology_impl(vault)
    overview = overview_impl(vault)

    counts = overview.get("counts", {})
    total = overview.get("total", 0)

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

### Available Tools
- **Creation**: create_note, create_reference, create_task, create_log
- **Lifecycle**: update_content, close_content, reweave
- **Query**: search, get_document, get_related, agent_context
- **Session**: session_close

### Available Resources
- `ztlctl://context` — full vault context
- `ztlctl://overview` — counts and recent items
- `ztlctl://work-queue` — prioritized task queue
- `ztlctl://topics` — topic directories
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
    """Register all 4 MCP prompts on the FastMCP server."""

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
