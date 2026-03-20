# Phase 3: MCP Surface Generation - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Auto-generate MCP tools from the ActionRegistry, replacing the hand-written `register_tools()` in `mcp/tools.py` (~1498 lines). Every ActionDefinition (all 59, including `custom_presentation` actions) becomes a discoverable MCP tool. Achieves full CLI/MCP parity (PLUG-04) and adds token-budget-aware responses for high-volume tools (AGNT-02). Resources and prompts (`mcp/resources.py`, `mcp/prompts.py`) are NOT in scope — they stay hand-written.

</domain>

<decisions>
## Implementation Decisions

### Tool generation strategy
- **Runtime generation at server startup** — iterate the ActionRegistry and call `server.tool()` for each ActionDefinition. No static codegen step. Matches the existing `_register_tool()` pattern but driven by registry data instead of a hand-written function list.
- **All 59 ActionDefinitions become MCP tools** — including the 5 `custom_presentation` actions (batch, init wizard, serve, workflow init/update). Thin wrappers call the handler directly. No parity gaps — agents can always discover every operation.
- **Context/dependency injection for Vault** — NOT closure binding. Vault lives on a context object (server-level or module-level) set once during `create_server()`. Generated tools access it via accessor rather than closing over it. Decouples tool functions from server setup.

### Migration & cleanup
- **Delete and replace `mcp/tools.py` entirely** — `_TOOL_CATALOG` is redundant (ActionDefinitions carry all metadata). 29 `_impl` functions are redundant (controllers handle orchestration). `register_tools()` is redundant (generator replaces it). Clean break, no zombie code.
- **Pydantic-based MCP response schema** — introduce Pydantic models for MCP response structure instead of raw dicts. ServiceResult (already Pydantic) gains MCP serialization capability via a base class method or static function. JSON schema generation derives from Pydantic model schemas. This replaces `_to_mcp_response()` and `COMMON_ERROR_RECOVERY` dict with typed, validated structures.
- **Single registration path via registry primitive** — the ActionRegistry exposes a registration mechanism (decorator or base class) that both built-in controllers AND plugins use identically. No separate `mcp_tool_contributions` path. Plugins register ActionDefinitions into the same registry. This unifies the plugin tool system with the core tool system before Phase 5 formalizes the plugin API.

### Testing approach
- **Both controller unit tests AND DummyServer integration tests** — controller tests verify business logic (already exist). MCP generation tests verify that the generator produces correct tool registrations from ActionDefinitions. DummyServer integration tests verify end-to-end tool execution through the generated layer. Replaces existing `_impl` function tests that will be deleted with `tools.py`.

### Claude's Discretion
- **DI implementation details** — whether to use FastMCP's built-in lifespan/dependency injection or a simpler module-level context pattern. Research FastMCP capabilities and pick the best fit for the single-vault-per-server reality.
- **Pydantic response model shape** — exact field structure, inheritance hierarchy, whether to extend ServiceResult or create a separate MCP response model. The key constraint is: Pydantic models for all schema definitions, with a method to convert to MCP-friendly output.
- **Registration primitive design** — decorator vs base class vs hybrid. Must work for both built-in `_register_core_actions()` and future plugin registrations. Can evolve further in Phase 5.
- **Token-budget implementation** — how truncation works for high-volume tools (list, search, vault_review, topic_packet). Per-tool opt-in vs universal, budget parameter naming, truncation strategy (AGNT-02).
- **Generator module organization** — file naming and module structure for the new MCP generation code.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ActionRegistry (generation source)
- `src/ztlctl/actions/definitions.py` — ActionParam + ActionDefinition frozen dataclasses with all MCP metadata fields (mcp_when_to_use, mcp_avoid_when, mcp_common_errors)
- `src/ztlctl/actions/registry.py` — ActionRegistry class with register/get/list_actions, singleton accessor
- `src/ztlctl/actions/_register_core.py` — All 59 built-in ActionDefinition registrations across 13 controllers

### Current MCP layer (to be replaced)
- `src/ztlctl/mcp/tools.py` — 1498 lines: _TOOL_CATALOG, 29 _impl functions, register_tools(), _register_tool(), _to_mcp_response(), COMMON_ERROR_RECOVERY
- `src/ztlctl/mcp/server.py` — create_server() integration point that calls register_tools(server, vault)
- `src/ztlctl/mcp/resources.py` — MCP resources (NOT in scope, stays hand-written)
- `src/ztlctl/mcp/prompts.py` — MCP prompts (NOT in scope, stays hand-written)

### Controller layer (tool handlers)
- `src/ztlctl/controllers/` — 13 controller files with factory lambda handlers registered in ActionDefinitions

### Service result (Pydantic base)
- `src/ztlctl/services/result.py` — ServiceResult frozen Pydantic model, the return type for all controller methods

### Requirements
- `.planning/REQUIREMENTS.md` — ACTN-03 (auto-generated MCP tools), AGNT-02 (token-budget responses), PLUG-04 (CLI/MCP parity)

### Prior phase context
- `.planning/phases/02-action-registry/02-CONTEXT.md` — Phase 2 decisions: 4-layer architecture, all-through-registry principle, no escape hatches

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ActionDefinition.mcp_when_to_use/mcp_avoid_when/mcp_common_errors`: All MCP metadata already captured per action — generator reads these directly
- `_render_tool_doc()` in tools.py: Produces rich docstrings from catalog entries — pattern can be adapted for ActionDefinition-driven docs
- `ServiceResult` (Pydantic): Already a frozen Pydantic model with ok/op/data/warnings/error fields — natural base for MCP response schema
- `DummyServer` test pattern from Phase 1: Call registered handlers on a mock server to test tool registration without mcp package

### Established Patterns
- **Factory lambda handlers**: `lambda vault, **kw: Controller(vault).method(**kw)` — each ActionDefinition.handler already accepts vault as first arg
- **Guarded mcp imports**: `try: import mcp... except ImportError` pattern in server.py — MCP generation code must maintain this optional-dependency guard
- **Plugin tool contributions**: `plugin_manager.mcp_tool_contributions(reserved_names=...)` — will be unified into ActionRegistry path

### Integration Points
- `mcp/server.py:create_server()` — the single integration point; currently calls `register_tools(server, vault)`, will call the new generator instead
- `actions/registry.py:get_action_registry()` — singleton accessor the generator reads from
- `plugins/hookspecs.py` — 16 hookspecs including `mcp_tool_contributions` that will be deprecated in favor of ActionRegistry registration

</code_context>

<specifics>
## Specific Ideas

- User explicitly wants Pydantic for all schema definitions — this is a broader pattern shift, not just MCP responses. MCP tool parameter schemas should derive from Pydantic models where possible.
- "The registry should expose functionality (either as a decorator or a base class) which we leverage to register actions. Plugins should leverage this functionality as well." — the registration mechanism must be a shared primitive, not just an internal API.
- The generator should produce tool functions with correct type annotations so FastMCP can derive JSON schema from Python signatures (current pattern relies on this).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-mcp-surface-generation*
*Context gathered: 2026-03-19*
