# Phase 05: Plugin Formalization - Research

**Researched:** 2026-03-19
**Domain:** Python plugin systems (pluggy), API versioning, plugin configuration, NoteTypeDefinition extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Plugin API versioning (PLUG-01)**
- Integer PLUGIN_API_VERSION constant — plugins declare a target version, host validates compatibility at load time. Incompatible plugins are rejected with clear error messages.
- @deprecated decorator — warns for N versions before removal. Provides version-specific deprecation messages so plugin authors know exactly what to change.
- Backward compatibility window — 2 versions minimum before breaking changes. Plugin load emits warnings for deprecated hookspecs, errors for removed ones.

**Pre-action hooks (PLUG-02)**
- pluggy firstresult pattern — synchronous dispatch before controller execution. Hooks receive the action name and kwargs.
- Hooks can modify inputs or abort — return modified kwargs to change inputs, return a rejection object to abort the action before execution. No modification = pass-through.
- Fire in controller layer — pre-hooks dispatch before the handler executes, post-hooks dispatch after. This aligns with the Phase 2 architecture: controllers orchestrate, services are pure logic.

**Plugin configuration (PLUG-03)**
- `[plugins.<name>]` in ztlctl.toml — plugin config lives alongside vault config. Passed to plugins during initialization.
- Pydantic schema validation — plugins declare a Pydantic model for their config. Host validates at load time and passes the validated model to the plugin. Invalid config produces clear errors.

**Custom note types (PLUG-05, PLUG-06)**
- Plugins register NoteTypeDefinitions — custom note types use the same NoteTypeDefinition primitive from Phase 1. Registration into ActionRegistry means they automatically gain CLI commands (via Phase 4 generator) and MCP tools (via Phase 3 generator). Define-once, use-everywhere.
- Render contribution contracts — plugins provide Rich CLI output format and MCP response format for their custom note types. A `RenderContribution` dataclass or protocol defines the interface.

**Marketplace metadata (PLUG-07)**
- `[tool.ztlctl-plugin]` in pyproject.toml — structured metadata (name, version, author, capabilities, compatibility, target API version) for future discoverability. Convention-based, not enforced at load time.

**Built-in plugin migration (validation)**
- Port GitPlugin and ReweavePlugin to new hookspecs — existing built-in plugins serve as the acid test for the new API. Both must work identically after porting. ObsidianPlugin stays as-is (init-only, not lifecycle-driven).
- New hookspec: `pre_action` / `post_action` — replaces the current per-event hookspecs (post_create, post_update, etc.) with a generic action-based pattern. Existing per-event hookspecs become convenience aliases that delegate to the generic hooks.

### Claude's Discretion
- Hook dispatch implementation details — exact pluggy configuration for firstresult, whether to use pluggy's `tryfirst`/`trylast` ordering.
- NoteTypeDefinition registration flow — how plugins register NoteTypeDefinitions (hookspec, decorator, or direct registry call) and when registration happens relative to ActionDefinition registration.
- Render contribution protocol — exact interface shape for Rich and MCP rendering contracts. Whether it's a Protocol, ABC, or dataclass.
- Config schema declaration — how plugins expose their Pydantic config model (class attribute, hookspec return, or registration call).
- Hookspec migration strategy — whether to deprecate old per-event hookspecs immediately or keep them as aliases for the transition period.
- Source provider registration — how `register_source_providers` hookspec relates to the new action-based model (source providers may not map cleanly to ActionDefinitions).

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| PLUG-01 | Plugin API versioning with deprecation helpers — explicit PLUGIN_API_VERSION constant; @deprecated decorator that warns for N versions before removal; compatibility checks at plugin load time | pluggy `warn_on_impl` / `warn_on_impl_args` (available in pluggy 1.5+, project uses 1.6.0) enables hookspec-level deprecation warnings; integer constant + load-time validator is a well-established Python plugin pattern |
| PLUG-02 | Pre-action hooks with modification and cancellation — synchronous dispatch via pluggy firstresult pattern; plugins can modify action inputs or return a rejection to abort the action before execution | `@hookspec(firstresult=True)` confirmed working in pluggy 1.6.0; `BaseController._dispatch_event()` is the injection point; firstresult stops at first non-None return value |
| PLUG-03 | Plugin configuration via `[plugins.<name>]` sections in ztlctl.toml — passed to plugins during initialization; validated against plugin-declared config schema | `PluginsConfig` in models.py already has `git: dict[str, Any]` slot pattern; ZtlSettings loads `[plugins]` section; extending to `extra="allow"` or `dict[str, dict]` enables arbitrary plugin sections |
| PLUG-05 | Custom note types with custom lifecycles registered by plugins — plugins register NoteTypeDefinitions that automatically gain CLI commands (create, update, close) and MCP tools | `NoteTypeRegistry.register()` already public API; `get_note_type_registry()` accessible module-level singleton; ActionRegistry already has `register()` for ActionDefinitions |
| PLUG-06 | Plugin-contributed content type rendering — custom note types control their Rich CLI output and MCP response format via render contribution contracts | `contracts.py` already has frozen dataclass pattern for contributions; existing `RenderContribution` abstraction can follow `VaultInitStepContribution` shape |
| PLUG-07 | Plugin marketplace metadata convention — structured metadata in pyproject.toml `[tool.ztlctl-plugin]` section for future discoverability | Convention-based; no runtime enforcement at load time; validated structure at discovery time only |
</phase_requirements>

---

## Summary

Phase 5 adds a stable, versioned API surface for third-party plugin authors. The codebase is already well-positioned: pluggy 1.6.0 is installed with `firstresult` and `warn_on_impl`/`warn_on_impl_args` support, `NoteTypeRegistry` and `ActionRegistry` are public-facing singletons with documented registration APIs, and the frozen dataclass contribution pattern from `contracts.py` is consistent and extensible.

The core work is four distinct subsystems: (1) an integer `PLUGIN_API_VERSION` constant with a `@deprecated` decorator that leverages pluggy's `warn_on_impl_args` for hookspec-level deprecation; (2) `pre_action` / `post_action` generic hookspecs replacing 8 per-event hookspecs, with firstresult allowing plugins to return a rejection object that aborts execution before the controller handler runs; (3) plugin config validation at load time via `[plugins.<name>]` TOML sections parsed into Pydantic models declared by plugins; and (4) `RenderContribution` frozen dataclasses for custom note type output.

The built-in GitPlugin and ReweavePlugin are ported to the new `pre_action`/`post_action` pattern as the integration acid test. GitPlugin's 8 per-event methods collapse to a single `post_action` implementation with action-name filtering — from 8 hookimpl methods to 1. ReweavePlugin's `post_create` maps directly to `post_action(action_name="create_note", ...)`. Old per-event hookspecs become aliases (delegating to the generic hooks) during the deprecation window.

**Primary recommendation:** Implement `PLUGIN_API_VERSION = 1` constant in `src/ztlctl/plugins/__init__.py`, add `pre_action`/`post_action` hookspecs, wire them into `BaseController` (replacing the current `_dispatch_event` per-event pattern for lifecycle events), then port GitPlugin and ReweavePlugin to validate before marking stable.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pluggy | 1.6.0 | Hook dispatch, firstresult, deprecation warnings | Already installed; powers entire existing plugin system |
| pydantic | >=2.0 | Plugin config schema validation | Already powers ZtlSettings and all service models |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| warnings (stdlib) | 3.13 | Emit DeprecationWarning from @deprecated decorator | Wraps pluggy warn_on_impl emissions |
| dataclasses (stdlib) | 3.13 | Frozen RenderContribution dataclass | Consistent with existing contracts.py pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Integer PLUGIN_API_VERSION | Semantic version string | Integer is simpler for compatibility range checks (current <= target <= current+window) |
| pluggy firstresult for pre-action | Custom dispatch loop | pluggy handles ordering (tryfirst/trylast), firstresult semantics, and exception isolation already |
| Pydantic model for plugin config | TypedDict or dataclass | Pydantic already in use; provides field-level validation errors with context |

**Installation:** No new dependencies. All required libraries are already present.

**Version verification:**
```bash
uv run python -c "import pluggy; print(pluggy.__version__)"  # 1.6.0
uv run python -c "import pydantic; print(pydantic.__version__)"  # >=2.x
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/ztlctl/plugins/
├── __init__.py          # PLUGIN_API_VERSION = 1, @deprecated decorator, hookimpl marker
├── hookspecs.py         # ZtlctlHookSpec: add pre_action/post_action; deprecate old per-event hookspecs
├── manager.py           # PluginManager: add load-time API version check, config injection
├── contracts.py         # Add RenderContribution frozen dataclass
├── event_bus.py         # (unchanged)
└── builtins/
    ├── git.py           # Port to post_action (replaces 8 hookimpl methods)
    ├── reweave_plugin.py  # Port to post_action
    └── obsidian.py      # (unchanged — init-only)
```

### Pattern 1: PLUGIN_API_VERSION + Load-Time Compatibility Check

**What:** Integer constant in `src/ztlctl/plugins/__init__.py`. At load time, `PluginManager.discover_and_load()` checks each plugin's declared `PLUGIN_API_VERSION` against the host's current version and compatibility window.

**When to use:** Every plugin load. Incompatible plugins are rejected with a clear error message. Deprecated API plugins emit warnings.

**Example:**
```python
# Source: pluggy 1.6.0 API (verified locally)

# src/ztlctl/plugins/__init__.py
PLUGIN_API_VERSION: int = 1
_COMPATIBILITY_WINDOW: int = 2  # warn but accept versions >= (current - window)
hookimpl = pluggy.HookimplMarker("ztlctl")

def check_plugin_api_version(plugin: object, plugin_name: str) -> list[str]:
    """Return list of warnings; raise PluginLoadError if incompatible."""
    declared = getattr(plugin, "PLUGIN_API_VERSION", None)
    if declared is None:
        return []  # legacy plugin — no version declared, accept with warning
    if declared > PLUGIN_API_VERSION:
        raise PluginLoadError(
            f"Plugin {plugin_name!r} requires API version {declared} "
            f"but host provides {PLUGIN_API_VERSION}"
        )
    if declared < PLUGIN_API_VERSION - _COMPATIBILITY_WINDOW:
        raise PluginLoadError(
            f"Plugin {plugin_name!r} targets API version {declared} "
            f"which is no longer supported (min: {PLUGIN_API_VERSION - _COMPATIBILITY_WINDOW})"
        )
    if declared < PLUGIN_API_VERSION:
        return [
            f"Plugin {plugin_name!r} targets API version {declared}; "
            f"consider updating to {PLUGIN_API_VERSION}"
        ]
    return []
```

### Pattern 2: @deprecated Decorator for Hookspec Deprecation

**What:** A `@deprecated` decorator that wraps a hookspec method, adding a `DeprecationWarning` emission when implemented. Leverages pluggy's `warn_on_impl` parameter to issue warnings at plugin-registration time rather than at call time.

**When to use:** On old per-event hookspecs (post_create, post_update, etc.) after migrating to pre_action/post_action. These remain as aliases but warn plugin authors.

**Example:**
```python
# Source: pluggy 1.6.0 API (verified locally) — warn_on_impl available since pluggy 1.3

# src/ztlctl/plugins/hookspecs.py
import warnings

hookspec = pluggy.HookspecMarker("ztlctl")

class ZtlctlHookSpec:
    # New generic hooks (stable)
    @hookspec(firstresult=True)
    def pre_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
    ) -> ActionRejection | dict[str, Any] | None:
        """Called before action execution. Return modified kwargs, ActionRejection to abort, or None."""

    @hookspec
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        """Called after action execution with the ServiceResult."""

    # Deprecated per-event hookspecs — keep as aliases during transition window
    @hookspec(
        warn_on_impl=DeprecationWarning(
            "post_create is deprecated; implement post_action and filter by "
            "action_name in {'create_note', 'create_reference', 'create_task'}"
        )
    )
    def post_create(self, content_type: str, content_id: str, title: str, path: str, tags: list[str]) -> None:
        """Deprecated: use post_action instead."""
```

### Pattern 3: ActionRejection Dataclass for Pre-Action Abort

**What:** A frozen dataclass returned by `pre_action` hooks to signal that an action should be aborted before execution. First non-None return from firstresult chain stops dispatch.

**When to use:** When a plugin needs to prevent an action from running (e.g., dry-run mode, validation gate, quota enforcement).

**Example:**
```python
# src/ztlctl/plugins/contracts.py
@dataclass(frozen=True)
class ActionRejection:
    """Returned from pre_action to abort action execution before the handler runs."""
    reason: str
    code: str = "plugin_rejected"
    detail: dict[str, Any] = field(default_factory=dict)
```

### Pattern 4: Pre-Action Hook Dispatch in BaseController

**What:** `BaseController._dispatch_pre_action()` calls `pre_action` hookspec via pluggy firstresult. If an `ActionRejection` is returned, the controller returns a failed `ServiceResult` without calling the service. If modified kwargs are returned, the controller uses those instead.

**When to use:** At the top of every controller method that represents a named action in ActionRegistry.

**Example:**
```python
# src/ztlctl/controllers/base.py

class BaseController:
    def _dispatch_pre_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
    ) -> tuple[dict[str, Any], ActionRejection | None]:
        """Dispatch pre_action hook. Returns (possibly modified kwargs, rejection or None)."""
        pm = self._vault.plugin_manager
        if pm is None:
            return kwargs, None
        try:
            result = pm.hook.pre_action(action_name=action_name, kwargs=kwargs)
        except Exception:
            logger.debug("pre_action dispatch failed for %s", action_name, exc_info=True)
            return kwargs, None  # failure is a warning, never an error

        if isinstance(result, ActionRejection):
            return kwargs, result
        if isinstance(result, dict):
            return result, None  # modified kwargs
        return kwargs, None  # None = pass-through

    def _dispatch_post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        """Dispatch post_action hook. Failures are warnings, never errors."""
        pm = self._vault.plugin_manager
        if pm is None:
            return
        try:
            pm.hook.post_action(action_name=action_name, kwargs=kwargs, result=result)
        except Exception:
            logger.debug("post_action dispatch failed for %s", action_name, exc_info=True)
```

### Pattern 5: Plugin Config via [plugins.<name>] Sections

**What:** `PluginsConfig` in `models.py` is extended to carry arbitrary `dict[str, dict[str, Any]]` for plugin sections. At plugin load time, `PluginManager` calls an optional `get_config_schema()` hookspec on each plugin to retrieve its Pydantic model class, then validates the TOML section and passes the validated model to `plugin.initialize(config)`.

**When to use:** Any plugin that reads `[plugins.<name>]` from ztlctl.toml.

**Example:**
```python
# Approach: hookspec return for config schema
# src/ztlctl/plugins/hookspecs.py
class ZtlctlHookSpec:
    @hookspec(firstresult=True)
    def get_config_schema(self) -> type[BaseModel] | None:
        """Return the Pydantic model class for this plugin's config section."""

    @hookspec
    def initialize(self, config: BaseModel | None) -> None:
        """Called after load with validated plugin config (or None if no schema declared)."""
```

```python
# models.py — extend PluginsConfig to accept arbitrary plugin sections
class PluginsConfig(BaseModel):
    model_config = {"frozen": False, "extra": "allow"}  # or dict[str, dict[str, Any]]

    git: dict[str, Any] = Field(default_factory=lambda: {"enabled": True})
    # extra fields captured as plugin-named dicts
```

### Pattern 6: RenderContribution for Custom Note Types

**What:** A frozen dataclass that plugins return from a `register_render_contributions()` hookspec. Contains a Rich formatter callable and an MCP response formatter callable keyed to a note type name.

**When to use:** When a plugin registers a custom `NoteTypeDefinition` and needs custom output.

**Example:**
```python
# src/ztlctl/plugins/contracts.py
@dataclass(frozen=True)
class RenderContribution:
    """Plugin-provided rendering for a custom note type."""
    note_type: str
    rich_formatter: Callable[[dict[str, Any]], str]  # returns Rich markup string
    mcp_formatter: Callable[[dict[str, Any]], dict[str, Any]]  # returns MCP response dict
```

### Pattern 7: Plugin NoteTypeDefinition + ActionDefinition Registration via Hookspec

**What:** A new `register_note_types()` hookspec returns `list[NoteTypeDefinition]`. `PluginManager` calls it at load time and registers each definition into `NoteTypeRegistry` and creates matching ActionDefinitions in `ActionRegistry`. The generators (CLI and MCP) then auto-surface these.

**Recommended flow:**
1. Plugin implements `register_note_types()` returning `[NoteTypeDefinition(...)]`
2. `PluginManager._register_note_types()` iterates results, calls `NoteTypeRegistry.register()`
3. For each registered NoteTypeDefinition, `PluginManager` auto-creates ActionDefinitions for create/update/close and calls `ActionRegistry.register()`
4. CLI generator and MCP generator iterate ActionRegistry — plugin types appear automatically

**Example:**
```python
# hookspecs.py
class ZtlctlHookSpec:
    @hookspec
    def register_note_types(self) -> list[NoteTypeDefinition] | None:
        """Return NoteTypeDefinitions to register into NoteTypeRegistry + ActionRegistry."""
```

### Pattern 8: GitPlugin Migration to post_action

**What:** GitPlugin currently implements 8 per-event hookimpl methods. After porting, it implements one `post_action` method with action-name filtering. The same behavior is preserved — staging and committing — based on the action name.

**Example:**
```python
# src/ztlctl/plugins/builtins/git.py (after migration)
class GitPlugin:
    PLUGIN_API_VERSION = 1

    @hookimpl
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        if not self._enabled or not result.ok:
            return
        if action_name in {"create_note", "create_reference", "create_task"}:
            self._git_add(result.data.get("path", "."))
            if not self._config.batch_commits:
                self._git_commit(f"feat: {action_name} {result.data.get('id', '')}")
        elif action_name in {"update_note", "close_note", ...}:
            ...
        elif action_name == "session_close":
            self._commit_session_batch(result.data.get("session_id", ""))
```

### Pattern 9: Marketplace Metadata Convention

**What:** `[tool.ztlctl-plugin]` section in a plugin's `pyproject.toml`. Structured metadata convention for future discovery tooling. No runtime enforcement at load time in Phase 5.

**Example:**
```toml
[tool.ztlctl-plugin]
name = "my-vault-plugin"
version = "1.0.0"
author = "Author Name <email@example.com>"
capabilities = ["note_types", "lifecycle_hooks"]
ztlctl_api_version = 1
description = "Adds custom note types for project management"
```

### Anti-Patterns to Avoid
- **Don't check PLUGIN_API_VERSION after hook dispatch** — check it in `register_plugin()` / `discover_and_load()` before hooks fire.
- **Don't raise in pre_action implementations** — return `ActionRejection` instead. Raises are caught and treated as warnings, so silent pass-through would occur if an exception is raised instead of a rejection.
- **Don't put plugin config validation inside hookimpl methods** — validate at load time in `PluginManager._inject_plugin_config()`.
- **Don't mutate kwargs in pre_action directly** — return a new dict (frozen dataclass principle).
- **Don't bypass NoteTypeRegistry validation** — always call `registry.register()` which enforces transition map integrity.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hook dispatch ordering | Custom priority queue | pluggy `tryfirst`/`trylast` on `@hookimpl` | pluggy already handles ordering within the firstresult chain |
| Deprecation warning delivery | Custom warning registry | pluggy `warn_on_impl` on `@hookspec` | Fires at plugin registration time, not at call time — no overhead in the hot path |
| Plugin config deserialization | Manual TOML parsing in each plugin | Pydantic model + PluginManager injection | Consistent error messages, field-level validation, freezing |
| CLI/MCP surface for custom types | Per-plugin Click commands | Register ActionDefinitions into ActionRegistry | Phase 4 generators auto-generate CLI and MCP tools for free |
| Transition map validation | Ad-hoc state checks | `NoteTypeRegistry.register()` existing validation | Already enforces all-targets-are-keys invariant |

**Key insight:** The define-once architecture from Phases 1-4 means plugin note types get CLI commands, MCP tools, and lifecycle validation for free by registering `NoteTypeDefinition` + `ActionDefinition`. The plugin author writes the business logic only.

---

## Common Pitfalls

### Pitfall 1: pre_action Firstresult Returns None by Default
**What goes wrong:** A plugin's `pre_action` method returns `None` implicitly (no explicit return), which pluggy treats as "pass-through" for firstresult — not a rejection. An early plugin that should abort silently does nothing.
**Why it happens:** Python functions return `None` by default; firstresult continues to the next plugin on `None`.
**How to avoid:** Document and enforce that `ActionRejection` is the only abort mechanism. Tests for rejection must assert the `ActionRejection` is returned, not just check the result.
**Warning signs:** Actions that "should have been aborted" still execute.

### Pitfall 2: Plugin Config Extra Fields Silently Ignored in Frozen Pydantic Models
**What goes wrong:** `PluginsConfig` currently uses `model_config = {"frozen": True}` without `extra = "allow"`. When a third-party plugin adds `[plugins.myplugin]` to ztlctl.toml, the fields are silently ignored during deserialization.
**Why it happens:** Pydantic's default `extra = "ignore"` drops unknown fields.
**How to avoid:** Change `PluginsConfig` to use `extra = "allow"` or store plugin configs as `dict[str, dict[str, Any]]` with a separate field. Access via `settings.plugins.model_extra["myplugin"]` or a dedicated lookup method.
**Warning signs:** Plugin config reads return defaults even when TOML values are present.

### Pitfall 3: ActionRegistry Double-Registration for Plugin Types
**What goes wrong:** If `register_note_types()` hookspec is called more than once (e.g., during test setup), `ActionRegistry.register()` raises `ValueError` on duplicate name.
**Why it happens:** `ActionRegistry` and `NoteTypeRegistry` are module-level singletons. Test teardown doesn't reset them.
**How to avoid:** Guard `PluginManager._register_note_types()` with a per-plugin seen-set, same pattern as `_normalize_plugin_instances()` uses. Add deregistration support or use a fixture that clears registrations.
**Warning signs:** `ValueError: Action 'plugin.create_custom' is already registered` in tests.

### Pitfall 4: post_action Fires on Failed ServiceResults
**What goes wrong:** GitPlugin's `post_action` stages files even when the service returned `result.ok == False`. This creates ghost git-staged paths for failed operations.
**Why it happens:** post_action receives the ServiceResult but a naive implementation ignores the `ok` flag.
**How to avoid:** All `post_action` implementations MUST check `result.ok` before taking side effects. Document this in the hookspec docstring.
**Warning signs:** Git shows staged changes that don't correspond to committed vault content.

### Pitfall 5: Per-Event Hookspec Aliases That Dispatch Twice
**What goes wrong:** During migration, if the deprecated `post_create` hookspec delegates to `post_action` AND services still call `_dispatch_event("post_create", ...)` via EventBus, some plugins receive both the old and new hook calls for the same action.
**Why it happens:** The EventBus dispatches per-event hookspecs, while BaseController dispatches the new generic hookspecs — both for the same lifecycle event.
**How to avoid:** Migrate services/controllers to call only `_dispatch_post_action()` during this phase. Remove direct `_dispatch_event("post_create", ...)` calls from services. Old per-event hookspecs fire ONLY via the alias delegation from `post_action`.
**Warning signs:** GitPlugin commits twice per create operation.

### Pitfall 6: Vault Not Exposing plugin_manager to BaseController
**What goes wrong:** `BaseController._dispatch_pre_action()` needs `self._vault.plugin_manager` but `Vault` may not expose `PluginManager` directly.
**Why it happens:** Vault currently exposes `event_bus` (which wraps PluginManager internally). Pre-action hooks need to call `pm.hook.pre_action()` directly — bypassing EventBus (which is async, WAL-backed, for post-events).
**How to avoid:** Add `vault.plugin_manager` property. Or add `pre_action()` and `post_action()` dispatch methods directly on `EventBus` (in synchronous, no-WAL mode since pre-action must be synchronous).
**Warning signs:** NameError or AttributeError when trying to call pre_action from a controller.

---

## Code Examples

Verified patterns from official sources:

### pluggy firstresult hookspec (verified against pluggy 1.6.0)
```python
# Source: pluggy 1.6.0 local API inspection
hookspec = pluggy.HookspecMarker("ztlctl")

class ZtlctlHookSpec:
    @hookspec(firstresult=True)
    def pre_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
    ) -> "ActionRejection | dict[str, Any] | None":
        """firstresult: stops at first non-None return."""
```

### pluggy warn_on_impl for deprecated hookspecs (verified against pluggy 1.5+/1.6.0)
```python
# Source: pluggy 1.6.0 local API inspection
# warn_on_impl fires at plugin REGISTRATION time, not at call time
@hookspec(
    warn_on_impl=DeprecationWarning(
        "post_create is deprecated since API v2; implement post_action instead."
    )
)
def post_create(self, content_type: str, ...) -> None: ...
```

### pluggy tryfirst/trylast on hookimpl (verified against pluggy 1.6.0)
```python
# Source: pluggy 1.6.0 local API inspection
hookimpl = pluggy.HookimplMarker("ztlctl")

class MyPlugin:
    @hookimpl(tryfirst=True)  # runs before other pre_action implementations
    def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> ...:
        ...
```

### NoteTypeRegistry public registration (verified from src/ztlctl/domain/registry.py)
```python
# Source: src/ztlctl/domain/registry.py
from ztlctl.domain.registry import get_note_type_registry, NoteTypeDefinition

get_note_type_registry().register(
    NoteTypeDefinition(
        name="sprint",
        content_type="task",
        model_cls=SprintModel,
        transitions={"open": ["closed"], "closed": []},
        template_name="sprint.md.j2",
        is_subtype=True,
        parent_type="task",
    )
)
```

### ActionRegistry plugin registration (verified from src/ztlctl/actions/registry.py)
```python
# Source: src/ztlctl/actions/registry.py
from ztlctl.actions.registry import get_action_registry
from ztlctl.actions.definitions import ActionDefinition, ActionParam

get_action_registry().register(
    ActionDefinition(
        name="create_sprint",
        description="Create a sprint task in the vault.",
        category="creation",
        params=(...),
        handler=lambda vault, **kw: SprintController(vault).create_sprint(**kw),
        side_effect="write",
    )
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 8 per-event hookspecs (post_create, post_update, ...) | Generic pre_action/post_action with action-name filtering | Phase 5 (this phase) | GitPlugin collapses from 8 hookimpl methods to 1; plugin authors write 1 method |
| No API versioning | Integer PLUGIN_API_VERSION + 2-version compatibility window | Phase 5 (this phase) | Third-party plugins can target a stable API version and be warned before breaking |
| No plugin config validation | Pydantic schema at load time via get_config_schema() hookspec | Phase 5 (this phase) | Invalid plugin config fails fast at startup, not at first use |
| Manual CLI/MCP tools per plugin type | Register ActionDefinitions → auto-generated | Phase 5 (this phase) | Payoff of Phases 2-4 architecture: plugin types get CLI+MCP for free |

**Deprecated/outdated after this phase:**
- `post_create`, `post_update`, `post_close`, `post_reweave`, `post_session_start`, `post_session_close`, `post_check`, `post_init`, `post_init_profile` — all deprecated in favor of `pre_action`/`post_action`. Kept as aliases during the 2-version window.

---

## Open Questions

1. **Vault.plugin_manager property**
   - What we know: `BaseController` needs to call `pm.hook.pre_action()` synchronously before service execution. The EventBus currently wraps PluginManager but is async/WAL-backed.
   - What's unclear: Does Vault expose `plugin_manager` directly? If not, should pre-action dispatch go through EventBus in a "sync bypass" mode, or should a separate `vault.plugin_manager` property be added?
   - Recommendation: Add `vault.plugin_manager` as a direct property. Pre-action hooks MUST be synchronous and must not be WAL-buffered — a separate code path from post-event EventBus dispatch is correct.

2. **PluginsConfig extra-field strategy**
   - What we know: `PluginsConfig` currently has a hardcoded `git: dict[str, Any]` field. Third-party plugin configs use `[plugins.<name>]` sections that don't have hardcoded field names.
   - What's unclear: Whether to use `model_config = {"extra": "allow"}` (Pydantic stores extras in `model_extra`) or to replace with `dict[str, dict[str, Any]]` holding all plugin configs.
   - Recommendation: Replace `PluginsConfig` internals with `extra = "allow"` and a `get_plugin_config(name: str) -> dict[str, Any]` helper. The `git` field becomes `model_extra["git"]` for backward compat, or keep the explicit field alongside extras. Need to verify Pydantic v2 frozen + extra = "allow" interaction.

3. **Source provider hookspec and pre_action**
   - What we know: `register_source_providers` provides source ingestion providers, not lifecycle actions. Source providers don't map cleanly to ActionDefinitions.
   - What's unclear: Whether `register_source_providers` stays as-is (a registration hookspec) or gets migrated to the new action-based model.
   - Recommendation: Leave `register_source_providers` as-is — it's a registration hook, not a lifecycle hook, and doesn't benefit from pre_action/post_action migration.

4. **Auto-generating create/update/close ActionDefinitions for plugin note types**
   - What we know: The planner must decide how ActionDefinitions are created for plugin note types. The plugin author could register them manually OR `PluginManager` auto-generates them from the NoteTypeDefinition.
   - What's unclear: Whether auto-generation produces correct `handler` lambdas pointing to the right controller methods with the right parameters.
   - Recommendation: Auto-generate via `PluginManager._register_note_type_actions()`: for each NoteTypeDefinition returned by `register_note_types()`, create 3 ActionDefinitions (create, update, close) using the existing controller pattern. This is the "define-once" payoff.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/plugins/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PLUG-01 | PLUGIN_API_VERSION constant exists and is an integer | unit | `uv run pytest tests/plugins/test_versioning.py -x` | ❌ Wave 0 |
| PLUG-01 | Compatible plugin loads without warning | unit | `uv run pytest tests/plugins/test_versioning.py::test_compatible_plugin_loads -x` | ❌ Wave 0 |
| PLUG-01 | Plugin too new raises PluginLoadError | unit | `uv run pytest tests/plugins/test_versioning.py::test_plugin_too_new_rejected -x` | ❌ Wave 0 |
| PLUG-01 | Plugin too old raises PluginLoadError | unit | `uv run pytest tests/plugins/test_versioning.py::test_plugin_too_old_rejected -x` | ❌ Wave 0 |
| PLUG-01 | Deprecated API version emits warning | unit | `uv run pytest tests/plugins/test_versioning.py::test_deprecated_api_version_warns -x` | ❌ Wave 0 |
| PLUG-01 | @deprecated hookspec warns on implementation | unit | `uv run pytest tests/plugins/test_hookspecs.py::test_deprecated_post_create_warns -x` | ❌ Wave 0 |
| PLUG-02 | pre_action firstresult stops on ActionRejection | unit | `uv run pytest tests/plugins/test_pre_action.py::test_rejection_aborts_action -x` | ❌ Wave 0 |
| PLUG-02 | pre_action modified kwargs passed to handler | unit | `uv run pytest tests/plugins/test_pre_action.py::test_modified_kwargs_used -x` | ❌ Wave 0 |
| PLUG-02 | pre_action None return is pass-through | unit | `uv run pytest tests/plugins/test_pre_action.py::test_none_return_passthrough -x` | ❌ Wave 0 |
| PLUG-02 | post_action fires after handler completes | unit | `uv run pytest tests/plugins/test_pre_action.py::test_post_action_fires -x` | ❌ Wave 0 |
| PLUG-02 | pre_action exception is warning not error | unit | `uv run pytest tests/plugins/test_pre_action.py::test_exception_is_warning -x` | ❌ Wave 0 |
| PLUG-03 | [plugins.name] section parsed and injected | unit | `uv run pytest tests/plugins/test_plugin_config.py::test_config_injected -x` | ❌ Wave 0 |
| PLUG-03 | Invalid plugin config raises at load time | unit | `uv run pytest tests/plugins/test_plugin_config.py::test_invalid_config_rejected -x` | ❌ Wave 0 |
| PLUG-05 | Plugin-registered NoteTypeDefinition gains CLI commands | integration | `uv run pytest tests/plugins/test_custom_note_types.py::test_custom_type_cli_commands -x` | ❌ Wave 0 |
| PLUG-05 | Plugin-registered NoteTypeDefinition gains MCP tools | integration | `uv run pytest tests/plugins/test_custom_note_types.py::test_custom_type_mcp_tools -x` | ❌ Wave 0 |
| PLUG-06 | RenderContribution rich_formatter called for custom type | unit | `uv run pytest tests/plugins/test_render_contributions.py::test_rich_formatter_called -x` | ❌ Wave 0 |
| PLUG-06 | RenderContribution mcp_formatter called for custom type | unit | `uv run pytest tests/plugins/test_render_contributions.py::test_mcp_formatter_called -x` | ❌ Wave 0 |
| PLUG-07 | Marketplace metadata helper reads [tool.ztlctl-plugin] | unit | `uv run pytest tests/plugins/test_marketplace.py::test_metadata_read -x` | ❌ Wave 0 |
| (migration) | GitPlugin post_action handles create_note | unit | `uv run pytest tests/plugins/test_git_plugin.py::test_post_action_create_note -x` | ❌ add to existing |
| (migration) | ReweavePlugin post_action handles create_note | unit | `uv run pytest tests/plugins/test_reweave_plugin.py::test_post_action_create_note -x` | ❌ add to existing |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/plugins/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/plugins/test_versioning.py` — covers PLUG-01 (API versioning, @deprecated, load-time checks)
- [ ] `tests/plugins/test_hookspecs.py` — covers PLUG-01 (deprecated hookspec warnings)
- [ ] `tests/plugins/test_pre_action.py` — covers PLUG-02 (firstresult, ActionRejection, post_action)
- [ ] `tests/plugins/test_plugin_config.py` — covers PLUG-03 (config injection and validation)
- [ ] `tests/plugins/test_custom_note_types.py` — covers PLUG-05 (NoteTypeDefinition registration + auto CLI/MCP)
- [ ] `tests/plugins/test_render_contributions.py` — covers PLUG-06 (RenderContribution contracts)
- [ ] `tests/plugins/test_marketplace.py` — covers PLUG-07 (marketplace metadata reading)

---

## Sources

### Primary (HIGH confidence)
- pluggy 1.6.0 local installation — `warn_on_impl`, `warn_on_impl_args`, `firstresult`, `tryfirst`, `trylast` all verified via `help()` and live test
- `src/ztlctl/plugins/hookspecs.py` — 16 current hookspecs, all param shapes
- `src/ztlctl/plugins/manager.py` — discovery, `_collect_contributions`, `_register_content_models` patterns
- `src/ztlctl/plugins/contracts.py` — frozen dataclass contribution pattern
- `src/ztlctl/plugins/builtins/git.py` — 8 hookimpl methods to be collapsed
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — post_create hook to migrate
- `src/ztlctl/domain/registry.py` — NoteTypeDefinition + NoteTypeRegistry.register() public API
- `src/ztlctl/actions/registry.py` — ActionRegistry.register() public API
- `src/ztlctl/actions/definitions.py` — ActionDefinition + ActionParam shapes
- `src/ztlctl/controllers/base.py` — BaseController._dispatch_event() injection point
- `src/ztlctl/config/models.py` — PluginsConfig current shape (git: dict[str, Any])
- `src/ztlctl/config/settings.py` — ZtlSettings TOML loading chain, `plugins: PluginsConfig`

### Secondary (MEDIUM confidence)
- pluggy official documentation pattern for `warn_on_impl` (versionadded: 1.5, in 1.6.0 docs)

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are already installed and verified locally
- Architecture: HIGH — all integration points are read from actual source files; no guessing
- Pitfalls: HIGH — identified from reading actual source code (PluginsConfig frozen, EventBus async, duplicate registration)
- Validation architecture: HIGH — pytest 9.0.2, test structure verified from filesystem scan

**Research date:** 2026-03-19
**Valid until:** 2026-06-19 (stable libraries; pluggy API changes rarely)
