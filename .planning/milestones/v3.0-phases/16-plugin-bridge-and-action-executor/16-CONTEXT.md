# Phase 16: Plugin Bridge and Action Executor - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Reverse the compatibility bridge so stable action events adapt into legacy hook calls (not legacy → stable). Introduce a generic action executor that replaces repeated pre/post hook boilerplate in controllers. Make `garden seed` a first-class action. Implement MCP server graceful shutdown. Pure internal architecture — no user-facing command changes.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Key constraints from architecture remediation design doc:
- Bridge reversal: stable action events → optional legacy hook adapters (not the reverse)
- Generic executor: reusable utility replacing repeated pre_action dispatch in controllers
- `garden seed` must exercise the same pre-action and post-commit machinery as other create flows
- MCP `ztlctl serve` must exit cleanly without dangling asyncio tasks when client disconnects

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture remediation design
- `.planning/research/2026-03-21-architecture-remediation-design.md` — §4 (reverse bridge), §6 (generic executor), §8 (command surface convergence)

### Event system (Phase 15 output)
- `src/ztlctl/plugins/event_bus.py` — Current EventBus with ActionEvent dispatch (modified in Phase 15)
- `src/ztlctl/services/base.py` — `_dispatch_post_action_event()` (added in Phase 15)
- `src/ztlctl/controllers/base.py` — `_dispatch_pre_action()` still exists; `_dispatch_post_action()` removed in Phase 15

### MCP server
- `src/ztlctl/mcp/server.py` — MCP server implementation, asyncio event loop

### Plugin system
- `src/ztlctl/plugins/hookspecs.py` — Legacy hookspec definitions
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — Uses post_action (stable API)
- `src/ztlctl/plugins/builtins/git.py` — Uses post_action (stable API)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `BaseController._dispatch_pre_action()` — existing pre-action dispatch, candidate for extraction into generic executor
- `ActionEvent` model from Phase 15 — canonical payload shape for bridge adaptation

### Established Patterns
- Controllers follow a consistent pattern: build kwargs → pre_action → service call → return result
- The EventBus bridge in `_execute_hook()` already handles `post_action` as a special path

### Integration Points
- `BaseController` → generic executor (replaces pre_action boilerplate)
- `EventBus._execute_hook()` bridge → reversal (stable → legacy adapters)
- `garden seed` command → first-class action through ActionRegistry
- `mcp/server.py` → graceful shutdown on client disconnect

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 16-plugin-bridge-and-action-executor*
*Context gathered: 2026-03-21*
