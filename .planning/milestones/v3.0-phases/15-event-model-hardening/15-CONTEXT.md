# Phase 15: Event Model Hardening - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Make event delivery reliable for normal CLI usage: WAL drain on shutdown, startup recovery of pending events, service-only post_action emission, canonical payload model, configurable EventBus timeout, and dead-letter resolution. This phase fixes correctness — no user-facing command changes.

</domain>

<decisions>
## Implementation Decisions

### Shutdown drain behavior
- **D-01:** CLI shutdown waits for write-side event completion with a bounded timeout (default 5 seconds, configurable via `[eventbus].shutdown_timeout_seconds`)
- **D-02:** After timeout, pending events remain in WAL as `pending` status — they are NOT cancelled or discarded
- **D-03:** `AppContext.close()` changes from `wait_for_events=False` to `wait_for_events=True` with the bounded timeout
- **D-04:** Read-only commands (query, list, search) skip event drain entirely — only write-side commands trigger drain

### Startup recovery
- **D-05:** On vault open, pending/failed WAL events from prior runs are drained synchronously before the command proceeds
- **D-06:** Startup drain uses the same bounded timeout as shutdown drain
- **D-07:** If startup drain times out, log a warning and continue — never block the user indefinitely

### Service-only post_action emission
- **D-08:** Services emit `post_action` after successful write commits — this is the single canonical producer
- **D-09:** `BaseController._dispatch_post_action()` is removed for write actions (52 call sites across 14 controllers)
- **D-10:** For read actions (query, list, search, etc.), no `post_action` is emitted — read-side hooks are not in scope for this phase
- **D-11:** Single-step cutover — no deprecation window needed since this is an internal change; both built-in plugins already guard for `result=None`

### Canonical action-event payload
- **D-12:** New Pydantic model `ActionEvent` with fields: `action_name: str`, `side_effect: Literal["write", "read"]`, `payload: dict[str, Any]`, `warnings: list[str]`
- **D-13:** `payload` dict contains committed state: `id`, `type`, `title`, `path`, `fields_changed`, `session_id` — action-specific fields vary but always include `id` and `type`
- **D-14:** `result` field carries the full `ServiceResult` — plugins receive committed output, not raw input kwargs
- **D-15:** EventBus WAL stores the serialized `ActionEvent` as the payload column value

### EventBus timeout configuration
- **D-16:** New `[eventbus]` section in config models with: `shutdown_timeout_seconds` (default 5), `max_retries` (default 3), `dead_letter_retention_days` (default 30)
- **D-17:** EventBus constructor reads config from vault settings instead of hardcoded values
- **D-18:** Per-future timeout in `_wait_futures()` becomes configurable (currently hardcoded 30s)

### Dead-letter resolution
- **D-19:** Dead-letter events reported in `ztlctl check` output under `CAT_STRUCTURAL` at info severity
- **D-20:** Auto-purge dead-letters older than `dead_letter_retention_days` during startup drain
- **D-21:** New `event_purge` action to manually clear dead-letter events (registered in ActionRegistry)

### Claude's Discretion
- Exact Pydantic model field names and validation rules for ActionEvent
- Whether startup drain runs in a thread or blocks the main thread
- Logging verbosity for drain operations (structlog integration)
- Test fixture design for slow-plugin simulation

</decisions>

<specifics>
## Specific Ideas

No specific requirements — decisions are driven by the architecture remediation design doc and codebase analysis.

</specifics>

<canonical_refs>
## Canonical References

### Architecture remediation design
- `.planning/research/2026-03-21-architecture-remediation-design.md` — Full remediation design doc; §1 (event delivery), §2 (two producers), §5 (CLI teardown)
- `.planning/research/2026-03-21-architecture-remediation-design.md` §3 — Canonical action-event payload shape specification

### Event system implementation
- `src/ztlctl/plugins/event_bus.py` — Current EventBus with WAL, dispatch, drain, shutdown; hardcoded 30s timeout at line 261; bridge pattern at lines 208-221
- `src/ztlctl/plugins/hookspecs.py` — `post_action` hookspec signature (stable API)
- `src/ztlctl/controllers/base.py` — `_dispatch_post_action()` at lines 84-102 (to be removed for write actions)

### Teardown and lifecycle
- `src/ztlctl/commands/_context.py` — `AppContext.close()` at lines 107-111; `wait_for_events=False` is the current behavior
- `src/ztlctl/infrastructure/vault.py` — Vault init/close, event bus initialization
- `src/ztlctl/services/session.py` — SessionService.close() drain logic at lines 201-219

### Plugin consumers
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — ReweavePlugin post_action handler; guards `result is None or not result.ok`
- `src/ztlctl/plugins/builtins/git.py` — GitPlugin post_action handler; routes by action_name, extracts kwargs

### Config model
- `src/ztlctl/config/models.py` — No EventBus section currently; new `[eventbus]` section needed

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `EventBus.drain(event_ids)` — existing drain method that retries pending/failed events; extend for startup drain
- `EventBus._wait_futures()` — existing timeout loop; make configurable
- `BaseService._dispatch_event()` — existing per-event hook dispatch; extend to also emit canonical post_action
- WAL table schema already has `status`, `retries`, `created`, `completed` columns — sufficient for dead-letter tracking

### Established Patterns
- **ServiceResult**: frozen Pydantic model returned by all service methods — will be carried in canonical payload
- **ContextVar telemetry**: `_verbose_enabled` + `_current_span` pattern for zero-signature-change propagation — can apply to event metadata
- **Config models**: Pydantic BaseSettings with TOML discovery — follow same pattern for `[eventbus]` section
- **CAT_STRUCTURAL checks**: existing category in CheckService — dead-letter reporting fits naturally here

### Integration Points
- `AppContext.close()` → `Vault.close(wait_for_events=True, timeout=config.shutdown_timeout_seconds)`
- `Vault.__init__()` or `Vault.open()` → startup drain of pending WAL events
- `BaseService._dispatch_event()` → also emit `ActionEvent` as canonical post_action
- `BaseController._dispatch_post_action()` → remove all 52 write-action call sites
- `CheckService._check_structural()` → add dead-letter event count reporting
- `config/models.py` → new `EventBusConfig` Pydantic model

</code_context>

<deferred>
## Deferred Ideas

- Bridge reversal (stable → legacy adapters) — Phase 16 (ARCH-05)
- Generic action executor replacing controller boilerplate — Phase 16 (ARCH-06)
- MCP graceful shutdown — Phase 16 (DEBT-04)
- Read-side post_action hooks — not in any current phase scope; evaluate if needed later

</deferred>

---

*Phase: 15-event-model-hardening*
*Context gathered: 2026-03-21*
