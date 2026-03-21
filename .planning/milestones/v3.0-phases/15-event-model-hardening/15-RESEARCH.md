# Phase 15: Event Model Hardening - Research

**Researched:** 2026-03-21
**Domain:** Python async event dispatch, WAL-backed durability, Pydantic models, pluggy hookspecs
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** CLI shutdown waits for write-side event completion with a bounded timeout (default 5 seconds, configurable via `[eventbus].shutdown_timeout_seconds`)
- **D-02:** After timeout, pending events remain in WAL as `pending` status — they are NOT cancelled or discarded
- **D-03:** `AppContext.close()` changes from `wait_for_events=False` to `wait_for_events=True` with the bounded timeout
- **D-04:** Read-only commands (query, list, search) skip event drain entirely — only write-side commands trigger drain
- **D-05:** On vault open, pending/failed WAL events from prior runs are drained synchronously before the command proceeds
- **D-06:** Startup drain uses the same bounded timeout as shutdown drain
- **D-07:** If startup drain times out, log a warning and continue — never block the user indefinitely
- **D-08:** Services emit `post_action` after successful write commits — this is the single canonical producer
- **D-09:** `BaseController._dispatch_post_action()` is removed for write actions (52 call sites across 14 controllers)
- **D-10:** For read actions (query, list, search, etc.), no `post_action` is emitted — read-side hooks are not in scope for this phase
- **D-11:** Single-step cutover — no deprecation window needed since this is an internal change; both built-in plugins already guard for `result=None`
- **D-12:** New Pydantic model `ActionEvent` with fields: `action_name: str`, `side_effect: Literal["write", "read"]`, `payload: dict[str, Any]`, `warnings: list[str]`
- **D-13:** `payload` dict contains committed state: `id`, `type`, `title`, `path`, `fields_changed`, `session_id` — action-specific fields vary but always include `id` and `type`
- **D-14:** `result` field carries the full `ServiceResult` — plugins receive committed output, not raw input kwargs
- **D-15:** EventBus WAL stores the serialized `ActionEvent` as the payload column value
- **D-16:** New `[eventbus]` section in config models with: `shutdown_timeout_seconds` (default 5), `max_retries` (default 3), `dead_letter_retention_days` (default 30)
- **D-17:** EventBus constructor reads config from vault settings instead of hardcoded values
- **D-18:** Per-future timeout in `_wait_futures()` becomes configurable (currently hardcoded 30s)
- **D-19:** Dead-letter events reported in `ztlctl check` output under `CAT_STRUCTURAL` at info severity
- **D-20:** Auto-purge dead-letters older than `dead_letter_retention_days` during startup drain
- **D-21:** New `event_purge` action to manually clear dead-letter events (registered in ActionRegistry)

### Claude's Discretion

- Exact Pydantic model field names and validation rules for ActionEvent
- Whether startup drain runs in a thread or blocks the main thread
- Logging verbosity for drain operations (structlog integration)
- Test fixture design for slow-plugin simulation

### Deferred Ideas (OUT OF SCOPE)

- Bridge reversal (stable → legacy adapters) — Phase 16 (ARCH-05)
- Generic action executor replacing controller boilerplate — Phase 16 (ARCH-06)
- MCP graceful shutdown — Phase 16 (DEBT-04)
- Read-side post_action hooks — not in any current phase scope; evaluate if needed later
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARCH-01 | Event delivery is reliable — WAL rows drain on CLI shutdown with bounded timeout | D-01/D-02/D-03: `AppContext.close()` passes timeout to `Vault.close()`; `EventBus.shutdown()` calls `_wait_futures()` with bounded timeout before returning; unfinished futures leave WAL rows as `pending` not cancelled |
| ARCH-02 | Pending/failed WAL events from prior runs drain on startup before new work begins | D-05/D-06/D-07: `Vault.init_event_bus()` or `AppContext.vault` lazy-init calls `EventBus.drain()` synchronously; uses same configurable timeout; log warning and continue on timeout |
| ARCH-03 | Write-side `post_action` is emitted by services only — controller-side dispatch removed | D-08/D-09/D-11: `BaseService._dispatch_event()` extended to emit `post_action` after write commit; `BaseController._dispatch_post_action()` removed from all 52 write-action call sites across 14 controllers; single-step cutover |
| ARCH-04 | Canonical action-event payload model with stable shape (`action_name`, `side_effect`, `payload`, `warnings`) | D-12/D-13/D-14/D-15: new `ActionEvent` Pydantic model; services populate it post-commit; WAL stores serialized form; plugins receive committed output |
| DEBT-02 | EventBus timeout configurable via settings | D-16/D-17/D-18: new `EventBusConfig` in `config/models.py`; injected into `EventBus.__init__`; replaces hardcoded 30s in `_wait_futures()` |
| DEBT-03 | Dead-letter event accumulation resolved | D-19/D-20/D-21: `CheckService._check_structural_validation()` reports dead-letters; startup drain auto-purges old dead-letters; `event_purge` action in ActionRegistry |
</phase_requirements>

---

## Summary

Phase 15 hardens the event delivery system across three axes: reliability (shutdown/startup drain), correctness (single canonical producer), and observability (dead-letter reporting and purge). All changes are internal — no user-facing commands change. The phase operates on already-deployed infrastructure: a WAL-backed `EventBus` with `ThreadPoolExecutor` dispatch, a `BaseService._dispatch_event()` method used by all services, and `BaseController._dispatch_post_action()` currently called at 52 write-action sites in 14 controllers.

The current system has two `post_action` producers: controllers dispatch it directly with raw input kwargs, and the EventBus bridge fires it again from the legacy lifecycle event path (with committed payload but `result=None`). Both built-in plugins (GitPlugin, ReweavePlugin) already guard for `result=None`, which confirms they depend on the bridge path rather than the controller path. The cutover eliminates the controller-side dispatch for write actions; services become the sole producer by emitting a canonical `ActionEvent` after a successful write transaction commits.

Shutdown drain is the central behavioral change. Today `AppContext.close()` calls `vault.close(wait_for_events=False)`, which discards in-flight ThreadPoolExecutor futures and leaves WAL rows as `pending`. After this phase, `AppContext.close()` passes a bounded timeout; `EventBus.shutdown()` waits up to that timeout for futures to resolve, then returns — leaving any remaining rows as `pending` for startup recovery rather than cancelling them.

**Primary recommendation:** Implement in four work streams — (1) config model + EventBus constructor, (2) ActionEvent model + service emission, (3) shutdown/startup drain, (4) dead-letter check + purge action — with regression tests gating each stream.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pluggy | already installed | hookspec/hookimpl dispatch | Already the ztlctl plugin system |
| pydantic | already installed (v2) | `ActionEvent` model validation | All service contracts use Pydantic v2 |
| pydantic-settings | already installed | `EventBusConfig` section | All config sections follow this pattern |
| sqlalchemy | already installed (Core) | WAL reads/writes | Already owns the `event_wal` table |
| concurrent.futures | stdlib | `ThreadPoolExecutor` + `Future.result(timeout=...)` | Already used in EventBus; `Future.result(timeout=N)` is the bounded wait primitive |
| structlog | already installed | drain/shutdown log output | Already used for all service-layer logging |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| threading | stdlib | startup drain thread decision | Only if startup drain is run async; research recommends blocking main thread (see Architecture Patterns) |
| datetime / timedelta | stdlib | dead-letter retention age check | `dead_letter_retention_days` purge during startup drain |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Blocking startup drain in main thread | Background thread with join | Background thread adds complexity; for CLI one-shot usage, a bounded synchronous drain is simpler and correct |
| Single `Future.result(total_budget)` call | Per-future timeout in loop | Per-future timeout is the existing pattern and handles partial completion better |

**No new dependencies required for this phase.** All primitives are already in the project.

---

## Architecture Patterns

### Recommended Project Structure

No new files/folders required. Existing structure absorbs all changes:

```
src/ztlctl/
├── config/
│   └── models.py              # ADD: EventBusConfig model
├── plugins/
│   ├── event_bus.py           # MODIFY: configurable timeout, startup drain, canonical dispatch
│   └── contracts.py           # ADD: ActionEvent model (or domain/events.py)
├── infrastructure/
│   └── vault.py               # MODIFY: startup drain in init_event_bus / open
├── commands/
│   └── _context.py            # MODIFY: close() passes timeout
├── services/
│   └── base.py                # MODIFY: _dispatch_event emits ActionEvent post_action
├── controllers/
│   ├── base.py                # MODIFY: remove _dispatch_post_action (keep _dispatch_pre_action)
│   ├── create.py              # MODIFY: remove 4 _dispatch_post_action calls
│   ├── update.py              # MODIFY: remove 3 calls
│   ├── session.py             # MODIFY: remove 9 calls (write actions only)
│   ├── check.py               # MODIFY: remove 4 calls
│   ├── reweave.py             # MODIFY: remove 3 calls
│   └── [9 other controllers]  # MODIFY: remove write-action calls
└── actions/
    └── _register_core.py      # ADD: event_purge ActionDefinition
```

### Pattern 1: EventBusConfig in config/models.py

**What:** New frozen Pydantic model following the exact same pattern as all other config sections (`VaultConfig`, `CheckConfig`, etc.)

**When to use:** Whenever EventBus needs a setting

```python
# Source: src/ztlctl/config/models.py (existing pattern)
class EventBusConfig(BaseModel):
    """[eventbus] section."""

    model_config = {"frozen": True}

    shutdown_timeout_seconds: float = 5.0
    max_retries: int = 3
    dead_letter_retention_days: int = 30
    per_future_timeout_seconds: float = 30.0  # replaces hardcoded 30 in _wait_futures
```

Then add to `ZtlSettings` in `settings.py`:
```python
eventbus: EventBusConfig = Field(default_factory=EventBusConfig)
```

**IMPORTANT:** `ZtlSettings` is frozen. EventBus receives the config at construction time via `Vault.init_event_bus()`. Do not attempt to modify settings post-construction.

### Pattern 2: ActionEvent Pydantic Model

**What:** Canonical payload model for write-side post-commit events. Lives in `src/ztlctl/plugins/contracts.py` (where other plugin contracts live) or a new `src/ztlctl/domain/events.py`.

**When to use:** Emitted by `BaseService._dispatch_event()` after every successful write transaction.

```python
# Source: CONTEXT.md D-12, D-13, D-14
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel

class ActionEvent(BaseModel):
    """Canonical post-commit action event payload."""

    model_config = {"frozen": True}

    action_name: str
    side_effect: Literal["write", "read"] = "write"
    payload: dict[str, Any]   # committed state: id, type, title, path, fields_changed, session_id
    warnings: list[str] = []
    result: Any = None         # carries full ServiceResult (D-14)
```

The WAL stores `ActionEvent.model_dump_json()` as the `payload` column. When EventBus fires `post_action`, it passes:
- `action_name=event.action_name`
- `kwargs=event.payload`  (stable committed state, not raw controller kwargs)
- `result=event.result`

### Pattern 3: Service-Side Emission via BaseService._dispatch_event

**What:** `BaseService._dispatch_event()` is extended (or a new `_dispatch_post_action()` method added) to construct an `ActionEvent` and fire `post_action` directly via the plugin manager — not via the WAL EventBus path.

**Decision:** The service emits `post_action` through the same `EventBus.dispatch()` mechanism used for legacy hooks, but with `hook_name="post_action"` and an `ActionEvent` payload. The WAL row stores the canonical payload.

**Alternative approach (recommended for simplicity):** Services emit `post_action` by calling `pm.hook.post_action(...)` directly (bypassing the WAL), consistent with how `BaseController._dispatch_post_action()` currently works. The WAL already tracks the per-event hook (e.g., `post_create`). Adding a second WAL row for `post_action` would create redundancy.

**Recommended approach given D-15 ("WAL stores serialized ActionEvent as payload column value"):** The existing legacy hook WAL row's payload IS replaced with or augmented by the ActionEvent. The cleanest implementation:

1. Services call `_dispatch_post_action(action_name, action_event)` on BaseService after successful commit
2. This calls `EventBus.dispatch("post_action", action_event.model_dump(), ...)` — written to WAL as a proper durably-tracked async event
3. The legacy hook dispatch (`post_create` etc.) from services ALSO continues, keeping the bridge functional until Phase 16 removes it

**Simpler alternative:** Fold the ActionEvent dispatch into the existing per-event WAL row by storing the ActionEvent as the payload, and updating `_execute_hook` to call `post_action` directly instead of via the bridge. This avoids doubling WAL rows.

Given D-15 and the desire to avoid bridge duplication, the recommended implementation:
- Services construct `ActionEvent` and call a new `_dispatch_post_action_event()` on `BaseService`
- That method calls `EventBus.dispatch_post_action(event)` — a new method that writes one WAL row with `hook_name="post_action"` and the serialized ActionEvent as payload
- The bridge in `_execute_hook` is kept until Phase 16 for legacy hook compatibility
- Controller `_dispatch_post_action()` for write actions is removed (they would produce duplicates)

### Pattern 4: Bounded Shutdown Drain

**What:** `AppContext.close()` passes a timeout to `Vault.close()`. `Vault.close()` passes it to `EventBus.shutdown()`. `EventBus.shutdown()` calls `_wait_futures(timeout=N)` before handing off to `executor.shutdown()`.

**Current state (lines 107-111 in `_context.py`):**
```python
def close(self) -> None:
    if self._vault is not None:
        # Keep command teardown non-blocking for async plugin dispatch.
        self._vault.close(wait_for_events=False)
```

**After:**
```python
def close(self) -> None:
    if self._vault is not None:
        timeout = self.settings.eventbus.shutdown_timeout_seconds
        self._vault.close(wait_for_events=True, timeout=timeout)
```

`Vault.close()` signature change:
```python
def close(self, *, wait_for_events: bool = True, timeout: float | None = None) -> None:
    if self._event_bus is not None:
        try:
            self._event_bus.shutdown(wait=wait_for_events, timeout=timeout)
        except Exception:
            ...
```

`EventBus._wait_futures()` signature change:
```python
def _wait_futures(
    self,
    *,
    event_ids: set[int] | None = None,
    timeout: float | None = None,   # per-future timeout; None = use config default
) -> None:
    per_future_timeout = timeout if timeout is not None else self._per_future_timeout
    for event_id, future in self._futures:
        ...
        try:
            future.result(timeout=per_future_timeout)
        except Exception:
            pass
```

**D-04 — read-only commands skip drain:** `AppContext` is the single teardown point. Since all commands go through `AppContext.close()`, the read/write distinction can be tracked with a flag set on `AppContext` when a write-side command runs, OR the drain can simply always run (it is a no-op if `_futures` is empty). The simplest approach: always run the drain but make it effectively free for read commands because they produce no events and `_futures` is empty.

### Pattern 5: Startup Recovery Drain

**What:** On vault initialization (when `init_event_bus()` is called), drain any `pending` or `failed` WAL rows from prior process runs before the command begins.

**Where:** At the end of `Vault.init_event_bus()`, after the EventBus is wired up.

```python
def init_event_bus(self, *, sync: bool = False) -> None:
    # ... existing plugin/bus construction ...
    self._event_bus = EventBus(self._engine, pm, sync=sync, config=self._settings.eventbus)

    # Startup recovery: drain pending/failed events from prior runs
    timeout = self._settings.eventbus.shutdown_timeout_seconds
    try:
        self._event_bus.drain_with_timeout(timeout=timeout)
    except Exception:
        logger.warning("Startup drain timed out or failed; continuing")
```

**Claude's Discretion — main thread vs background thread:** Block the main thread. For CLI one-shot usage, a user running `ztlctl create note "X"` expects any pending `post_create` hooks from the last run to complete before new work begins. The timeout prevents indefinite blocking. A background thread would require a join before shutdown anyway, adding complexity with no benefit.

### Pattern 6: Dead-Letter Reporting in CheckService

**What:** `_check_structural_validation()` queries the WAL for `dead_letter` rows and reports them as `SEVERITY_INFO` issues.

**Note on severity:** `SEVERITY_INFO` does not currently exist in `check.py`. The constants are:
- `SEVERITY_ERROR = "error"`
- `SEVERITY_WARNING = "warning"`

Decision D-19 says "info severity." The implementation should either add `SEVERITY_INFO = "info"` (with appropriate rank) or use `SEVERITY_WARNING` with a distinct message. Adding `SEVERITY_INFO` is cleaner and maps to the "advisory, not blocking" nature of dead-letter accumulation.

```python
# In CheckService._check_structural_validation()
from ztlctl.infrastructure.database.schema import event_wal
from sqlalchemy import func

dead_letter_count = conn.execute(
    select(func.count()).where(event_wal.c.status == "dead_letter")
).scalar_one()

if dead_letter_count > 0:
    issues.append({
        "category": CAT_STRUCTURAL,
        "severity": SEVERITY_INFO,  # new constant
        "message": f"{dead_letter_count} dead-letter event(s) in WAL. Run 'ztlctl event purge' to clear.",
        "fix_action": "event_purge",
    })
```

### Pattern 7: event_purge Action Registration

**What:** New `event_purge` action registered in `_register_core.py` following the exact same `ActionDefinition` + `ActionParam` pattern as all other actions.

**Controller:** New method on a relevant controller (e.g., `CheckController` or a new minimal `EventController`). Since event management relates to vault maintenance, `CheckController` is the cleanest home.

```python
# In CheckController or a new EventController
def event_purge(self, *, older_than_days: int = 30) -> ServiceResult:
    """Purge dead-letter events older than N days from the WAL."""
    ...
```

**Implementation logic:** Query `event_wal` for rows with `status = "dead_letter"` and `created` older than `older_than_days` days. Delete them. Return count in ServiceResult.

### Anti-Patterns to Avoid

- **Double WAL rows:** Do not write both a legacy hook WAL row AND a `post_action` WAL row for the same service write. Choose one authoritative WAL row per commit. If keeping legacy hooks (for bridge compatibility until Phase 16), emit the ActionEvent's `post_action` directly through the plugin manager without a WAL row, or fold it into the same legacy row by updating the payload schema.
- **Cancelling futures at timeout:** D-02 is explicit — pending events must NOT be cancelled or discarded. After timeout, leave them as WAL `pending` rows and return. Do not call `executor.shutdown(cancel_futures=True)`.
- **Blocking in plugin hooks:** Plugin hooks run in the ThreadPoolExecutor thread, not the main thread. Slow hooks that exceed the shutdown timeout leave WAL rows for startup recovery — this is the intended behavior.
- **Modifying frozen ZtlSettings:** Use `EventBusConfig` values at construction time. EventBus stores `self._shutdown_timeout`, `self._per_future_timeout`, `self._max_retries` from the config passed at construction.
- **Dispatching post_action for read actions:** D-10 is explicit. Controllers like `QueryController`, `GraphController` have `_dispatch_post_action()` calls. These should be removed (not migrated to service-side emission) as part of the write-action call site cleanup.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bounded future wait | Custom polling loop | `Future.result(timeout=N)` from stdlib `concurrent.futures` | Already used; `TimeoutError` is the natural signal |
| Pydantic v2 JSON serialization | Custom serializer | `model.model_dump()` / `model.model_dump_json()` | Already used for all ServiceResult and contract models |
| Config section | Custom TOML parsing | `pydantic.BaseModel` with `frozen=True` + `Field` | All other config sections use this exact pattern |
| Datetime age check for dead-letters | Custom datetime logic | `datetime.fromisoformat(created) < datetime.now() - timedelta(days=N)` | Standard stdlib; `now_iso()` helper already in `services/_helpers.py` |
| ThreadPoolExecutor timeout | `threading.Timer` or custom signal | `Future.result(timeout=per_future_timeout)` in loop | Already the pattern in `_wait_futures()` |

**Key insight:** Every primitive needed (WAL drain, future wait, config model, JSON serialization) already exists in the codebase. This phase is about wiring them together correctly, not building new infrastructure.

---

## Common Pitfalls

### Pitfall 1: Double post_action delivery to built-in plugins

**What goes wrong:** After adding service-side `post_action` emission, the EventBus bridge in `_execute_hook()` also fires `post_action` for the same event. GitPlugin and ReweavePlugin receive the hook twice per write action.

**Why it happens:** The bridge at lines 208-221 of `event_bus.py` fires unconditionally for all legacy lifecycle hooks. If services now also emit `post_action` directly, and legacy hooks are still emitted (for Phase 16 compatibility), double delivery occurs.

**How to avoid:** Two strategies:
1. Remove controller-side `_dispatch_post_action()` calls AND change services to emit `post_action` directly via `pm.hook.post_action()` (not through EventBus), keeping the legacy hook dispatch path via EventBus for bridge compatibility. In this model: services call `pm.hook.post_action(...)` synchronously, and also call `bus.dispatch("post_create", ...)` for WAL durability of the legacy hook.
2. Remove the bridge from `_execute_hook()` entirely in Phase 15 (since D-11 says "single-step cutover" and built-in plugins already guard for `result=None`). Services emit `post_action` via EventBus with canonical ActionEvent payload. No more bridge. Legacy hooks remain for third-party plugin compat but no longer trigger `post_action`.

**Strategy 2 is preferred** given D-11 explicitly removes the need for a deprecation window.

**Warning signs:** `ReweavePlugin.post_action()` runs twice for one create action. Track by logging the number of `post_action` calls received per `action_name` in tests.

### Pitfall 2: Startup drain running on every vault access (not just first open)

**What goes wrong:** If startup drain is placed in `Vault.__init__()` instead of `Vault.init_event_bus()`, it runs before the plugin manager is initialized — meaning `drain()` calls `_execute_hook()` but `self._pm` is None.

**Why it happens:** `init_event_bus()` is called lazily from `AppContext.vault` (the property), not from `Vault.__init__()`. Drain must happen after the plugin manager and event bus are both initialized.

**How to avoid:** Place startup drain at the end of `Vault.init_event_bus()`, after `self._event_bus = EventBus(...)`.

**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'hook'` during startup drain.

### Pitfall 3: Controller call sites for read-only actions

**What goes wrong:** When removing `_dispatch_post_action()` from controllers, accidentally removing it from actions that are "mostly write but sometimes read" (e.g., `session status`, `session context`), or failing to remove it from clearly read-only actions like `QueryController.search()`, `GraphController.related()`.

**Why it happens:** The 52 call sites span write and read controllers. D-09 says "remove for write actions." D-10 says no `post_action` for reads. This means ALL 52 call sites should be removed (writes migrate to service-side; reads are dropped entirely per D-10).

**How to avoid:** Remove ALL `_dispatch_post_action()` calls from ALL controllers. The service layer handles write-side emission. Read-side gets nothing (D-10). Then delete `BaseController._dispatch_post_action()` itself.

**Warning signs:** Controllers in `query.py`, `graph.py` still calling `_dispatch_post_action()` after the refactor.

### Pitfall 4: Frozen ZtlSettings breaks EventBus config injection

**What goes wrong:** `ZtlSettings` is frozen (`model_config = {"frozen": True}`). Attempting to pass `vault.settings` to `EventBus` and then mutate it fails. This is not a problem if EventBus reads what it needs at construction time.

**Why it happens:** Known codebase pattern (MEMORY.md: "Frozen Pydantic models can't be mocked with patch.object").

**How to avoid:** `EventBus.__init__()` accepts `config: EventBusConfig` and extracts values into `self._shutdown_timeout`, `self._max_retries`, etc. Tests override via TOML config file, not by patching ZtlSettings attributes.

**Warning signs:** `pydantic.ValidationError` or `FrozenInstanceError` during test setup.

### Pitfall 5: WAL startup drain reprocesses events from the current run

**What goes wrong:** If a service emits a WAL event, then startup drain runs again (e.g., in a test that creates a vault twice), the newly-added `pending` event from this run gets drained before the ThreadPoolExecutor picks it up.

**Why it happens:** `drain()` without filtering picks up all `pending` and `failed` rows — including ones just dispatched.

**How to avoid:** Add a `created_before: str | None` parameter to `EventBus.drain()`. Startup drain passes `created_before=now_iso()` (the moment vault was opened), so only pre-existing WAL rows are drained — not events from the current process.

**Warning signs:** Events processed synchronously during startup even though they were just dispatched by this run.

### Pitfall 6: _wait_futures timeout causes TimeoutError not being caught

**What goes wrong:** `Future.result(timeout=N)` raises `concurrent.futures.TimeoutError` (not `TimeoutError`). The existing `except Exception: pass` in `_wait_futures` catches it, but if timeout is treated as a fatal error elsewhere, the behavior is wrong.

**Why it happens:** Python's `concurrent.futures.TimeoutError` is a subclass of `Exception` (Python 3.11+: it's `concurrent.futures.TimeoutError`, distinct from `TimeoutError`).

**How to avoid:** Keep `except Exception: pass` in the futures loop. After the loop, check if any futures are still incomplete (non-done). Log a structlog WARNING with count of unfinished futures so the user knows events will be recovered on next startup.

**Warning signs:** Silent failures that look like events were delivered when they weren't.

---

## Code Examples

Verified patterns from the codebase:

### EventBus._wait_futures with timeout parameter (current + proposed)

```python
# Source: src/ztlctl/plugins/event_bus.py lines 253-264 (current)
def _wait_futures(self, *, event_ids: set[int] | None = None) -> None:
    """Wait for all in-flight async futures to complete."""
    remaining: list[tuple[int, Future[None]]] = []
    for event_id, future in self._futures:
        if event_ids is not None and event_id not in event_ids:
            remaining.append((event_id, future))
            continue
        try:
            future.result(timeout=30)   # <-- hardcoded 30s, becomes self._per_future_timeout
        except Exception:
            pass  # Errors already handled in _execute_hook
    self._futures = remaining
```

### EventBus constructor — proposed signature

```python
# Proposed: src/ztlctl/plugins/event_bus.py
from ztlctl.config.models import EventBusConfig  # new import

def __init__(
    self,
    engine: Engine,
    plugin_manager: PluginManager,
    *,
    sync: bool = False,
    config: EventBusConfig | None = None,
) -> None:
    cfg = config or EventBusConfig()
    self._max_retries = cfg.max_retries
    self._per_future_timeout = cfg.per_future_timeout_seconds
    self._shutdown_timeout = cfg.shutdown_timeout_seconds
    self._dead_letter_retention_days = cfg.dead_letter_retention_days
    # Remove: max_retries and max_workers positional kwargs (breaking — keep with defaults for compat)
```

### Vault.init_event_bus startup drain placement

```python
# Source: src/ztlctl/infrastructure/vault.py init_event_bus() (proposed addition)
self._event_bus = EventBus(self._engine, pm, sync=sync, config=self._settings.eventbus)

# Startup recovery: drain pre-existing pending/failed WAL events
import structlog
_log = structlog.get_logger()
try:
    drained = self._event_bus.drain_startup()   # new method or parameterized drain()
    if drained:
        _log.debug("startup_drain", count=len(drained))
except Exception:
    _log.warning("startup_drain_failed", msg="continuing without startup drain")
```

### AppContext.close() proposed change

```python
# Source: src/ztlctl/commands/_context.py lines 107-111 (proposed)
def close(self) -> None:
    """Release held resources after command execution."""
    if self._vault is not None:
        timeout = self.settings.eventbus.shutdown_timeout_seconds
        self._vault.close(wait_for_events=True, timeout=timeout)
```

### Dead-letter purge query pattern

```python
# Source: pattern from existing WAL queries in event_bus.py
from datetime import datetime, timedelta
from sqlalchemy import delete

cutoff = (datetime.now() - timedelta(days=self._dead_letter_retention_days)).isoformat()
with self._engine.begin() as conn:
    result = conn.execute(
        delete(event_wal)
        .where(event_wal.c.status == "dead_letter")
        .where(event_wal.c.created < cutoff)
    )
    return result.rowcount
```

### ActionEvent model in contracts.py

```python
# Source: pattern from src/ztlctl/services/result.py + CONTEXT.md D-12/D-13/D-14
from pydantic import BaseModel

class ActionEvent(BaseModel):
    """Canonical post-commit write-side event payload."""

    model_config = {"frozen": True}

    action_name: str
    side_effect: Literal["write", "read"] = "write"
    payload: dict[str, Any]    # id, type, title, path, fields_changed, session_id
    warnings: list[str] = []
    result: Any = None          # ServiceResult — set by service after commit
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Direct `pm.hook.post_action()` in controllers | EventBus bridge fires `post_action` from legacy hooks | Phase 6 (pluggy migration) | Duplicate delivery: controllers AND bridge both fire `post_action` |
| `AppContext.close(wait_for_events=False)` | Proposed: bounded wait | Phase 15 | Hooks for slow plugins now complete reliably on one-shot CLI exit |
| Hardcoded `max_retries=3` in EventBus | Proposed: from `[eventbus]` config | Phase 15 | User-tunable; test-overridable |
| Bridge: legacy hook → post_action | Proposed: service emits ActionEvent → post_action, bridge removed | Phase 15 | Single producer, stable shape, no duplicate delivery |

**Deprecated/outdated after Phase 15:**
- `BaseController._dispatch_post_action()`: Removed entirely; no callers remain
- EventBus bridge (`_HOOK_TO_ACTION` + bridge logic in `_execute_hook()`): Removed in Phase 15 per D-11 (built-in plugins already guard for `result=None`)
- Hardcoded `timeout=30` in `EventBus._wait_futures()`: Replaced by `self._per_future_timeout`

---

## Open Questions

1. **Single WAL row vs. two WAL rows per write action**
   - What we know: Legacy hooks (e.g., `post_create`) are currently dispatched by services and written to the WAL. Services will now also need to emit `post_action`. If both go through `EventBus.dispatch()`, there are 2 WAL rows per write action.
   - What's unclear: D-15 says "EventBus WAL stores the serialized ActionEvent as the payload column value." This could mean the legacy hook WAL row carries an ActionEvent payload (fold them together) OR a new dedicated `post_action` WAL row exists alongside the legacy row.
   - Recommendation: **Fold together.** Rename `hook_name` to `action_name` in the WAL and write only the ActionEvent. This requires a schema migration (Alembic). Alternatively, keep the legacy WAL row as-is and emit `post_action` directly via `pm.hook.post_action()` without a WAL row (since the legacy row already provides durability). The planner should pick one and document it clearly.

2. **EventBus constructor backward compatibility**
   - What we know: `EventBus(engine, pm, sync=sync)` is called from `Vault.init_event_bus()`. Tests construct `EventBus(engine, pm, sync=True, max_retries=3)` directly.
   - What's unclear: Adding `config: EventBusConfig | None = None` while keeping `max_retries` and `max_workers` for backward compat creates an ambiguous dual interface.
   - Recommendation: Accept both. If `config` is provided, it wins. If only `max_retries` is passed, it overrides. Update all test fixtures to use `EventBusConfig` in Phase 15 tests.

3. **D-04: Read-only command identification**
   - What we know: The decision says "read-only commands skip drain." The simplest implementation is: drain is a no-op when `_futures` is empty (which it will be for read commands that produce no events).
   - What's unclear: Whether any read action should set a flag preventing drain — or whether "skip" simply means "drain takes < 1ms with no futures."
   - Recommendation: No explicit flag needed. Empty `_futures` makes drain a no-op. Document this as the intended behavior.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/plugins/test_event_bus.py tests/services/test_event_dispatch.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARCH-01 | Slow plugin leaves no `pending` WAL rows after CLI teardown with timeout | integration | `uv run pytest tests/plugins/test_event_bus.py::TestShutdownDrain -x` | ❌ Wave 0 |
| ARCH-01 | Shutdown timeout leaves WAL rows as `pending` (not cancelled) | unit | `uv run pytest tests/plugins/test_event_bus.py::TestShutdownTimeout -x` | ❌ Wave 0 |
| ARCH-02 | Startup drain recovers `pending` WAL events from prior run | integration | `uv run pytest tests/plugins/test_event_bus.py::TestStartupDrain -x` | ❌ Wave 0 |
| ARCH-02 | Startup drain timeout logs warning and continues | unit | `uv run pytest tests/plugins/test_event_bus.py::TestStartupDrainTimeout -x` | ❌ Wave 0 |
| ARCH-03 | ReweavePlugin receives exactly one `post_action` per `create_note` | integration | `uv run pytest tests/plugins/test_event_dispatch_canonical.py -x` | ❌ Wave 0 |
| ARCH-03 | GitPlugin receives exactly one `post_action` per write action | integration | `uv run pytest tests/plugins/test_event_dispatch_canonical.py -x` | ❌ Wave 0 |
| ARCH-04 | `ActionEvent` model validates required fields | unit | `uv run pytest tests/plugins/test_action_event.py -x` | ❌ Wave 0 |
| ARCH-04 | WAL payload deserializes to `ActionEvent` | unit | `uv run pytest tests/plugins/test_action_event.py -x` | ❌ Wave 0 |
| DEBT-02 | EventBus reads timeout from `EventBusConfig` | unit | `uv run pytest tests/plugins/test_event_bus.py::TestEventBusConfig -x` | ❌ Wave 0 |
| DEBT-03 | `ztlctl check` reports dead-letter count under `structural_validation` | unit | `uv run pytest tests/services/test_check_dead_letters.py -x` | ❌ Wave 0 |
| DEBT-03 | Startup drain auto-purges dead-letters older than retention period | unit | `uv run pytest tests/plugins/test_event_bus.py::TestDeadLetterPurge -x` | ❌ Wave 0 |
| DEBT-03 | `event_purge` action clears dead-letter WAL rows | integration | `uv run pytest tests/services/test_event_purge.py -x` | ❌ Wave 0 |

### Existing Test Coverage (do not break)
| File | What it covers | Risk |
|------|----------------|------|
| `tests/plugins/test_event_bus.py` | WAL persistence, failure handling, drain, async dispatch | HIGH — touched by all EventBus changes |
| `tests/plugins/test_event_bus_post_action_bridge.py` | Bridge fires `post_action` from legacy hooks | MEDIUM — bridge removed in Phase 15; these tests must be updated or replaced |
| `tests/services/test_event_dispatch.py` | Service → plugin dispatch integration | HIGH — affected by service-side emission change |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/plugins/ tests/services/test_event_dispatch.py tests/services/test_check.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/plugins/test_action_event.py` — covers ActionEvent model + WAL serialization
- [ ] `tests/plugins/test_event_bus_shutdown_drain.py` — covers ARCH-01 slow-plugin timeout scenarios
- [ ] `tests/plugins/test_event_bus_startup_drain.py` — covers ARCH-02 startup recovery
- [ ] `tests/plugins/test_event_dispatch_canonical.py` — covers ARCH-03 single-producer assertion
- [ ] `tests/plugins/test_event_bus_config.py` — covers DEBT-02 configurable timeout
- [ ] `tests/services/test_check_dead_letters.py` — covers DEBT-03 check reporting
- [ ] `tests/services/test_event_purge.py` — covers DEBT-03 event_purge action

---

## Sources

### Primary (HIGH confidence)
- `src/ztlctl/plugins/event_bus.py` — full EventBus implementation; hardcoded timeout at line 261; bridge at lines 208-221; `_wait_futures()` at lines 253-264
- `src/ztlctl/commands/_context.py` — `AppContext.close()` at lines 107-111; `wait_for_events=False` current behavior
- `src/ztlctl/infrastructure/vault.py` — `Vault.close()` at lines 341-359; `init_event_bus()` at lines 361-390
- `src/ztlctl/config/models.py` — all existing config section models; no `[eventbus]` section currently
- `src/ztlctl/config/settings.py` — `ZtlSettings` frozen model; TOML sources; how sections are composed
- `src/ztlctl/services/base.py` — `BaseService._dispatch_event()` signature and implementation
- `src/ztlctl/controllers/base.py` — `BaseController._dispatch_post_action()` at lines 84-102
- `src/ztlctl/plugins/hookspecs.py` — `post_action` hookspec signature (stable; must not change)
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — guards `result is None or not result.ok`; routing via `action_name`
- `src/ztlctl/plugins/builtins/git.py` — `post_action` hookimpl; routes by `action_name`
- `src/ztlctl/services/check.py` — `CAT_STRUCTURAL`, `_check_structural_validation()`, existing severity constants
- `src/ztlctl/infrastructure/database/schema.py` — `event_wal` table columns: `id`, `hook_name`, `payload`, `status`, `error`, `retries`, `session_id`, `created`, `completed`
- `.planning/phases/15-event-model-hardening/15-CONTEXT.md` — all 21 locked decisions
- `.planning/research/2026-03-21-architecture-remediation-design.md` — §1, §2, §3, §5 design rationale

### Secondary (MEDIUM confidence)
- Grep of 52 `_dispatch_post_action` call sites across 14 controllers — confirms scope of write-action removal
- `tests/plugins/test_event_bus.py` and `test_event_bus_post_action_bridge.py` — confirms test patterns for EventBus and bridge

### Tertiary (LOW confidence)
- None — all findings are from direct code inspection of the target codebase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in use; no new dependencies
- Architecture: HIGH — code patterns directly read from source; decisions are locked in CONTEXT.md
- Pitfalls: HIGH — derived from direct reading of existing code paths and known codebase conventions (MEMORY.md)

**Research date:** 2026-03-21
**Valid until:** 60 days — this is an internal refactor phase with no external library dependencies; changes will not be invalidated by upstream updates
