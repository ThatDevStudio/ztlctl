# Technology Stack

**Project:** ztlctl v2 — Plugin Formalization, Define-Once Actions, Agentic Integration
**Researched:** 2026-03-19

## Scope

This document covers **new** stack additions for v2. The existing stack (Python 3.13, Click, Pydantic, SQLAlchemy Core, pluggy, Rich, structlog, etc.) is established and unchanged. See `.planning/codebase/STACK.md` for the full baseline.

## Recommended Stack Additions

### Define-Once Action System

No external library. Build a custom `ActionRegistry` using Pydantic models and Python's type introspection.

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| None (custom) | — | Action definition and registry | No library solves this problem well. pydanclick (58 GitHub stars, 28 commits) is too immature for a production contract. The define-once pattern requires tight control over how Pydantic models map to both Click options and MCP tool schemas — this is a ~200-line metaclass/registry, not a framework problem. |

**Confidence:** HIGH — this is an architecture decision, not a library gap.

**The pattern:**
```python
class Action(BaseModel):
    """Base for all define-once actions."""
    model_config = ConfigDict(frozen=True)

class CreateNoteAction(Action):
    """Create a note in the vault."""
    title: str = Field(description="Human-readable note title")
    subtype: str | None = Field(None, description="Note subtype (knowledge, decision)")
    tags: list[str] = Field(default_factory=list, description="Domain/scope tags")
    body: str | None = Field(None, description="Markdown body content")
```

From a single `CreateNoteAction` model:
- **CLI:** Auto-generate Click options from Pydantic fields (Field metadata provides help text, types, defaults)
- **MCP:** Auto-generate tool schema from `model_json_schema()` (already how FastMCP works)
- **Validation:** Pydantic handles it in both surfaces
- **Execution:** `ActionRegistry.execute(action_instance)` routes to service layer

The existing `_impl` functions in `mcp/tools.py` (25 functions) already contain the service-calling logic. The v2 refactor promotes these into `Action` classes with Pydantic schemas, then generates CLI and MCP wrappers from the same source.

#### Why NOT pydanclick or similar

| Library | Stars | Status | Why Not |
|---------|-------|--------|---------|
| pydanclick | 58 | Low activity (28 commits) | Too thin for production contract; Click option generation is ~50 lines of custom code using `Field.metadata` |
| clidantic | ~100 | Stale | Replaces Click groups entirely — incompatible with existing Click architecture |
| clipstick | ~50 | Small | Not Click-based (argparse); wrong ecosystem |
| pydantic-cli | ~200 | Abandoned | No Pydantic v2 support |

**Confidence:** HIGH — evaluated all options; custom is the right call for this codebase.

### MCP SDK Upgrade

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `mcp` | `>=1.26.0` | Official MCP Python SDK | Current codebase uses `mcp>=1.0`. Upgrade to 1.26+ for Streamable HTTP transport (supersedes SSE), improved tool schemas, and protocol compliance. The SDK is now maintained by the Agentic AI Foundation (Linux Foundation). |

**Confidence:** HIGH — verified on PyPI (1.26.0 released 2026-01-24). Python >=3.10 required (ztlctl requires 3.13, no issue).

**Key changes in 1.26:**
- Streamable HTTP transport replaces SSE for production deployments
- Improved client/server lifecycle management
- Better error reporting in tool schemas

#### FastMCP Standalone — Do NOT Adopt

| Technology | Version | Status | Why Not |
|------------|---------|--------|---------|
| `fastmcp` (PrefectHQ) | 3.1.1 | Active | The standalone FastMCP diverged from the official SDK. ztlctl already uses FastMCP as bundled in the `mcp` package. Switching to the standalone would mean two competing MCP layers. The official SDK's built-in FastMCP is sufficient and avoids dependency sprawl. |

**Confidence:** HIGH — the official `mcp` package bundles FastMCP 1.x patterns; standalone FastMCP 3.x adds OpenAPI-to-MCP features ztlctl does not need.

### Plugin System Formalization

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| `pluggy` | `>=1.6.0` | Plugin hooks (existing, pin update) | Current pin is `>=1.4`. Upgrade to 1.6.0 (released 2025-05-15) for bugfixes. No API changes needed — pluggy's hookspec/hookimpl pattern is the right abstraction for ztlctl's plugin system. |

**Confidence:** HIGH — verified on PyPI.

**What pluggy already provides that v2 needs:**
- `hookspec(firstresult=True)` for short-circuit hooks (e.g., custom note type resolution)
- `tryfirst`/`trylast` for hook ordering (e.g., plugin CLI commands load after core)
- Entry-point discovery (already used in v1)
- `HookCallError` for debugging plugin failures

**What to build on top of pluggy (custom):**
- `ActionHookSpec` — pre/post hooks on every Action execution
- `NoteTypeContribution` — plugins register custom note types with lifecycle definitions
- `TemplateContribution` — plugins register Jinja2 template overrides
- These extend the existing `contracts.py` dataclasses (already 13 contribution types)

### Agentic Integration — Evaluation

| Technology | Version | Purpose | Recommendation |
|------------|---------|---------|----------------|
| OpenAI Agents SDK | 0.12.5 | Agent orchestration framework | **DO NOT ADOPT** — wrong layer |
| PydanticAI | 1.70.0 | Agent framework | **DO NOT ADOPT** — wrong layer |
| MCP (already adopted) | >=1.26.0 | Tool/resource protocol | **USE THIS** — correct abstraction |

**Confidence:** HIGH — this is an architectural decision backed by the project's core value statement.

**Rationale:** ztlctl is a *tool* that agents use, not an agent itself. The project constraint says "agents should only ever have to orchestrate the tool — not build custom functionality." This means:

1. **MCP is the agentic interface.** Agents connect via MCP protocol and use tools/resources/prompts. The v2 define-once pattern ensures complete MCP tool coverage with zero gaps.

2. **Agent SDKs are for agent builders**, not tool builders. OpenAI Agents SDK and PydanticAI help build agents that *consume* MCP tools. ztlctl's users may use these SDKs to build agents that orchestrate ztlctl — but ztlctl itself does not need them.

3. **Agent orchestration patterns** (the PROJECT.md requirement) means documenting how agents should sequence MCP tool calls (e.g., "research workflow: search -> get_document -> create_note -> reweave"). This is documentation, not a library dependency.

**Exception:** If a future milestone adds an *embedded agent* (e.g., `ztlctl agent synthesize` that calls an LLM to generate notes), then PydanticAI would be the right choice because it integrates with Pydantic's type system. But this is explicitly out of scope for v2.

## Supporting Libraries (No Changes)

These existing dependencies need no version changes or replacements:

| Library | Current Pin | Status | Notes |
|---------|-------------|--------|-------|
| Click | >=8.1 | Stable | CLI framework stays; Action system generates Click commands atop it |
| Pydantic | >=2.0 | Stable | Core of the Action system; `model_json_schema()` drives MCP schema generation |
| SQLAlchemy | >=2.0 | Stable | Core only; no ORM needed |
| NetworkX | >=3.0 | Stable | Graph algorithms unchanged |
| Rich | >=13.0 | Stable | Output formatting unchanged |
| structlog | >=24.0 | Stable | Telemetry unchanged |
| Jinja2 | >=3.1 | Stable | Template system unchanged |
| Copier | >=9.12.0 | Stable | Workflow templates unchanged |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Action→CLI generation | Custom (~200 LOC) | pydanclick | Immature (58 stars), doesn't handle Click groups, would add fragile dependency for something trivial to build |
| Action→MCP generation | Pydantic `model_json_schema()` | FastMCP standalone 3.x | Standalone diverges from official SDK; adds competing MCP layer |
| Plugin hooks | pluggy 1.6 | stevedore, yapsy | pluggy already adopted; stevedore is heavier; yapsy is abandoned |
| Agentic integration | MCP protocol (tool-side) | OpenAI Agents SDK | ztlctl is a tool, not an agent; SDK is wrong abstraction layer |
| Agentic integration | MCP protocol (tool-side) | PydanticAI | Same reason; correct only if ztlctl embeds an LLM agent (out of scope) |

## Version Pin Updates

```toml
# pyproject.toml changes
[project]
dependencies = [
    # ... existing deps unchanged ...
]

[project.optional-dependencies]
mcp = [
    "mcp>=1.26.0",   # was >=1.0; upgrade for Streamable HTTP
    "anyio>=4.0",
]
```

```bash
# Update commands
uv add "mcp>=1.26.0" --group mcp
```

No new runtime dependencies are introduced. The v2 work is primarily architectural (Action registry, auto-generated surfaces) built on the existing stack.

## Architecture Implications

### What Changes

1. **New `actions/` package** — Pydantic action models + registry (custom, ~500 LOC total)
2. **`commands/` refactored** — Click commands auto-generated from Action models instead of hand-coded
3. **`mcp/tools.py` refactored** — MCP tools auto-generated from same Action models; `_impl` functions become `Action.execute()` methods
4. **`plugins/contracts.py` extended** — New contribution types for note types, lifecycles, and actions
5. **`mcp` pin bumped** — >=1.26.0 for Streamable HTTP

### What Does NOT Change

- Click remains the CLI framework (actions generate Click commands, not replace Click)
- pluggy remains the plugin framework (extended, not replaced)
- ServiceResult remains the universal return type
- Vault repository pattern unchanged
- 6-layer architecture preserved (actions sit between services and commands/mcp)

## Sources

- [MCP Python SDK — PyPI](https://pypi.org/project/mcp/) — v1.26.0, verified 2026-03-19
- [FastMCP standalone — PyPI](https://pypi.org/project/fastmcp/) — v3.1.1, evaluated and rejected
- [pydanclick — GitHub](https://github.com/felix-martel/pydanclick) — 58 stars, evaluated and rejected
- [pluggy — PyPI](https://pypi.org/project/pluggy/) — v1.6.0, verified 2026-03-19
- [OpenAI Agents SDK — PyPI](https://pypi.org/project/openai-agents/) — v0.12.5, evaluated and rejected
- [PydanticAI — PyPI](https://pypi.org/project/pydantic-ai/) — v1.70.0, evaluated and rejected
- [MCP donated to Agentic AI Foundation](https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation) — protocol governance context
- [Streamable HTTP for MCP](https://blog.cloudflare.com/streamable-http-mcp-servers-python/) — transport evolution context
