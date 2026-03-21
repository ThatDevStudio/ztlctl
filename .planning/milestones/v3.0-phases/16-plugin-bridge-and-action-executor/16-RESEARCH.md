# Phase 16: Plugin Bridge and Action Executor - Research

**Researched:** 2026-03-21
**Domain:** Plugin event bridge reversal, generic action executor, MCP graceful shutdown
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
None — all implementation choices are at Claude's discretion (pure infrastructure phase).

### Claude's Discretion
All implementation choices. Key constraints from architecture remediation design doc:
- Bridge reversal: stable action events → optional legacy hook adapters (not the reverse)
- Generic executor: reusable utility replacing repeated pre_action dispatch in controllers
- `garden seed` must exercise the same pre-action and post-commit machinery as other create flows
- MCP `ztlctl serve` must exit cleanly without dangling asyncio tasks when client disconnects

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ARCH-05 | Compatibility bridge reversed — stable action events adapt into legacy hook calls (not legacy → stable) | EventBus._execute_hook already has the two-path split; reversal inverts which path is canonical. The `_HOOK_TO_ACTION` map and its bridge code in the per-event path are the exact change targets. |
| ARCH-06 | Generic action executor replaces repeated pre/post hook boilerplate in controllers | BaseController._dispatch_pre_action + rejection-to-ServiceResult pattern is identical across all 13 controllers. An ActionExecutor utility can encapsulate the entire pre → invoke → return pipeline. |
| ARCH-09 | Command surface convergence — `garden seed` is a first-class action; hybrid patching reduced | `commands/__init__.py` line 73 explicitly comments "garden: not in ActionRegistry". Adding a `garden_seed` ActionDefinition to `_register_core.py` with `cli_group="garden"` and `cli_name="seed"` removes this hole. |
| DEBT-04 | MCP server graceful shutdown implemented | `mcp/server.py` creates a Vault but never calls vault.close(). FastMCP's `server.run()` is a blocking call; cleanup hook must run after it returns or on signal. |
</phase_requirements>

## Summary

Phase 16 targets four tightly related internal changes that collectively complete the "one canonical write path" model introduced in Phase 15. No user-facing command shapes change.

**ARCH-05 (bridge reversal):** Today `EventBus._execute_hook` dispatches the legacy per-event hook first, then fires a `post_action` bridge. This is backwards — new events should be canonical and legacy hooks should be adapters. The reversal means: for per-event hooks, first dispatch the stable `post_action` (with the correctly-shaped ActionEvent payload), then invoke the legacy hook adapter as a side effect for backward compatibility. Both built-in plugins (git, reweave) already implement `post_action` exclusively — they will be unaffected. Third-party plugins using deprecated hookspecs will continue to receive their call through the adapter path.

**ARCH-06 (generic executor):** Every controller method repeats the same four-step pattern: build kwargs dict, call `_dispatch_pre_action`, convert rejection to `ServiceResult`, call service. A standalone `ActionExecutor` utility collapses this into a single `executor.run(action_name, inputs, invoke=...)` call. Controllers become thinner; the rejection-mapping code lives once.

**ARCH-09 (garden seed as first-class action):** `garden seed` currently bypasses the ActionRegistry entirely — it calls `CreateService` directly without going through a controller or dispatcher. Adding a `garden_seed` ActionDefinition routes the command through `CreateController.create_note` with `maturity="seed"` baked in, making pre_action, post_action, and telemetry work identically to other create flows.

**DEBT-04 (MCP graceful shutdown):** `mcp/server.py` creates a Vault but never closes it. When `server.run()` returns (client disconnects), the EventBus ThreadPoolExecutor and the DB engine remain open. A finally block around `server.run()` calling `vault.close()` (with `wait_for_events=True`) is sufficient.

**Primary recommendation:** Implement in the order ARCH-05 → ARCH-06 → ARCH-09 → DEBT-04. The bridge reversal is the highest-correctness item; the executor and garden seed are mechanical; shutdown is self-contained.

---

## Standard Stack

### Core (all existing — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pluggy | >=1.3 (current) | Hook dispatch for pre_action / post_action / legacy hooks | Already the plugin backbone |
| pydantic | >=2 (current) | ActionEvent frozen model | Already domain model layer |
| asyncio (stdlib) | 3.13 | MCP server event loop; signal handling for clean shutdown | FastMCP runs on asyncio |
| FastMCP | current | MCP server framework; `server.run()` blocks until disconnect | Already the MCP transport layer |
| SQLAlchemy | >=2 (current) | EventBus WAL reads/writes | Already infrastructure layer |

No new dependencies. This is a pure refactor/wiring phase.

---

## Architecture Patterns

### Recommended Project Structure (no changes to top-level layout)

The only new file proposed by this phase:

```
src/ztlctl/
├── controllers/
│   ├── base.py          # BaseController — add ActionExecutor or import it
│   └── executor.py      # NEW: ActionExecutor utility (may live here or in actions/)
├── actions/
│   └── _register_core.py  # Add garden_seed ActionDefinition
├── plugins/
│   └── event_bus.py     # Reverse bridge in _execute_hook
├── mcp/
│   └── server.py        # Add vault.close() in finally block after server.run()
└── commands/
    └── __init__.py      # Remove manual garden.add_command; use generator
```

### Pattern 1: Bridge Reversal in EventBus._execute_hook

**What:** Change the legacy hook dispatch path so the canonical `post_action` fires first (from a proper ActionEvent payload), and the per-event legacy hook fires as an optional adapter.

**Current flow (legacy → stable):**
```
dispatch("post_create", raw_payload)
  → per-event hook fires with raw_payload
  → bridge fires post_action(action_name=..., kwargs=raw_payload, result=None)
```

**Reversed flow (stable → legacy adapter):**
```
dispatch("post_action", action_event_dict)   ← canonical path (services emit this)
  → post_action fires with ActionEvent fields (action_name, payload, result)

dispatch("post_create", raw_payload)         ← legacy path (only if per-event hook has impl)
  → legacy adapter fires post_create(**raw_payload)  [no change to per-event behavior]
  NOTE: legacy path no longer bridges to post_action. Services already emit post_action
        directly via _dispatch_post_action_event, so the bridge is dead code after Phase 15.
```

**Key insight from code audit:** After Phase 15, all write services call `_dispatch_post_action_event()` directly. The bridge in `_execute_hook` fires `post_action` *again* when a per-event hook runs. This produces duplicate delivery. The reversal means: the per-event dispatch path no longer calls `post_action`; it just calls the legacy hook. Since services already own `post_action` dispatch, no duplication occurs.

**What the reversal actually changes in `_execute_hook`:**
```python
# BEFORE (in the per-event branch):
hook_fn(**payload)         # call legacy hook
post_action_fn(...)        # bridge fires post_action (duplicate!)

# AFTER (in the per-event branch):
hook_fn(**payload)         # call legacy hook
# No bridge. post_action already fired by the service layer.
```

The `_HOOK_TO_ACTION` dict and the bridge block (lines 280-294 of event_bus.py) are removed entirely.

**Confidence:** HIGH — code read confirms the exact lines to change.

### Pattern 2: ActionExecutor Utility

**What:** A callable utility that encapsulates the pre_action → invoke → return pipeline.

**When to use:** Every controller method that follows the build-kwargs → pre_action → service call pattern.

**Design options:**

Option A — standalone class (`controllers/executor.py`):
```python
class ActionExecutor:
    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    def run(
        self,
        action_name: str,
        inputs: dict[str, Any],
        invoke: Callable[[dict[str, Any]], ServiceResult],
    ) -> ServiceResult:
        from ztlctl.services.result import ServiceError, ServiceResult
        kwargs, rejection = self._dispatch_pre_action(action_name, inputs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op=action_name,
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )
        return invoke(kwargs)
```

Option B — static method / module-level function that accepts vault+action+inputs+invoke. Slightly simpler, avoids another class.

Option C — fold into `BaseController` as `_run_action(name, inputs, invoke)`. Keeps the controller hierarchy intact without a new file.

**Recommendation:** Option C (fold into BaseController). It keeps the change localized to one file, avoids adding a class to the public API surface, and matches the existing `_dispatch_pre_action` pattern.

**Controller migration approach:** Each controller method currently has 15-25 lines of boilerplate. After migration:
```python
def create_note(self, title: str, ...) -> ServiceResult:
    from ztlctl.services.create import CreateService
    return self._run_action(
        "create_note",
        {"title": title, "subtype": subtype, ...},
        lambda kw: CreateService(self._vault).create_note(kw["title"], subtype=kw["subtype"], ...),
    )
```

**Anti-pattern to avoid:** Do not put `_run_action` in a separate module that requires importing `BaseController`. Import cycles are a real risk in this codebase (lazy imports are the established pattern for cross-layer references).

### Pattern 3: garden_seed as First-Class Action

**What:** Add a `garden_seed` ActionDefinition in `_register_core.py` that routes through `CreateController.create_note` with `maturity="seed"` baked in.

**Key design point:** The ActionDefinition `handler` is `lambda vault: CreateController(vault).create_note_seed` where `create_note_seed` is a thin wrapper or the `ActionDefinition` uses a partial/lambda that injects `maturity="seed"`. The cleanest approach:

```python
# In _register_core.py:
registry.register(
    ActionDefinition(
        name="garden_seed",
        description="Plant a seed note — quick capture with minimal metadata.",
        category="creation",
        params=(
            ActionParam("title", str, required=True, cli_is_argument=True, ...),
            ActionParam("tags", list, required=False, ...),
            ActionParam("topic", str, required=False, ...),
        ),
        handler=lambda vault: (
            lambda title, tags=None, topic=None:
                CreateController(vault).create_note(title, tags=tags, topic=topic, maturity="seed")
        ),
        side_effect="write",
        cli_group="garden",
        cli_name="seed",
        ...
    )
)
```

Then `commands/__init__.py` removes the manual `cli.add_command(garden)` and the generated `garden` group carries only the `seed` subcommand (from the ActionDefinition). The `commands/garden.py` file becomes dead code and can be deleted.

**What changes in `commands/__init__.py`:** The comment "garden: not in ActionRegistry" becomes obsolete and the manual `cli.add_command(garden)` block is removed.

**What the generator must support:** The generator must handle `cli_group="garden"` creating a `garden` group and `cli_name="seed"` as the subcommand. Check whether the existing generator already supports multi-word group names or requires the group to be pre-existing.

**Confidence:** HIGH — the ActionDefinition model has `cli_group` and `cli_name` fields explicitly designed for this.

### Pattern 4: MCP Graceful Shutdown (DEBT-04)

**What:** Ensure `vault.close(wait_for_events=True)` runs when `ztlctl serve` exits.

**Current state in `mcp/server.py`:** `create_server()` creates a `Vault` and calls `vault.init_event_bus()`. The returned server object is run via `server.run(transport=transport)` in `commands/serve.py`. When the MCP client disconnects, `server.run()` returns normally, but nothing closes the vault.

**The fix:** `commands/serve.py` wraps `server.run()`:
```python
server = create_server(vault_root=app.settings.vault_root, host=host, port=port)
try:
    server.run(transport=transport)
finally:
    # Drain and close the vault's event bus
    if hasattr(server, "_vault"):
        server._vault.close(wait_for_events=True)
```

However, `create_server()` does not currently expose the vault it creates. Two approaches:
1. Return `(server, vault)` from `create_server()` — breaking change to the public API.
2. Store `vault` on the server object: `server._vault = vault` — relies on FastMCP instance being mutable.
3. Move vault lifecycle into `serve.py` directly instead of inside `create_server()`.
4. Add a `close_server(server)` function to `mcp/server.py` that the serve command calls.

**Recommendation:** Add a module-level `_vault: Vault | None = None` in `mcp/server.py` and a `close_server()` function, OR return vault alongside server. The cleanest is a `ServerContext` namedtuple/dataclass:
```python
@dataclass
class ServerContext:
    server: Any      # FastMCP instance
    vault: Vault

def create_server(...) -> ServerContext: ...
```

Then `commands/serve.py`:
```python
ctx = create_server(...)
try:
    ctx.server.run(transport=transport)
finally:
    ctx.vault.close(wait_for_events=True)
```

**Signal handling note:** FastMCP's stdio transport handles SIGTERM/SIGINT internally before returning from `run()`. The `finally` block runs after `run()` returns regardless of cause (normal exit or signal). No additional signal handler registration is needed.

**Asyncio note:** FastMCP's `run()` creates and tears down its own asyncio event loop. After `run()` returns, the loop is gone. `vault.close()` is synchronous, so no asyncio concerns in the teardown path.

### Anti-Patterns to Avoid

- **Do not add a new `post_action` bridge in the per-event path.** After ARCH-05, services own all `post_action` dispatch. Any bridge re-introduction creates the duplicate delivery problem again.
- **Do not call `vault.close()` inside FastMCP lifecycle callbacks.** These run inside the asyncio event loop; synchronous SQLAlchemy calls in that context can deadlock.
- **Do not make `ActionExecutor` a public module-level class** if it is only used by `BaseController`. Unnecessary surface area.
- **Do not remove the `_HOOK_TO_ACTION` map** entirely if it is tested directly. Check test coverage first; tests may need updating alongside the removal.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pre-action hook dispatch | Custom hook caller | `pm.hook.pre_action(action_name=..., kwargs=...)` (existing) | pluggy firstresult semantics are already correct |
| ActionRejection → ServiceResult conversion | Custom error factory | Existing pattern in CreateController (lines 49-59) — extract it, don't re-invent | Consistent error codes and recovery messages |
| MCP server signal handling | Custom SIGTERM handler | FastMCP handles signals internally before returning from `run()` | Re-registering handlers can interfere with FastMCP's own teardown |
| Event bus thread teardown | Custom ThreadPoolExecutor shutdown | `vault.close(wait_for_events=True)` → `EventBus.shutdown(wait=True)` | Already implemented and tested in Phase 15 |

---

## Common Pitfalls

### Pitfall 1: Duplicate post_action delivery survives bridge reversal

**What goes wrong:** After reversal, some code path still calls `post_action` twice for the same action — once from the service, once residually from a legacy per-event path.

**Why it happens:** The test file `test_event_bus_post_action_bridge.py` tests the bridge by dispatching per-event hooks and asserting that `post_action` fires. If those tests are not updated, they will fail, but if they are simply deleted without replacement, the regression is invisible.

**How to avoid:** Update bridge tests to assert the opposite — per-event dispatch does NOT trigger a second `post_action`. Add an integration test that creates a note and asserts the reweave plugin fires exactly once.

**Warning signs:** Any test asserting `len(plugin.post_action_calls) == 1` after a per-event dispatch. After the reversal, `post_action_calls` will be 0 for per-event dispatches (post_action only fires when the service directly emits it).

### Pitfall 2: garden seed bypasses ActionExecutor after migration

**What goes wrong:** The `garden_seed` ActionDefinition is added but the handler calls `CreateService` directly rather than going through `CreateController` (which uses the executor). Pre-action hooks are then silently skipped.

**Why it happens:** It's tempting to write the handler as `lambda vault: CreateService(vault).create_note(...)` (shorter). But the executor/controller layer is where `pre_action` runs.

**How to avoid:** All `garden_seed` handlers must call `CreateController(vault).create_note(...)`.

### Pitfall 3: MCP vault not closed on SIGTERM in stdio mode

**What goes wrong:** When the MCP client (e.g. Claude Desktop) terminates abruptly, SIGTERM is sent to the `ztlctl serve` process. FastMCP may raise `SystemExit` in `run()`, bypassing the `finally` block in some Python configurations.

**Why it happens:** `SystemExit` propagates through `try/finally` in Python — the `finally` block does run. But if FastMCP uses `os._exit()` instead of `sys.exit()`, `finally` blocks are skipped.

**How to avoid:** Verify FastMCP's shutdown path does not use `os._exit()`. A regression test can mock `server.run()` to raise `SystemExit(0)` and assert that vault.close() is still called.

**Warning signs:** If WAL rows remain `pending` after a forced disconnect test.

### Pitfall 4: ActionExecutor lambda captures mutable loop variable

**What goes wrong:** If the executor migration uses a loop to register actions or a closure that captures a loop variable, all actions end up calling the last service method.

**Why it happens:** Python's late-binding closure semantics. Not a risk if lambdas are written inline per-action (the established pattern in `_register_core.py`).

**How to avoid:** Write each controller method's lambda explicitly (as in the existing `_register_core.py` pattern), not in a loop.

### Pitfall 5: Breaking the generator for garden group

**What goes wrong:** Adding `cli_group="garden"` to `garden_seed` ActionDefinition, but the CLI generator does not create the `garden` group object before adding the `seed` subcommand.

**Why it happens:** The generator iterates ActionDefinitions and creates groups lazily. If no other action uses `cli_group="garden"`, the group may not exist when `seed` tries to attach.

**How to avoid:** The generator already handles this pattern (every existing `cli_group` value creates groups lazily). Verify by checking the generator's group-creation logic before assuming it works.

---

## Code Examples

Verified patterns from codebase reading:

### Current bridge (lines to remove in event_bus.py)
```python
# Source: src/ztlctl/plugins/event_bus.py lines 280-294
# This block fires post_action for legacy hooks. REMOVE after ARCH-05.
action_name = _HOOK_TO_ACTION.get(hook_name)
if action_name is not None:
    if hook_name == "post_create":
        content_type = payload.get("content_type", "note")
        action_name = f"create_{content_type}"
    try:
        post_action_fn = getattr(self._pm.hook, "post_action", None)
        if post_action_fn is not None:
            post_action_fn(action_name=action_name, kwargs=payload, result=None)
    except Exception:
        logger.debug("post_action bridge failed for %s", hook_name, exc_info=True)
```

### Existing pre_action rejection pattern (extract into _run_action)
```python
# Source: src/ztlctl/controllers/create.py lines 48-59
# This identical pattern repeats across all 13 controllers.
kwargs, rejection = self._dispatch_pre_action("create_note", kwargs)
if rejection is not None:
    return ServiceResult(
        ok=False,
        op="create_note",
        error=ServiceError(
            code="ACTION_REJECTED",
            message=rejection.reason,
            detail=rejection.detail,
            recovery=f"Action rejected by plugin: {rejection.reason}",
        ),
    )
```

### Canonical post_action dispatch (already implemented in services, for reference)
```python
# Source: src/ztlctl/services/base.py lines 58-96
# Services emit ActionEvent via this method. Bridge must not duplicate this.
def _dispatch_post_action_event(self, action_name, payload, warnings, result=None, ...):
    event = ActionEvent(
        action_name=action_name,
        side_effect="write",
        payload=payload,
        warnings=warnings,
        result=result,
    )
    return bus.dispatch("post_action", event.model_dump(), ...)
```

### garden seed current implementation (to replace)
```python
# Source: src/ztlctl/commands/garden.py lines 36-48
# Currently calls CreateService directly — no pre_action, no executor.
def seed(app: AppContext, title: str, tags: str | None, topic: str | None) -> None:
    tag_list = [t.strip() for t in tags.split(",")] if tags else None
    app.emit(
        CreateService(app.vault).create_note(title, tags=tag_list, topic=topic, maturity="seed")
    )
```

### MCP serve teardown (target pattern)
```python
# Source: src/ztlctl/commands/serve.py lines 49-50 (current — no vault teardown)
server = create_server(vault_root=app.settings.vault_root, host=host, port=port)
server.run(transport=transport)  # vault never closed

# Target pattern:
ctx = create_server(vault_root=app.settings.vault_root, host=host, port=port)
try:
    ctx.server.run(transport=transport)
finally:
    ctx.vault.close(wait_for_events=True)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Legacy hooks → post_action bridge | Services emit post_action directly | Phase 15 | Bridge is now redundant; creates duplicate delivery |
| Controllers dispatch post_action | Services dispatch post_action | Phase 15 | ARCH-03 complete; controllers only do pre_action |
| garden seed calls CreateService directly | After Phase 16: goes through ActionRegistry → Controller | Phase 16 | pre_action hooks and post_action events work for garden seed |
| MCP vault leaks on disconnect | vault.close() in finally block | Phase 16 | WAL drain happens reliably on serve exit |

**Bridge is dead code after Phase 15:** Every write operation in the codebase now calls `_dispatch_post_action_event()` directly from the service layer. The bridge in `_execute_hook` for per-event hooks fires `post_action` again — this is pure duplicate delivery. ARCH-05 is removing a now-defunct code path, not implementing new logic.

---

## Open Questions

1. **Does the CLI generator already support `cli_group="garden"` creating a new top-level group?**
   - What we know: The generator creates groups lazily from `cli_group` values. Existing groups (`create`, `graph`, `session`, etc.) all work. `garden` is a new group name with a single member.
   - What's unclear: Whether the generator adds a description/help text to auto-created groups or leaves them blank.
   - Recommendation: Read `commands/generator.py` briefly before planning the garden task. The group creation logic will confirm whether a group-level `ActionDefinition` or a simple `cli_group` reference is needed.

2. **Should `commands/garden.py` be deleted or kept as a dead file?**
   - What we know: After ARCH-09, the `garden` group and `seed` subcommand will be generated. The old hand-written file becomes dead code.
   - What's unclear: Whether any test directly imports from `commands/garden.py`.
   - Recommendation: Grep for imports of `commands.garden` in tests before planning deletion. If tests exist, update them; if not, delete the file.

3. **Does FastMCP expose the vault or server context for teardown?**
   - What we know: `create_server()` creates a local `vault` variable that is not returned. FastMCP instances are mutable Python objects.
   - What's unclear: Whether storing `server._vault = vault` is idiomatic or if FastMCP has a lifecycle callback API.
   - Recommendation: Accept the `ServerContext` dataclass pattern as the clean approach — return both server and vault from `create_server()`. This is the minimal invasive change and does not depend on FastMCP internals.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (current) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/plugins/test_event_bus.py tests/controllers/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ARCH-05 | Per-event dispatch does NOT fire a second post_action | unit | `uv run pytest tests/plugins/test_event_bus_post_action_bridge.py -x` | ✅ (update existing) |
| ARCH-05 | Legacy per-event hooks still receive their call via adapter | unit | `uv run pytest tests/plugins/test_event_bus_post_action_bridge.py -x` | ✅ (update/add assertion) |
| ARCH-05 | Built-in reweave plugin fires exactly once per create action | integration | `uv run pytest tests/plugins/test_reweave_plugin.py -x` | ✅ (add once-only assertion) |
| ARCH-06 | Pre_action rejection handled identically across all controllers | unit | `uv run pytest tests/controllers/test_hook_wiring.py tests/controllers/test_create.py -x` | ✅ (update for executor) |
| ARCH-06 | _run_action propagates rejection with correct ServiceError shape | unit | `uv run pytest tests/controllers/test_base.py -x` | ✅ (add executor test) |
| ARCH-09 | `ztlctl garden seed` exercises pre_action hook | unit | `uv run pytest tests/controllers/test_create.py -x` | ✅ (add garden_seed test) |
| ARCH-09 | garden_seed ActionDefinition registered in ActionRegistry | unit | `uv run pytest tests/actions/ -x` | ✅ (add registration test) |
| DEBT-04 | vault.close() called after server.run() returns | unit | `uv run pytest tests/mcp/ -x` | ✅ (add shutdown test) |
| DEBT-04 | vault.close() called even when server.run() raises SystemExit | unit | `uv run pytest tests/mcp/ -x` | ✅ Wave 0 gap |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/plugins/ tests/controllers/ tests/actions/ tests/mcp/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/mcp/test_serve_shutdown.py` — covers DEBT-04 (vault close on normal exit and SystemExit)
- [ ] Test asserting reweave plugin fires exactly once after create (in `test_reweave_plugin.py` or integration)

*(All other required tests are modifications of existing files, not new files)*

---

## Sources

### Primary (HIGH confidence)
- `src/ztlctl/plugins/event_bus.py` — full read; bridge logic confirmed at lines 280-294
- `src/ztlctl/controllers/base.py` — full read; `_dispatch_pre_action` confirmed as extraction candidate
- `src/ztlctl/controllers/create.py` — full read; boilerplate pattern confirmed across all 4 methods
- `src/ztlctl/services/base.py` — full read; `_dispatch_post_action_event` placement confirmed
- `src/ztlctl/commands/garden.py` — full read; confirmed bypasses ActionRegistry
- `src/ztlctl/commands/__init__.py` — full read; line 73 confirms gap documented in comments
- `src/ztlctl/mcp/server.py` — full read; vault not returned/closed confirmed
- `src/ztlctl/commands/serve.py` — full read; no finally block confirmed
- `src/ztlctl/actions/definitions.py` — full read; `cli_group`, `cli_name` fields confirmed
- `.planning/research/2026-03-21-architecture-remediation-design.md` — §4, §6, §8 read in full
- `tests/plugins/test_event_bus_post_action_bridge.py` — full read; existing tests map to ARCH-05 changes

### Secondary (MEDIUM confidence)
- `src/ztlctl/domain/events.py` — ActionEvent model confirmed as already-correct Phase 15 output
- `src/ztlctl/plugins/hookspecs.py` — deprecated hookspec `warn_on_impl` confirmed on all per-event hooks

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all libraries already in use
- Architecture: HIGH — all patterns derived from direct code reading, not assumptions
- Pitfalls: HIGH — duplicate delivery and missing vault teardown are concrete bugs confirmed by reading the code; not speculative
- MCP shutdown: MEDIUM — FastMCP's `run()` internal signal handling assumed to not use `os._exit()`; warrants a quick verification in the FastMCP source before implementation

**Research date:** 2026-03-21
**Valid until:** Stable (no external dependencies); valid until the affected files change
