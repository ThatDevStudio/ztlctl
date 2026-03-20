# Phase 7: Plugin & Agentic Wiring Fixes - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Close all integration gaps identified by the v2.0 milestone audit: wire pre/post-action hooks into controller methods, connect plugin config injection to the initialization path, forward error detail through MCP responses, and clarify category activation semantics. This is a wiring-only phase — no new features, no new abstractions.

</domain>

<decisions>
## Implementation Decisions

### Pre/post-action hook wiring (PLUG-02)
- Wire `_dispatch_pre_action()` and `_dispatch_post_action()` into ALL controller methods (both read and write)
- Read-side hooks enable plugins to observe queries (audit logging, metrics) — not just mutations
- Pattern: call `_dispatch_pre_action(action_name, kwargs)` before service delegation; if rejection returned, convert to `ServiceResult` error with rejection reason and return early
- Pattern: call `_dispatch_post_action(action_name, kwargs, result)` after service returns, regardless of result.ok
- `create_batch` (custom_presentation, called directly from CLI) also needs hooks
- 14 concrete controllers × ~59 methods total need wiring — systematic, not selective

### Plugin config injection (PLUG-03)
- Add `pm.inject_configs(self._settings)` call in `vault.init_event_bus()` after `pm.discover_and_load()` and before built-in plugin registration
- Single initialization path — no secondary injection site needed
- Built-in plugins (GitPlugin, ReweavePlugin) don't use TOML config (they receive config via constructor), so ordering is safe

### Category activation semantics (AGNT-04)
- Category activation is **advisory metadata** — document this explicitly, do not implement tool gating
- Rationale: FastMCP does not support dynamic tool deregistration; gating would require server restart
- `discover_categories` returns active/inactive status; agents use this for tool selection heuristics
- Update REQUIREMENTS.md AGNT-04 description to clarify "activation" means "discovery metadata for agent tool selection" not "dynamic tool surface reduction"
- Add docstring/comment in generator.py explaining the advisory-only design decision

### Error detail forwarding (AGNT-01)
- Forward `result.error.detail` to `McpError.detail` in `McpResponse.from_result()` — one-line fix
- Forward all fields — no selective filtering (agents parse what they need)

### Claude's Discretion
- Exact ServiceResult error code for ActionRejection (suggest "ACTION_REJECTED" or similar)
- Whether to add a COMMON_ERROR_RECOVERY entry for the rejection error code
- Test organization (new test files vs extending existing)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Audit findings
- `.planning/v2.0-MILESTONE-AUDIT.md` — Full gap descriptions, broken flows, fix suggestions

### Controller layer
- `src/ztlctl/controllers/base.py` — BaseController with _dispatch_pre_action/_dispatch_post_action (the methods that need to be called)
- `src/ztlctl/controllers/create.py` — Example of current pattern (direct service delegation, no hook calls)

### Plugin system
- `src/ztlctl/plugins/hookspecs.py` — pre_action (firstresult=True), post_action hookspec definitions
- `src/ztlctl/plugins/contracts.py` — ActionRejection frozen dataclass
- `src/ztlctl/plugins/manager.py` — inject_configs() method, _inject_plugin_configs() implementation

### Initialization path
- `src/ztlctl/infrastructure/vault.py` lines 361-388 — init_event_bus() where inject_configs() needs to be added

### MCP response
- `src/ztlctl/mcp/response.py` lines 140-164 — from_result() where detail forwarding is needed
- `src/ztlctl/mcp/generator.py` lines 80-110 — Category activation state and _active_categories

### Action registry
- `src/ztlctl/actions/_register_core.py` — All 59 ActionDefinition registrations (action_name values needed for hook wiring)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BaseController._dispatch_pre_action()` — Fully implemented, handles ActionRejection/dict/None returns
- `BaseController._dispatch_post_action()` — Fully implemented, catches exceptions
- `PluginManager.inject_configs()` — Fully implemented with Pydantic validation and error handling
- `McpError.detail` field — Already exists as `dict[str, Any]` with default_factory=dict

### Established Patterns
- Controllers construct services per-call: `XService(self._vault).method(...)` — hooks wrap this pattern
- Controllers use lazy local imports for service classes
- All controller methods return `ServiceResult`
- Plugin failures are warnings, never errors (DEBUG logging for exceptions)

### Integration Points
- `vault.init_event_bus()` — Single insertion point for inject_configs()
- `McpResponse.from_result()` — Single insertion point for detail forwarding
- 14 controller files × ~59 public methods — systematic wiring needed
- `_register_core.py` — Source of truth for action names (used in _dispatch_pre_action calls)

</code_context>

<specifics>
## Specific Ideas

No specific requirements — the audit findings precisely define what needs to change. This is mechanical wiring work, not design work.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-plugin-agentic-wiring-fixes*
*Context gathered: 2026-03-20*
