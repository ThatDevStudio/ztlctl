# Phase 07: Plugin & Agentic Wiring Fixes - Research

**Researched:** 2026-03-20
**Domain:** pluggy hook dispatch, controller wiring, MCP error propagation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Pre/post-action hook wiring (PLUG-02)**
- Wire `_dispatch_pre_action()` and `_dispatch_post_action()` into ALL controller methods (both read and write)
- Read-side hooks enable plugins to observe queries (audit logging, metrics) — not just mutations
- Pattern: call `_dispatch_pre_action(action_name, kwargs)` before service delegation; if rejection returned, convert to `ServiceResult` error with rejection reason and return early
- Pattern: call `_dispatch_post_action(action_name, kwargs, result)` after service returns, regardless of result.ok
- `create_batch` (custom_presentation, called directly from CLI) also needs hooks
- 14 concrete controllers × ~59 methods total need wiring — systematic, not selective

**Plugin config injection (PLUG-03)**
- Add `pm.inject_configs(self._settings)` call in `vault.init_event_bus()` after `pm.discover_and_load()` and before built-in plugin registration
- Single initialization path — no secondary injection site needed
- Built-in plugins (GitPlugin, ReweavePlugin) don't use TOML config (they receive config via constructor), so ordering is safe

**Category activation semantics (AGNT-04)**
- Category activation is **advisory metadata** — document this explicitly, do not implement tool gating
- Rationale: FastMCP does not support dynamic tool deregistration; gating would require server restart
- `discover_categories` returns active/inactive status; agents use this for tool selection heuristics
- Update REQUIREMENTS.md AGNT-04 description to clarify "activation" means "discovery metadata for agent tool selection" not "dynamic tool surface reduction"
- Add docstring/comment in generator.py explaining the advisory-only design decision

**Error detail forwarding (AGNT-01)**
- Forward `result.error.detail` to `McpError.detail` in `McpResponse.from_result()` — one-line fix
- Forward all fields — no selective filtering (agents parse what they need)

### Claude's Discretion
- Exact ServiceResult error code for ActionRejection (suggest "ACTION_REJECTED" or similar)
- Whether to add a COMMON_ERROR_RECOVERY entry for the rejection error code
- Test organization (new test files vs extending existing)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLUG-02 | Pre-action hooks with modification and cancellation — synchronous dispatch via pluggy firstresult pattern; plugins can modify action inputs or return a rejection to abort the action before execution | BaseController._dispatch_pre_action/_dispatch_post_action are fully implemented and ready to call; 14 controller files × 59 methods identified |
| PLUG-03 | Plugin configuration via `[plugins.<name>]` sections in ztlctl.toml — passed to plugins during initialization; validated against plugin-declared config schema | inject_configs() is fully implemented in PluginManager; single insertion point in vault.init_event_bus() identified (line 376) |
| AGNT-01 | Structured error responses with machine-readable recovery guidance — every ServiceResult error includes actionable "what to do next" for agents | McpError.detail field already exists; from_result() drop is a one-line fix; McpError model confirmed |
| AGNT-04 | Progressive tool disclosure — category-based tool activation so plugins don't overwhelm the MCP tool surface; agents can discover and activate tool categories on demand | Decision resolved as advisory metadata; generator.py docstring update needed; no generate_tools() changes |
</phase_requirements>

---

## Summary

This is a wiring-only phase that closes four integration gaps identified in the v2.0 milestone audit. All underlying machinery (BaseController hook dispatch, PluginManager.inject_configs, McpError.detail field) is fully implemented and tested in isolation — it was simply never wired into the production execution path.

The highest-effort item is PLUG-02: systematically adding `_dispatch_pre_action` / `_dispatch_post_action` calls to all 59 public methods across 14 controller files. The pattern is identical in each case and the action names map directly to the ActionDefinition names in `_register_core.py`. The remaining three items (PLUG-03, AGNT-01, AGNT-04) are micro-fixes: one line in `vault.init_event_bus()`, one line in `McpResponse.from_result()`, and a docstring update plus REQUIREMENTS.md clarification.

AGNT-04 does not require any code change to `generate_tools()`. The design decision is settled: category activation is advisory metadata exposed to agents via `discover_categories` — FastMCP does not support dynamic tool deregistration, so no implementation-level gating is possible or desired.

**Primary recommendation:** Organize the work into three plans: (1) PLUG-02 controller wiring across all 14 files, (2) PLUG-03 vault init + AGNT-01 MCP detail + AGNT-04 docs in a single micro-fixes plan, (3) regression tests confirming all four requirements are now satisfied end-to-end.

---

## Standard Stack

### Core (already in project — no new dependencies)

| Component | Location | Purpose |
|-----------|----------|---------|
| `BaseController._dispatch_pre_action` | `src/ztlctl/controllers/base.py:49` | Returns `(kwargs, ActionRejection | None)` — fully implemented |
| `BaseController._dispatch_post_action` | `src/ztlctl/controllers/base.py:84` | Fires all post_action hooks — fully implemented |
| `PluginManager.inject_configs` | `src/ztlctl/plugins/manager.py:233` | Validates TOML config sections and calls plugin `initialize()` — fully implemented |
| `McpError.detail` | `src/ztlctl/mcp/response.py` | `dict[str, Any]` with `default_factory=dict` — field already exists |
| `ServiceError.detail` | `src/ztlctl/services/result.py:22` | Source of structured error context — already populated by services |

No new packages required. This phase is pure wiring of existing components.

---

## Architecture Patterns

### Pattern 1: Controller Method Hook Wiring (PLUG-02)

The pattern for each controller method is a four-step wrapper around the existing service call:

```python
def some_method(self, param: str, *, kwarg: int = 0) -> ServiceResult:
    """Existing docstring."""
    from ztlctl.services.some import SomeService
    from ztlctl.services.result import ServiceError, ServiceResult

    # 1. Build kwargs dict matching the action's ActionDefinition params
    kwargs: dict[str, Any] = {"param": param, "kwarg": kwarg}

    # 2. Pre-action dispatch — may return modified kwargs or rejection
    kwargs, rejection = self._dispatch_pre_action("some_action_name", kwargs)
    if rejection is not None:
        return ServiceResult(
            ok=False,
            op="some_action_name",
            error=ServiceError(
                code="ACTION_REJECTED",
                message=rejection.reason,
                detail=rejection.detail,
                recovery=f"Plugin '{rejection.code}' rejected this action: {rejection.reason}",
            ),
        )

    # 3. Service call using (possibly modified) kwargs
    result = SomeService(self._vault).some_method(**kwargs)

    # 4. Post-action dispatch — fires regardless of result.ok
    self._dispatch_post_action("some_action_name", kwargs, result)
    return result
```

**Key constraint:** The action name string passed to `_dispatch_pre_action` MUST match the `name` field of the corresponding `ActionDefinition` in `_register_core.py`. These are the authoritative names.

**Signature-based constraint:** Methods with positional parameters (e.g., `create_note(title, *, ...)`) must unpack positional args into the kwargs dict explicitly. All keyword-only params are included as-is.

**Return type constraint:** `ServiceResult` is frozen (Pydantic model). The rejection ServiceResult is constructed inline — do not mutate existing results.

**Existing `dispatch_post_create` parameter:** Several `CreateController` methods accept `dispatch_post_create: bool = True` which controls the EventBus bridge for the deprecated `post_create` hookspec. This parameter is NOT part of the ActionDefinition kwargs and should NOT be included in the pre/post-action kwargs dict passed to plugins.

### Pattern 2: Methods Requiring Special Handling

Some controller methods are not backed by ActionDefinitions or have non-standard return types:

| Method | Controller | Action Name | Note |
|--------|-----------|-------------|------|
| `create_note` | CreateController | `create_note` | Exclude `dispatch_post_create` from kwargs |
| `create_reference` | CreateController | `create_reference` | Exclude `dispatch_post_create` from kwargs |
| `create_task` | CreateController | `create_task` | Standard |
| `create_batch` | CreateController | `create_batch` | CONTEXT.md says wire it — use `"create_batch"` |
| `discover_categories` | DiscoveryController | `discover_categories` | Does not delegate to service; constructs ServiceResult directly — still wrap with hooks |
| `activate_category` | DiscoveryController | `activate_category` | Same — inline ServiceResult construction |
| `deactivate_category` | DiscoveryController | `deactivate_category` | Same |
| `read_answers` | WorkflowController | — | Returns `WorkflowChoices | None`, not ServiceResult — **skip hooks** |
| `profile_choices` | WorkflowController | — | Returns `list[str]`, not ServiceResult — **skip hooks** |
| `default_choices` | WorkflowController | — | Returns `Any`, not ServiceResult — **skip hooks** |

**Rule:** Only wire hooks on methods that return `ServiceResult`. Methods returning other types (WorkflowController helpers, non-ServiceResult methods) are skipped.

### Pattern 3: PLUG-03 Insertion in vault.init_event_bus()

The current `init_event_bus()` body (lines 374-388 of `infrastructure/vault.py`):

```python
pm = PluginManager()
local_plugins = self.root / ".ztlctl" / "plugins"
pm.discover_and_load(local_dir=local_plugins)           # line 376

# INSERT HERE: pm.inject_configs(self._settings)

# Register built-in git plugin with vault context
git_config = self._settings.git
git_plugin = GitPlugin(config=git_config, vault_root=self.root)
pm.register_plugin(git_plugin, name="git-builtin")

reweave_plugin = ReweavePlugin(vault=self)
pm.register_plugin(reweave_plugin, name="reweave-builtin")

self._plugin_manager = pm
self._event_bus = EventBus(self._engine, pm, sync=sync)
```

The insertion goes after `pm.discover_and_load()` and before the built-in plugin registrations. Order matters: `inject_configs()` must see only the third-party plugins loaded from entry points/local dir, not the built-ins (which use constructor-based config, not TOML config).

### Pattern 4: AGNT-01 One-Line Fix in McpResponse.from_result()

Current code (response.py lines 151-157):
```python
error = McpError(
    code=result.error.code,
    message=result.error.message,
    recovery=recovery,
    # MISSING: detail=result.error.detail
)
```

Fix:
```python
error = McpError(
    code=result.error.code,
    message=result.error.message,
    recovery=recovery,
    detail=result.error.detail,
)
```

`McpError.detail` already has `default_factory=dict` — when `ServiceError.detail` is empty (most existing errors), this forwards `{}`, which is harmless.

### Pattern 5: AGNT-04 Documentation Update

Two documentation changes required, zero code changes to `generate_tools()`:

1. **generator.py** — add a module-level or function-level comment near `_active_categories` explaining the advisory-only design:

```python
# NOTE: Category activation state is advisory metadata for agent tool selection.
# FastMCP does not support dynamic tool deregistration without a server restart,
# so generate_tools() registers all ActionDefinitions unconditionally regardless
# of _active_categories. Agents use discover_categories to understand tool groupings
# and make informed tool selection decisions — not to actually reduce the tool surface.
```

2. **REQUIREMENTS.md** — update AGNT-04 description to replace "dynamic tool surface reduction" framing with "discovery metadata" framing.

### Recommended Project Structure (no new files needed)

All changes are in existing files:
```
src/ztlctl/
├── controllers/
│   ├── check.py          # 4 methods — wire hooks
│   ├── create.py         # 4 methods — wire hooks (exclude dispatch_post_create)
│   ├── discovery.py      # 3 methods — wire hooks (inline ServiceResult pattern)
│   ├── export.py         # 4 methods — wire hooks
│   ├── graph.py          # 8 methods — wire hooks
│   ├── ingest.py         # 4 methods — wire hooks
│   ├── init_ctrl.py      # 3 methods — wire hooks
│   ├── query.py          # 9 methods — wire hooks
│   ├── reweave.py        # 3 methods — wire hooks
│   ├── session.py        # 9 methods — wire hooks
│   ├── update.py         # 3 methods — wire hooks
│   ├── upgrade.py        # 3 methods — wire hooks
│   ├── vector.py         # 2 methods — wire hooks
│   └── workflow.py       # 4 ServiceResult methods — wire hooks; skip 3 non-SR methods
├── infrastructure/
│   └── vault.py          # init_event_bus(): add inject_configs() call
└── mcp/
    ├── response.py       # from_result(): add detail= kwarg
    └── generator.py      # advisory-only comment
```

### Anti-Patterns to Avoid

- **Including internal flags in kwargs dict:** `dispatch_post_create`, `partial`, and other flags that are not ActionDefinition params must NOT be in the kwargs dict passed to plugins. Plugins see only the semantic action parameters.
- **Silently skipping rejection on error:** If `_dispatch_pre_action` returns a rejection, the method MUST return a ServiceResult error immediately. Never fall through to service delegation.
- **Calling post_action before checking rejection:** Always check rejection first; if rejected, skip service call AND post_action call.
- **Mutating the result after post_action:** ServiceResult is frozen. Don't try to update it after dispatch.
- **Wiring non-ServiceResult methods:** WorkflowController.read_answers, profile_choices, default_choices return non-ServiceResult types — do not wire them.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pre-action hook dispatch | Custom hook loop | `BaseController._dispatch_pre_action()` | Already handles ActionRejection/dict/None returns, exception isolation |
| Post-action hook dispatch | Custom hook loop | `BaseController._dispatch_post_action()` | Already handles exceptions, fires all plugins |
| Plugin config validation | Custom TOML parsing | `PluginManager.inject_configs()` | Already handles schema discovery, Pydantic validation, error logging |
| ActionRejection → ServiceResult | Custom error model | `ServiceError(code="ACTION_REJECTED", ...)` | Plugs into existing error propagation path |

---

## Common Pitfalls

### Pitfall 1: kwargs dict construction mismatch

**What goes wrong:** The kwargs dict passed to `_dispatch_pre_action` includes flags that aren't part of the ActionDefinition (e.g., `dispatch_post_create`, `partial`), or omits required params.

**Why it happens:** Controller methods often have extra internal params that the ActionDefinition doesn't expose. Plugins receive kwargs and may act on unexpected keys.

**How to avoid:** Build kwargs dict from only the params listed in the corresponding ActionDefinition in `_register_core.py`. Internal flags stay out of the dict.

**Warning signs:** Tests pass but a plugin that modifies kwargs gets keys it doesn't recognize.

### Pitfall 2: Action name string typo

**What goes wrong:** `_dispatch_pre_action("create_notes", kwargs)` instead of `"create_note"` — plugin never fires because the action name doesn't match what the plugin registers for.

**Why it happens:** Action names are stringly typed. There's no compile-time validation.

**How to avoid:** The source of truth is `_register_core.py` ActionDefinition `name` fields. Use those verbatim. The planner should enumerate all 59 action names from that file.

**Warning signs:** Integration test where a plugin filters by action_name doesn't fire.

### Pitfall 3: inject_configs ordering relative to built-in plugin registration

**What goes wrong:** `inject_configs()` is called after built-in plugins are registered. Built-in plugins (GitPlugin, ReweavePlugin) don't use TOML config — they use constructor params — so they'd get `initialize(config=None)` if they implement `initialize`. This is harmless for current built-ins but could cause confusion.

**How to avoid:** Insert `inject_configs()` before the built-in plugin registrations, as specified in CONTEXT.md.

**Warning signs:** A future built-in plugin that uses `initialize()` gets called twice.

### Pitfall 4: Detail forwarding breaks exclude_none serialization

**What goes wrong:** `detail=result.error.detail` always populates the field, even when the dict is empty `{}`. A client using `model_dump(exclude_none=True)` would still see `"detail": {}` in the output.

**Why it happens:** `McpError.detail` has `default_factory=dict`, not `default=None`. Empty dict is not None so it won't be excluded.

**How to avoid:** This is acceptable behavior — empty dict is benign. Agents can check `if error.get("detail")`. Do not make detail Optional just to suppress the empty key. Confirmed by CONTEXT.md: "Forward all fields — no selective filtering."

### Pitfall 5: WorkflowController non-ServiceResult methods

**What goes wrong:** Wiring `read_answers`, `profile_choices`, or `default_choices` with hooks. These return `WorkflowChoices | None`, `list[str]`, and `Any` respectively — not ServiceResult. Trying to return a rejection ServiceResult from them breaks the return type contract.

**How to avoid:** Only wire methods that return `ServiceResult`. Check the method signature.

---

## Code Examples

### Complete controller method (create_note, PLUG-02)

```python
# Source: controllers/create.py — PLUG-02 wiring pattern
def create_note(
    self,
    title: str,
    *,
    subtype: str | None = None,
    tags: list[str] | None = None,
    topic: str | None = None,
    session: str | None = None,
    maturity: str | None = None,
    body: str | None = None,
    key_points: list[str] | None = None,
    links: dict[str, list[str]] | None = None,
    aliases: list[str] | None = None,
    dispatch_post_create: bool = True,
) -> ServiceResult:
    """Create a new note."""
    from ztlctl.services.create import CreateService
    from ztlctl.services.result import ServiceError, ServiceResult

    # Only include ActionDefinition params — exclude dispatch_post_create
    kwargs: dict[str, Any] = {
        "title": title,
        "subtype": subtype,
        "tags": tags,
        "topic": topic,
        "session": session,
        "maturity": maturity,
        "body": body,
        "key_points": key_points,
        "links": links,
        "aliases": aliases,
    }

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

    result = CreateService(self._vault).create_note(
        kwargs["title"],
        subtype=kwargs["subtype"],
        tags=kwargs["tags"],
        topic=kwargs["topic"],
        session=kwargs["session"],
        maturity=kwargs["maturity"],
        body=kwargs["body"],
        key_points=kwargs["key_points"],
        links=kwargs["links"],
        aliases=kwargs["aliases"],
        dispatch_post_create=dispatch_post_create,  # internal flag, NOT in kwargs
    )

    self._dispatch_post_action("create_note", kwargs, result)
    return result
```

### inject_configs insertion (PLUG-03)

```python
# Source: infrastructure/vault.py — init_event_bus()
pm = PluginManager()
local_plugins = self.root / ".ztlctl" / "plugins"
pm.discover_and_load(local_dir=local_plugins)
pm.inject_configs(self._settings)  # PLUG-03: validate + pass TOML config to plugins

git_config = self._settings.git
git_plugin = GitPlugin(config=git_config, vault_root=self.root)
pm.register_plugin(git_plugin, name="git-builtin")

reweave_plugin = ReweavePlugin(vault=self)
pm.register_plugin(reweave_plugin, name="reweave-builtin")
```

### from_result() detail forwarding (AGNT-01)

```python
# Source: mcp/response.py — from_result()
if result.error is not None:
    recovery = result.error.recovery or COMMON_ERROR_RECOVERY.get(result.error.code)
    error = McpError(
        code=result.error.code,
        message=result.error.message,
        recovery=recovery,
        detail=result.error.detail,  # AGNT-01: forward structured error context
    )
```

---

## Complete Action Name Inventory

The following 59 action names (from `_register_core.py`) are the strings to pass to `_dispatch_pre_action`:

**creation category (CreateController):**
`create_note`, `create_reference`, `create_task`, `create_batch`

**mutation category (UpdateController):**
`update`, `archive`, `supersede`

**query category (QueryController):**
`count_items`, `search`, `get`, `list_items`, `work_queue`, `list_tags`, `decision_support`, `topic_packet`, `draft_from_topic`, `vault_review`

**graph category (GraphController):**
`related`, `themes`, `rank`, `path`, `gaps`, `bridges`, `unlink`, `materialize_metrics`

**session category (SessionController):**
`start`, `close`, `reopen`, `status`, `log_entry`, `cost`, `context`, `brief`, `extract_decision`

**enrichment category (ReweaveController):**
`reweave`, `prune`, `undo`

**integrity category (CheckController):**
`check`, `fix`, `rebuild`, `rollback`

**lifecycle category (InitController):**
`init_vault`, `regenerate_self`, `check_staleness`

**export category (ExportController):**
`export_markdown`, `export_indexes`, `export_graph`, `export_dashboard`

**ingest category (IngestController):**
`list_providers`, `ingest_text`, `ingest_file`, `ingest_url`

**vector category (VectorController):**
`vector_status`, `reindex_all`

**workflow category (WorkflowController — ServiceResult methods only):**
`init_workflow`, `update_workflow`, `export_assets`, `validate_assets`

**upgrade category (UpgradeController):**
`check_pending`, `apply`, `stamp_current`

**discovery category (DiscoveryController):**
`discover_categories`, `activate_category`, `deactivate_category`

Note: The exact names for some of these must be verified against `_register_core.py` — the above are derived from method names but the ActionDefinition `name` field is authoritative. Pay special attention to `vector_status` (may be `status` in the registry), `log_entry` (may be `create_log`), `start`/`close` for SessionController.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (uv run pytest) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/controllers/ tests/plugins/ tests/mcp/test_response.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLUG-02 | Controller pre_action fires; rejection aborts service call | unit | `uv run pytest tests/controllers/ -x` | Partial — test_base.py has dispatch unit tests; integration test needed |
| PLUG-02 | post_action fires regardless of result.ok | unit | `uv run pytest tests/controllers/ -x` | Partial |
| PLUG-02 | Action name passed matches ActionDefinition name | integration | `uv run pytest tests/controllers/ -x` | Needs new tests |
| PLUG-03 | inject_configs() called during vault init | integration | `uv run pytest tests/plugins/test_plugin_config.py tests/controllers/ -x` | Needs vault init integration test |
| AGNT-01 | ServiceError.detail forwarded to McpError.detail | unit | `uv run pytest tests/mcp/test_response.py -x` | ❌ New test needed |
| AGNT-04 | REQUIREMENTS.md and generator.py updated with advisory docs | manual review | — | ❌ Docs update |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/controllers/ tests/plugins/ tests/mcp/test_response.py -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] New test in `tests/controllers/test_create.py` (or new `test_hook_wiring.py`) — integration test confirming `_dispatch_pre_action` fires with correct action name for at least one method per controller
- [ ] New test in `tests/mcp/test_response.py` — `test_from_result_forwards_detail()` asserting `McpError.detail` matches `ServiceError.detail`
- [ ] New test in `tests/plugins/test_plugin_config.py` or integration test — confirms `inject_configs()` is called during vault initialization (requires a vault fixture with plugin mock)

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-event hooks (post_create, post_update, etc.) | Generic `pre_action` / `post_action` by action name | Phase 5 (plugin API v2) | Old per-event hooks deprecated but still present; new code MUST use `pre_action`/`post_action` |
| hand-wired MCP tools in register_tools() | Auto-generated from ActionDefinitions | Phase 3 | All tools flow through ActionRegistry → generator.py |

**Deprecated/outdated patterns:**
- `post_create`, `post_update`, `post_close`, `post_reweave`, `post_session_start`, `post_session_close`, `post_check`, `post_init`, `post_init_profile`: deprecated since plugin API v2. The new `pre_action`/`post_action` hooks are the replacement. Do not add any new usage of deprecated hooks.

---

## Open Questions

1. **Exact action names for VectorController and SessionController**
   - What we know: `VectorController.status()` method name conflicts with `SessionController.status()` method name. ActionRegistry must have distinct names.
   - What's unclear: Whether `vector_status` or just `status` is the ActionDefinition name for VectorController. Similarly, `log_entry` vs `create_log` for SessionController.
   - Recommendation: Read `_register_core.py` fully before wiring — use the `name` field from each ActionDefinition, not the method name.

2. **ACTION_REJECTED error code and COMMON_ERROR_RECOVERY entry**
   - What we know: CONTEXT.md gives discretion on the exact code. "ACTION_REJECTED" is suggested.
   - What's unclear: Whether to add "ACTION_REJECTED" to `COMMON_ERROR_RECOVERY` in `response.py`.
   - Recommendation: Add the entry. It's a new error code that agents will see. Without an entry, `from_result()` will silently produce no recovery guidance for rejections.

3. **DiscoveryController methods and kwargs construction**
   - What we know: `discover_categories`, `activate_category`, `deactivate_category` use `**_kwargs` signature and construct ServiceResult inline (no service delegation).
   - What's unclear: Whether the kwargs dict for `discover_categories()` is empty `{}` or includes the catch-all `_kwargs`.
   - Recommendation: Pass `{}` for no-param actions like `discover_categories`; for `activate_category` pass `{"category": category}`.

---

## Sources

### Primary (HIGH confidence)
- `src/ztlctl/controllers/base.py` — `_dispatch_pre_action` and `_dispatch_post_action` implementations read directly
- `src/ztlctl/plugins/manager.py` — `inject_configs()` and `_inject_plugin_configs()` implementations read directly
- `src/ztlctl/mcp/response.py` — `McpResponse.from_result()` read directly; `McpError.detail` field confirmed
- `src/ztlctl/services/result.py` — `ServiceError.detail` field confirmed as `dict[str, Any]`
- `src/ztlctl/infrastructure/vault.py` — `init_event_bus()` body read; insertion point confirmed
- `src/ztlctl/mcp/generator.py` — `_active_categories` module state confirmed; `generate_tools()` unconditional registration confirmed
- `.planning/v2.0-MILESTONE-AUDIT.md` — gap descriptions and fix specifics read directly
- `src/ztlctl/controllers/` — all 14 controller files method signatures read directly
- `src/ztlctl/actions/_register_core.py` — action names and handler patterns read
- `tests/plugins/test_plugin_config.py` — existing test patterns for inject_configs confirmed
- `tests/plugins/test_pre_action_hooks.py` — existing test patterns for hook dispatch confirmed
- `tests/mcp/test_response.py` — existing test file structure confirmed

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions — represent finalized design decisions from the discuss phase

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all components verified by reading source code directly
- Architecture: HIGH — patterns derived from reading actual implementations, no inference
- Pitfalls: HIGH — derived from actual code constraints verified by source reading
- Action name inventory: MEDIUM — method names read from all controller files, but ActionDefinition `name` fields for all 59 must be confirmed in `_register_core.py` (only first ~20 read)

**Research date:** 2026-03-20
**Valid until:** Stable — no external dependencies; all findings are from internal source code
