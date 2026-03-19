# Phase 2: Action Registry — Research

**Researched:** 2026-03-19
**Domain:** Declarative action registry infrastructure + 4-layer architectural refactoring (service/controller split)
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Architecture — 4-Layer Refactoring**
- **Data layer**: Repository pattern encapsulating DB + filesystem. The current `Vault`, `VaultTransaction`, `DatabaseEngine`, `FilesystemOps` largely fill this role. ACID guarantees managed here via SQLAlchemy transactions + compensation-based file rollback. Services should NOT directly manage files or databases.
- **Service layer**: Pure domain logic — side-effect-free functions that take inputs and return results. Current services mix orchestration with domain logic; this needs separation. Services should be composable, testable in isolation, and free of Vault/transaction management.
- **Controller layer** (NEW): Orchestrates service calls + data layer operations. Manages transactions, dispatches events, coordinates multi-step workflows. The controller is the single interface for the registry layer. This replaces the current pattern where services do both domain logic and orchestration.
- **Registry layer** (NEW): Wraps controller methods with required schema (type hints, docstrings, parameter metadata). Provides auto-mapping to CLI and MCP. The registry is the only way to connect controller functionality to events and to generate presentation layer interfaces.

**Registration — All Public Methods**
- **ALL public controller methods** get ActionDefinitions — no exceptions.
- **No escape hatches**: Complex commands (batch, init wizard, serve) still go through the registry with thin definitions. They can be marked for custom presentation (the registry skips auto-generation but the action is still registered, discoverable, and hookable).
- **Controller is the only way to expose functionality**: No direct service-to-CLI/MCP paths. Everything flows through controllers → registry → presentation.

**Scope — Full Refactor in Phase 2**
- This is NOT registry-only — Phase 2 includes refactoring existing services into the controller+service+data split.
- The goal is that by end of Phase 2, the new architecture is in place and all existing operations are registered as ActionDefinitions through their controllers.
- CLI and MCP continue to work via the current hand-written code during Phase 2 — auto-generation replaces them in Phases 3-4.

### Claude's Discretion

- **ActionDefinition dataclass shape**: What fields it carries, how metadata is structured, complexity budget per definition. Research recommended 50-line budget.
- **Param type system**: How ActionParam maps to both Click types and MCP JSON schema. Single type system that generates both.
- **Controller granularity**: How to split current services. Whether each current service becomes one controller or whether controllers are organized differently (by domain area, by command group, etc.).
- **Migration strategy**: How to incrementally refactor without breaking existing CLI/MCP. Whether to do service-by-service or all-at-once.
- **Event dispatch location**: Whether events fire from controllers (new location) or stay in services (current location via BaseService._dispatch_event).

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ACTN-01 | ActionDefinition dataclass — name, typed params (ActionParam), service method binding, CLI metadata (group, help, interactive params), MCP metadata (catalog entries, when_to_use, avoid_when) | NoteTypeDefinition frozen dataclass pattern directly transferable; `ToolCatalogEntry` TypedDict provides the MCP metadata shape; CLI metadata mirrors existing Click command parameters |
| ACTN-02 | ActionRegistry — collects ActionDefinitions from core modules and plugins; validates uniqueness; provides lookup by name; single source of truth for all operations | NoteTypeRegistry implements the identical register/get/list pattern; the controller split creates the clean registration boundary; 45+ public service methods quantified as the registration target |
</phase_requirements>

---

## Summary

Phase 2 builds the ActionDefinition/ActionRegistry infrastructure and refactors the existing 12-service codebase into a clean 4-layer architecture. The phase does NOT generate CLI or MCP surfaces from the registry — that is Phases 3 and 4. The deliverable is: (1) a new `actions/` package with `ActionParam`, `ActionDefinition`, `ActionRegistry` dataclasses, (2) a new `controllers/` package where each controller wraps a set of related service calls with transaction and event orchestration, and (3) all 45+ public service operations registered as `ActionDefinition` objects pointing to their controller methods.

The template for the entire pattern already exists in the codebase: `domain/registry.py` implements `NoteTypeDefinition` (frozen dataclass) and `NoteTypeRegistry` (register/get/list with validation). The `ActionDefinition` and `ActionRegistry` follow the same structural pattern with different fields. The `_impl` functions in `mcp/tools.py` are proto-controllers — they already receive a `Vault`, orchestrate service calls, and return results. The controller layer formalizes exactly that pattern.

The key architectural invariant from CONTEXT.md: "The controller layer is the only way to expose functionality; the registry layer is the only way to connect that functionality to events." This means no direct service-to-CLI or service-to-MCP paths survive Phase 2.

**Primary recommendation:** Follow the service-by-service migration strategy. Introduce `BaseController` and the `actions/` package first as pure infrastructure, then port each service to a controller one-by-one (starting with the smallest, e.g., `CheckService` / `UpdateService`), registering all their ActionDefinitions along the way.

---

## Standard Stack

### Core (no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python dataclasses (`@dataclass(frozen=True)`) | stdlib | ActionDefinition / ActionParam / ActionRegistry data structures | Same pattern as existing NoteTypeDefinition; zero dep overhead; frozen = thread-safe |
| Python typing (`Callable`, `Literal`, `Any`) | stdlib | Handler binding type, side_effect enum, flexible param types | Already used throughout domain layer |
| pydantic | >=2.8 (pinned in pyproject.toml) | ServiceResult (unchanged); validation at controller boundaries | Universal return type; no change needed |
| pytest | >=8.3 (pinned) | Unit tests for ActionDefinition/ActionRegistry/controllers | Existing test infrastructure — just add test files |

### No New Runtime Dependencies

This phase introduces zero new packages. The action registry and controller layer are ~500 LOC of pure Python using only what is already installed. Pre-existing research confirmed no mature library handles the Click-groups-plus-MCP-schema use case.

**Verification:** No `uv add` calls are needed for this phase.

---

## Architecture Patterns

### Recommended Project Structure

```
src/ztlctl/
├── domain/
│   └── registry.py          # NoteTypeDefinition/NoteTypeRegistry (UNCHANGED — template)
├── actions/                  # NEW: Action registry infrastructure
│   ├── __init__.py           # Exports ActionDefinition, ActionParam, ActionRegistry
│   ├── definitions.py        # ActionParam + ActionDefinition frozen dataclasses
│   ├── registry.py           # ActionRegistry class + get_action_registry() singleton
│   └── _register_core.py    # Registers all built-in ActionDefinitions at module load
├── controllers/              # NEW: Orchestration layer (controller-per-domain)
│   ├── __init__.py
│   ├── base.py               # BaseController with _vault injection + _dispatch_event()
│   ├── create.py             # CreateController: wraps CreateService
│   ├── query.py              # QueryController: wraps QueryService + ContextAssembler
│   ├── graph.py              # GraphController: wraps GraphService
│   ├── update.py             # UpdateController: wraps UpdateService
│   ├── reweave.py            # ReweaveController: wraps ReweaveService
│   ├── session.py            # SessionController: wraps SessionService
│   ├── check.py              # CheckController: wraps CheckService
│   ├── ingest.py             # IngestController: wraps IngestService
│   ├── export.py             # ExportController: wraps ExportService
│   ├── vector.py             # VectorController: wraps VectorService
│   ├── workflow.py           # WorkflowController: wraps WorkflowService (custom_presentation=True)
│   └── init_ctrl.py          # InitController: wraps InitService (custom_presentation=True)
└── services/                 # REFACTORED: pure domain logic only, no transaction management
    └── (existing files — transaction mgmt moves to controllers)
```

### Pattern 1: ActionParam Dataclass

**What:** Typed descriptor for a single parameter of an action. Maps to Click option and MCP JSON schema field simultaneously.

**When to use:** Every parameter of every ActionDefinition.

```python
# Source: design derived from domain/registry.py NoteTypeDefinition pattern
# + existing ToolCatalogEntry args_guidance + create_note_impl parameter shapes

@dataclass(frozen=True)
class ActionParam:
    """One parameter descriptor — single source of truth for CLI and MCP."""
    name: str
    type: type                          # Python built-in: str, int, bool, list[str]
    required: bool = True
    default: Any = None
    description: str = ""
    choices: tuple[str, ...] | None = None   # constrained set (generates Click.Choice + MCP enum)
    cli_multiple: bool = False          # Click: --tags a --tags b --tags c
    cli_is_argument: bool = False       # Click: positional arg vs --option
    cli_flag: bool = False              # Click: --flag / --no-flag (for bool params)
    mcp_example: str = ""               # placed in args_guidance for MCP catalog
```

**Design note:** `choices` uses `tuple[str, ...]` not `list[str]` to maintain frozen dataclass compatibility. `type` carries Python-native types (`str`, `int`, `bool`, `list[str]`) — generators convert these to Click and JSON Schema representations, not the ActionParam itself.

### Pattern 2: ActionDefinition Dataclass

**What:** Declarative descriptor for one operation. One definition produces one controller binding, one CLI command (Phases 3-4), and one MCP tool (Phases 3-4).

**Complexity budget:** 50 lines per definition (per PITFALLS.md Pitfall 4). Definitions exceeding this indicate the abstraction is too heavy.

```python
# Source: ARCHITECTURE.md canonical design + ToolCatalogEntry TypedDict shape
# from src/ztlctl/mcp/tools.py

@dataclass(frozen=True)
class ActionDefinition:
    """One operation in the system. Frozen for thread safety and hashability."""

    # Core identity
    name: str                                      # e.g. "create_note", "graph_related"
    description: str                               # human-readable; used for CLI help + MCP description
    category: str                                  # e.g. "creation", "query", "graph", "lifecycle"
    params: tuple[ActionParam, ...]
    handler: Callable[..., ServiceResult]          # bound controller method
    side_effect: Literal["read", "write"]

    # MCP-specific metadata (optional — empty strings = omit from generated catalog)
    mcp_when_to_use: str = ""
    mcp_avoid_when: str = ""
    mcp_common_errors: tuple[str, ...] = ()

    # CLI-specific metadata (optional overrides)
    cli_group: str | None = None                   # which Click group to attach to (e.g. "graph")
    cli_examples: str = ""
    cli_interactive_params: tuple[str, ...] = ()   # which params get interactive prompts

    # Presentation escape hatch (for batch, init wizard, serve)
    custom_presentation: bool = False              # registry skips auto-gen; action still registered
```

**Key invariant:** `custom_presentation=True` means Phases 3-4 generators skip this action. The action is still in the registry and therefore discoverable and hookable.

### Pattern 3: ActionRegistry Class

**What:** Module-level singleton collecting all ActionDefinitions. Validates uniqueness on registration. Provides lookup and filtering. The `get_action_registry()` accessor mirrors `get_note_type_registry()` exactly.

```python
# Source: domain/registry.py NoteTypeRegistry — same structural pattern

class ActionRegistry:
    """Registry of all ActionDefinitions (built-in + plugin-contributed).

    Thread safety: registrations happen at module-load time only.
    """

    def __init__(self) -> None:
        self._actions: dict[str, ActionDefinition] = {}

    def register(self, action: ActionDefinition) -> None:
        """Register an ActionDefinition. Raises ValueError on name collision."""
        if action.name in self._actions:
            raise ValueError(f"Action {action.name!r} is already registered")
        self._actions[action.name] = action

    def get(self, name: str) -> ActionDefinition:
        """Return ActionDefinition by name. Raises KeyError if not found."""
        try:
            return self._actions[name]
        except KeyError:
            raise KeyError(f"No action registered for name={name!r}") from None

    def list_actions(
        self,
        *,
        category: str | None = None,
        side_effect: Literal["read", "write"] | None = None,
        custom_presentation: bool | None = None,
    ) -> list[ActionDefinition]:
        """Return filtered list of registered actions."""
        actions = list(self._actions.values())
        if category is not None:
            actions = [a for a in actions if a.category == category]
        if side_effect is not None:
            actions = [a for a in actions if a.side_effect == side_effect]
        if custom_presentation is not None:
            actions = [a for a in actions if a.custom_presentation == custom_presentation]
        return actions


_REGISTRY = ActionRegistry()


def get_action_registry() -> ActionRegistry:
    """Return the module-level ActionRegistry singleton."""
    return _REGISTRY
```

### Pattern 4: BaseController

**What:** Abstract base for all controllers. Mirrors BaseService structure (`__init__(vault)`, `_vault` attribute). Adds `_dispatch_event()` (event dispatch responsibility moves from services to controllers per CONTEXT.md decision area).

```python
# Source: services/base.py — direct structural mirror
# Event dispatch decision area noted in CONTEXT.md

class BaseController:
    """Abstract base for all controller-layer classes.

    Controllers receive a Vault, orchestrate service calls, manage
    transaction boundaries, and dispatch lifecycle events.

    INVARIANT: All controller methods return ServiceResult.
    INVARIANT: Plugin failures are warnings, never errors.
    """

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    def _dispatch_event(
        self,
        hook_name: str,
        payload: dict[str, Any],
        warnings: list[str],
        *,
        session_id: str | None = None,
    ) -> int | None:
        """Dispatch a lifecycle event. No-op if event bus not initialized."""
        # Same implementation as BaseService._dispatch_event()
        ...
```

**Design decision — event dispatch location:** The CONTEXT.md lists event dispatch location as "Claude's Discretion." Based on the architectural goal (controllers own orchestration), events should fire from controllers. However, services currently call `_dispatch_event()` internally (via `BaseService`). The migration path is: (1) controllers call `_dispatch_event()` after the service call completes, (2) the service no longer calls it. This means removing `_dispatch_event()` from services is part of the service refactoring. BaseService can retain the method temporarily during migration but it should not be called — a deprecation comment is sufficient.

### Pattern 5: Handler Binding via Lazy Service Construction

**What:** Controller methods use lazy local imports (matching existing convention) and construct services per-call. They do NOT hold service references as instance variables.

```python
# Source: mcp/tools.py _impl pattern — formalized into controllers
# Existing precedents: session.py, context.py, upgrade.py lazy imports

class CreateController(BaseController):
    @traced
    def create_note(
        self,
        title: str,
        *,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        body: str | None = None,
        links: dict[str, list[str]] | None = None,
        aliases: list[str] | None = None,
    ) -> ServiceResult:
        """Create a new note."""
        from ztlctl.services.create import CreateService  # lazy import — established pattern
        result = CreateService(self._vault).create_note(
            title, subtype=subtype, tags=tags, topic=topic,
            body=body, links=links, aliases=aliases,
        )
        # Event dispatch moves here from CreateService (pending migration)
        return result
```

**Why lazy imports:** Six established precedents in `session.py`, `context.py`, `upgrade.py`. Controllers importing services directly at module level would create cross-layer circular dependency risk.

### Pattern 6: Core Registration Module

**What:** `actions/_register_core.py` is the single file that instantiates all built-in ActionDefinitions and calls `get_action_registry().register(...)`. Called at module-load time by `actions/__init__.py`. Mirrors `_register_builtins()` in `domain/registry.py`.

```python
# Source: domain/registry.py _register_builtins() pattern

def _register_core_actions() -> None:
    """Register all built-in ActionDefinitions into the singleton registry."""
    registry = get_action_registry()

    # --- creation category ---
    registry.register(ActionDefinition(
        name="create_note",
        description="Create a new note in the vault",
        category="creation",
        params=(
            ActionParam("title", str, required=True, description="Note title"),
            ActionParam("subtype", str, required=False, default=None,
                       description="Note subtype (knowledge, decision)"),
            ActionParam("tags", list, required=False, default=None,
                       cli_multiple=True, description="Tags to apply"),
            # ... remaining params
        ),
        handler=CreateController(None).create_note,  # handler replaced at dispatch time
        side_effect="write",
        mcp_when_to_use="When capturing a new idea, insight, or concept",
        cli_group="create",
    ))
    # ... remaining 44+ actions
```

**Note on handler binding:** The `handler` field stores a bound method reference. At registration time, `CreateController(None)` is a placeholder — the actual controller is constructed with the real `Vault` at dispatch time by the CLI/MCP generator layers. Alternative: store a callable factory `lambda vault: CreateController(vault).create_note` — the generators decide which pattern serves them better. This is a discretion area; research recommends the factory lambda approach for clarity.

### Pattern 7: Controller Granularity — 1-to-1 Service Mapping

**Recommendation:** Each existing service becomes one controller. This is the lowest-risk migration path because the existing service boundaries already reflect domain cohesion.

| Existing Service | New Controller | Public Methods |
|-----------------|---------------|----------------|
| `CreateService` | `CreateController` | `create_note`, `create_reference`, `create_task`, `create_log`, `create_batch` |
| `QueryService` | `QueryController` | `search`, `get`, `list_items`, `work_queue`, `list_tags`, `decision_support`, `topic_packet`, `draft_from_topic`, `vault_review`, `count_items` |
| `GraphService` | `GraphController` | `related`, `themes`, `rank`, `path`, `gaps`, `bridges`, `unlink`, `materialize_metrics` |
| `UpdateService` | `UpdateController` | `update`, `archive`, `supersede` |
| `ReweaveService` | `ReweaveController` | `reweave`, `prune`, `undo` |
| `SessionService` | `SessionController` | `start`, `close`, `reopen`, `status`, `log_entry`, `cost`, `context`, `brief`, `extract_decision` |
| `CheckService` | `CheckController` | `check`, `fix`, `rebuild`, `rollback` |
| `IngestService` | `IngestController` | `list_providers`, `ingest_text`, `ingest_file`, `ingest_url` |
| `ExportService` | `ExportController` | `export_markdown`, `export_indexes`, `export_graph`, `export_dashboard` |
| `VectorService` | `VectorController` | `reindex_all` (other methods are internal helpers) |
| `WorkflowService` | `WorkflowController` | `init_workflow`, `update_workflow`, `export_assets`, `validate_assets` — `custom_presentation=True` |
| `InitService` | `InitController` | `init_vault`, `regenerate_self`, `check_staleness` — `custom_presentation=True` |
| `UpgradeService` | `UpgradeController` | `check_pending`, `apply`, `stamp_current` |

Total: ~50 public controller methods → ~50 ActionDefinitions.

### Pattern 8: Migration Strategy — Service-by-Service

**Recommendation:** Port one service-to-controller pair at a time, not a big-bang rewrite.

**Order by risk (lowest first):**
1. `CheckService` → `CheckController`: no write pipeline, no event dispatch currently, isolated functionality
2. `UpgradeService` → `UpgradeController`: same rationale
3. `ExportService` → `ExportController`: read-heavy, no events
4. `GraphService` → `GraphController`: read-heavy algorithms
5. `ReweaveService` → `ReweaveController`: events present, moderate complexity
6. `UpdateService` → `UpdateController`: write pipeline, events
7. `QueryService` → `QueryController`: complex but no side effects
8. `CreateService` → `CreateController`: most critical path, save for late
9. `SessionService` → `SessionController`: highest orchestration complexity, last

**After each service migration:**
- Register its ActionDefinitions in `_register_core.py`
- Write `tests/actions/test_registry.py` assertions for the new definitions
- Write `tests/controllers/test_<name>.py` coverage
- Verify `uv run pytest` green before moving to the next service

### Anti-Patterns to Avoid

- **Direct service import in commands/mcp after Phase 2**: Every operation must route through a controller. Scan for `from ztlctl.services.* import *Service` in `commands/` and `mcp/` — these are violations by Phase 2 end. The CLI and MCP hand-written code continues to work but must call controllers, not services directly.
- **ActionDefinition carrying >50 lines**: If a single action registration block exceeds 50 lines, the metadata is too heavy. Split optional annotations into a separate layer.
- **ActionRegistry discovering actions automatically**: The registry is passive — core startup code explicitly registers. Never have services or controllers self-register.
- **Circular imports between controllers/ and services/**: Controllers import services via lazy local imports (inside methods). Never at module level.
- **Event dispatch in services after Phase 2**: Once a service is migrated to a controller, the service must not call `_dispatch_event()`. The controller owns dispatch.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frozen dataclass for definitions | Custom `__init__` / `__hash__` / `__eq__` | `@dataclass(frozen=True)` | Stdlib; already used by `NoteTypeDefinition`; provides `__hash__` for free |
| Registry singleton | Module-level dict | `_REGISTRY = ActionRegistry()` + `get_action_registry()` | Same pattern as `get_note_type_registry()`; proven stable |
| Type validation at registration | Hand-rolled `isinstance` chains | `ValueError` on name collision + transition validation | Mirror `NoteTypeRegistry._validate_transitions()` — simple and sufficient |
| Per-invocation service construction | Service factory classes | Lazy import inside method + `ServiceClass(vault).method()` | 6 existing precedents in session.py, context.py, upgrade.py |
| ServiceResult union types | Custom result types | `ServiceResult(ok=False, error=ServiceError(...))` | Universal return type — never change this contract |

**Key insight:** The `_impl` functions in `mcp/tools.py` are already 90% of the controller pattern. The controller refactoring is renaming them, moving them to `controllers/`, and grouping them under `BaseController`.

---

## Common Pitfalls

### Pitfall 1: ActionDefinition Becomes a God Object (CRITICAL)

**What goes wrong:** Adding CLI metadata, MCP metadata, event hooks, telemetry spans, and permissions to a single `ActionDefinition` dataclass produces a 200-field monster.

**Why it happens:** The existing ToolCatalogEntry has ~8 fields; Click commands have ~20 lines of decorators; combining these into one dataclass with all edge cases leads to field explosion.

**How to avoid:** Complexity budget of 50 lines per action definition. Core identity fields (name, description, category, params, handler, side_effect) are the required set. CLI/MCP metadata fields are optional string fields that default to empty. If a field is needed by only 1-2 actions, it may be a sign the abstraction is wrong.

**Warning signs:** Defining `create_note` takes more than 30 lines. Changing a CLI help string requires touching the same dict structure as an MCP catalog entry.

### Pitfall 2: Broken CLI/MCP During Migration (CRITICAL)

**What goes wrong:** Refactoring services to controllers breaks existing `commands/` and `mcp/` code that imports services directly.

**Why it happens:** Commands currently do `from ztlctl.services.create import CreateService`. If CreateService's public API changes during refactoring, all consumers break.

**How to avoid:** Services MUST NOT change their public API during this phase. Controllers wrap services — services are not changed. The existing service method signatures are the contract. The CLI/MCP hand-written code continues importing services directly UNTIL it is replaced in Phases 3-4. Alternatively, commands can import from controllers — but this is optional for Phase 2.

**Warning signs:** Any existing test failure in `tests/commands/` or `tests/mcp/` that was passing before the refactor.

### Pitfall 3: Handler Binding Type Safety

**What goes wrong:** `handler: Callable[..., ServiceResult]` accepts anything. Calling `registry.get("create_note").handler(vault=vault, title="x")` requires kwargs matching the controller method signature, but nothing enforces this at registration time.

**How to avoid:** The ActionParam list IS the spec — generators use it to construct calls, not raw kwargs. Write a test that each registered ActionDefinition's params match its handler's signature using Python's `inspect.signature()`.

**Warning signs:** A registered action handler has required params not declared in `ActionDefinition.params`, or vice versa.

### Pitfall 4: Event Dispatch Double-Fire During Migration

**What goes wrong:** Services still call `_dispatch_event()` internally. After the controller wrapping them also calls `_dispatch_event()`, lifecycle events fire twice per operation.

**How to avoid:** When a service is migrated to a controller, immediately remove the `_dispatch_event()` call from the service. Add a comment: `# INVARIANT: Event dispatch moved to {ControllerClass}. Do not add dispatch calls here.` This is the most common migration bug — add an integration test checking event count per operation.

**Warning signs:** EventBus WAL has duplicate entries for the same operation. `_impl` test assertions on event counts fail.

### Pitfall 5: `_register_core.py` Import Ordering

**What goes wrong:** `_register_core.py` imports controller classes to instantiate handlers. Controllers import services lazily. But if any controller's module-level code triggers a heavy import, the registry initialization becomes slow or fails.

**How to avoid:** Keep all service imports inside controller methods (lazy local imports). `_register_core.py` imports only controller module-level symbols (class names), never service module-level symbols.

**Warning signs:** `import ztlctl.actions` takes more than 100ms. Import profiling with `python -X importtime` shows unexpected service imports at registry load time.

---

## Code Examples

### Verified Pattern: NoteTypeDefinition as Template (from source)

The ActionDefinition structure mirrors this exactly:

```python
# Source: src/ztlctl/domain/registry.py (verified — current codebase)

@dataclass(frozen=True)
class NoteTypeDefinition:
    name: str
    content_type: str
    model_cls: type[ContentModel]
    transitions: dict[str, list[str]]
    template_name: str
    required_sections: list[str] = field(default_factory=list)
    initial_status: str = ""
    is_subtype: bool = False
    parent_type: str | None = None
```

**Key observation:** The `field(default_factory=list)` pattern is used for mutable defaults. ActionDefinition uses `tuple[ActionParam, ...]` (immutable) so no `field(default_factory=...)` is needed for `params`.

### Verified Pattern: _impl as Proto-Controller (from source)

```python
# Source: src/ztlctl/mcp/tools.py (verified — current codebase, line ~708)

def create_note_impl(
    vault: Any,
    title: str,
    *,
    subtype: str | None = None,
    tags: list[str] | None = None,
    topic: str | None = None,
    body: str | None = None,
    key_points: list[str] | None = None,
    links: dict[str, list[str]] | None = None,
    aliases: list[str] | None = None,
) -> dict[str, Any]:
    """Create a new note."""
    from ztlctl.services.create import CreateService

    result = CreateService(vault).create_note(
        title, subtype=subtype, tags=tags, topic=topic,
        body=body, key_points=key_points, links=links, aliases=aliases,
    )
    return _to_mcp_response(result)
```

The controller version of this is structurally identical but: (a) returns `ServiceResult` not `dict[str, Any]`, (b) is a method on `CreateController(BaseController)`, (c) carries the `@traced` decorator.

### Verified Pattern: Registry Singleton (from source)

```python
# Source: src/ztlctl/domain/registry.py (verified — current codebase, line ~295)

_REGISTRY = NoteTypeRegistry()
_register_builtins()

def get_note_type_registry() -> NoteTypeRegistry:
    """Return the module-level NoteTypeRegistry singleton."""
    return _REGISTRY
```

The ActionRegistry follows the identical pattern: `_REGISTRY = ActionRegistry()` at module level, `_register_core_actions()` called immediately, `get_action_registry()` accessor function.

### Verified Pattern: Test Structure for Registry (from source)

```python
# Source: tests/domain/test_registry.py (verified — current test suite)

class TestNoteTypeRegistry:
    def test_register_and_get(self) -> None:
        registry = NoteTypeRegistry()  # fresh instance, not singleton
        registry.register(NoteTypeDefinition(name="custom", ...))
        result = registry.get("custom")
        assert result.name == "custom"

    def test_duplicate_raises(self) -> None:
        registry = NoteTypeRegistry()
        registry.register(NoteTypeDefinition(name="x", ...))
        with pytest.raises(ValueError, match="already registered"):
            registry.register(NoteTypeDefinition(name="x", ...))
```

ActionRegistry tests use the same pattern: instantiate fresh `ActionRegistry()` (not singleton) for isolation.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact for Phase 2 |
|--------------|------------------|--------------|-------------------|
| Services own transaction mgmt + dispatch | Controllers own transaction mgmt + dispatch; services = pure domain logic | Phase 2 (this phase) | Services become thinner; controllers absorb `with self._vault.transaction()` calls |
| CLI/MCP import services directly | CLI/MCP import controllers; services not imported outside controllers | Phase 2 (enforced) / Phases 3-4 (generated) | Commands/MCP can still import services in Phase 2 — enforced in Phases 3-4 |
| `_impl` functions in `mcp/tools.py` as MCP-only | Controller methods in `controllers/` as universal handlers | Phase 2 | ~30 `_impl` functions get formalized counterparts; `_impl` functions become thin wrappers |
| 45+ service methods described only in code | 45+ `ActionDefinition` objects in registry with typed params, category, side_effect, metadata | Phase 2 | Enables registry lookup, introspection, plugin extension |

**Deprecated/outdated after Phase 2:**
- Direct service imports in `commands/` (allowed during Phase 2, replaced in Phase 4)
- `_impl` functions calling service methods directly (replaced by calling controllers; `_impl` becomes `ControllerClass(vault).method(...)`)

---

## Open Questions

1. **Handler binding mechanism: method reference vs lambda factory**
   - What we know: `ActionDefinition.handler` is `Callable[..., ServiceResult]`. The generators in Phases 3-4 need to call the handler with a Vault + params.
   - What's unclear: Should `handler` store a bound method reference (requires a dummy controller at registration time) or a lambda/factory `lambda vault, **kw: CreateController(vault).create_note(**kw)`?
   - Recommendation: Use the factory lambda approach. It avoids constructing dummy controllers at registration time and is explicit about the Vault injection. Planner should decide the convention and apply it consistently in `_register_core.py`.

2. **`@traced` on controller methods**
   - What we know: `@traced` is currently applied to 45 service methods. Controllers will wrap these. If controllers also carry `@traced`, spans will double-wrap (root controller span containing root service span).
   - What's unclear: Should controllers carry `@traced` or rely on service-level spans only?
   - Recommendation: Remove `@traced` from services that get migrated (service becomes pure logic without tracing). Controllers carry `@traced`. This is cleaner but adds migration work. Alternatively, keep service spans and do not add `@traced` to controllers — simpler migration.

3. **`create_batch` controller granularity**
   - What we know: `create_batch` in CreateService is a complex multi-content operation with `_BatchAbort` rollback logic. It does not map cleanly to a simple controller delegation.
   - What's unclear: Should `CreateController.create_batch` register with `custom_presentation=True` or as a normal action with reduced params?
   - Recommendation: Register with `custom_presentation=True` since batch input format (list of items) cannot be expressed in a flat ActionParam list. Still gets an ActionDefinition; generators skip auto-generation.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/actions/ tests/controllers/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACTN-01 | ActionParam fields, defaults, frozen immutability | unit | `uv run pytest tests/actions/test_definitions.py -x` | ❌ Wave 0 |
| ACTN-01 | ActionDefinition fields, defaults, frozen immutability | unit | `uv run pytest tests/actions/test_definitions.py -x` | ❌ Wave 0 |
| ACTN-01 | ActionDefinition carries CLI metadata (cli_group, cli_interactive_params) | unit | `uv run pytest tests/actions/test_definitions.py::test_cli_metadata -x` | ❌ Wave 0 |
| ACTN-01 | ActionDefinition carries MCP metadata (mcp_when_to_use, mcp_avoid_when, mcp_common_errors) | unit | `uv run pytest tests/actions/test_definitions.py::test_mcp_metadata -x` | ❌ Wave 0 |
| ACTN-02 | ActionRegistry register/get/list_actions | unit | `uv run pytest tests/actions/test_registry.py -x` | ❌ Wave 0 |
| ACTN-02 | ActionRegistry rejects duplicate names | unit | `uv run pytest tests/actions/test_registry.py::test_duplicate_raises -x` | ❌ Wave 0 |
| ACTN-02 | All 45+ core operations registered in singleton | integration | `uv run pytest tests/actions/test_registry.py::test_core_registrations -x` | ❌ Wave 0 |
| ACTN-02 | Registry lookup by name returns correct ActionDefinition | unit | `uv run pytest tests/actions/test_registry.py::test_get -x` | ❌ Wave 0 |
| ACTN-02 | Registry filtering by category and side_effect | unit | `uv run pytest tests/actions/test_registry.py::test_list_actions -x` | ❌ Wave 0 |
| ACTN-01+02 | Each registered action's handler params match ActionDefinition.params | integration | `uv run pytest tests/actions/test_registry.py::test_handler_signature_parity -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/actions/ tests/controllers/ -x -q`
- **Per wave merge:** `uv run pytest` (full 1256+ test suite)
- **Phase gate:** Full suite green + `uv run mypy src/` strict + `uv run ruff check .` before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/actions/__init__.py` — package init
- [ ] `tests/actions/test_definitions.py` — ActionParam + ActionDefinition unit tests
- [ ] `tests/actions/test_registry.py` — ActionRegistry unit + integration tests
- [ ] `tests/controllers/__init__.py` — package init
- [ ] `tests/controllers/test_base.py` — BaseController unit tests
- [ ] `tests/controllers/test_create.py` — CreateController integration tests (require vault fixture)
- [ ] `tests/controllers/test_check.py` — CheckController integration tests
- [ ] Framework: already installed — pytest 8.3+ confirmed in pyproject.toml

---

## Sources

### Primary (HIGH confidence)
- `src/ztlctl/domain/registry.py` — NoteTypeDefinition/NoteTypeRegistry direct template; verified 2026-03-19
- `src/ztlctl/mcp/tools.py` — 30 `_impl` proto-controller functions; ToolCatalogEntry TypedDict; verified 2026-03-19
- `src/ztlctl/services/base.py` — BaseService pattern; `_dispatch_event()` implementation; verified 2026-03-19
- `src/ztlctl/services/create.py`, `query.py`, `graph.py`, `update.py`, `reweave.py`, `session.py`, `check.py`, `ingest.py`, `export.py`, `vector.py`, `workflow.py`, `upgrade.py` — public method inventory; verified 2026-03-19
- `.planning/research/ARCHITECTURE.md` — ActionDefinition/ActionRegistry design; build order rationale; verified 2026-03-19
- `.planning/research/PITFALLS.md` — Pitfall 4 (god object), Pitfall 2 (parity regression); verified 2026-03-19
- `.planning/codebase/ARCHITECTURE.md` — 6-layer architecture, data flow, BaseService pattern; verified 2026-03-19
- `.planning/codebase/CONVENTIONS.md` — lazy import pattern, naming conventions, `@dataclass(frozen=True)` usage; verified 2026-03-19
- `tests/domain/test_registry.py` — registry test structure to mirror; verified 2026-03-19

### Secondary (MEDIUM confidence)
- `.planning/research/SUMMARY.md` — phase ordering rationale; Phase 2 scope definition; verified 2026-03-19

### Tertiary (LOW confidence)
- None for this phase — all findings grounded in current codebase analysis

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies; existing stdlib dataclasses pattern confirmed in codebase
- Architecture: HIGH — ActionDefinition/ActionRegistry design validated against existing NoteTypeDefinition pattern; all 45+ service methods quantified from source
- Controller granularity: HIGH — 1-to-1 service mapping confirmed as lowest-risk migration strategy; all services enumerated
- Pitfalls: HIGH — all pitfalls grounded in specific existing code (ToolCatalogEntry, _impl, _dispatch_event, BaseService) rather than generic warnings
- Migration order: MEDIUM — order is sensible but the actual migration complexity of CreateService vs SessionService may differ from the risk ranking

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable Python patterns; only invalidated if major service refactoring occurs before planning)
