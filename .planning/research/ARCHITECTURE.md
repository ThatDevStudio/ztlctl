# Architecture Patterns

**Domain:** Plugin-extensible CLI/MCP tool with unified action registry
**Researched:** 2026-03-19

## Recommended Architecture

The v2 architecture introduces a **single new layer** -- the **Action Registry** -- between the existing service layer and the existing presentation layers (CLI commands, MCP tools). This registry is the "define once" source of truth. CLI and MCP become thin, auto-generated adapters over it.

### High-Level Structure

```
                          ┌─────────────┐
                          │   Plugins   │
                          │  (extend)   │
                          └──────┬──────┘
                                 │ registers
                                 v
┌──────────┐  generates   ┌──────────────┐  generates   ┌──────────┐
│  Click   │<─────────────│    Action    │─────────────>│   MCP    │
│   CLI    │              │   Registry   │              │  Tools   │
└────┬─────┘              └──────┬───────┘              └────┬─────┘
     │                           │                           │
     │        ┌──────────────────┘                           │
     │        │ dispatches                                   │
     v        v                                              v
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
│  (CreateService, QueryService, GraphService, ... unchanged)     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                          ┌────v────┐
                          │  Vault  │
                          └─────────┘
```

**Key insight:** The service layer does NOT change. Services remain the business logic owners. The Action Registry sits above services, defining what operations exist and their parameter schemas. CLI and MCP are generated from those definitions.

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **ActionDefinition** | Declares one operation: name, parameters (typed), service method binding, metadata (category, side effects, description) | Registry (registered into), CLI generator, MCP generator |
| **ActionRegistry** | Collects ActionDefinitions from core + plugins. Single source of truth for all operations | ActionDefinitions, CLI generator, MCP generator, Plugin system |
| **CLI Generator** | Reads ActionRegistry, produces Click commands with proper types, options, help text. Handles CLI-specific concerns (interactive prompts, output formatting) | ActionRegistry, AppContext, Output layer |
| **MCP Generator** | Reads ActionRegistry, produces FastMCP tool registrations with proper schemas and catalog entries | ActionRegistry, FastMCP server, Vault |
| **NoteTypeRegistry** | Collects ContentModel subclasses + lifecycle transition maps. Extensible by plugins | ContentModel hierarchy, lifecycle maps, ActionRegistry (for type-aware actions) |
| **EventBus** (existing) | Async event dispatch for lifecycle hooks | Services (dispatch), Plugins (subscribe) |
| **PluginManager** (existing, extended) | Discovers and loads plugins. Plugins contribute: ActionDefinitions, NoteTypes, templates, hooks | ActionRegistry, NoteTypeRegistry, EventBus |

### Data Flow

**Startup (one-time):**

```
1. PluginManager discovers and loads plugins (entry-points + local)
2. Core registers built-in ActionDefinitions into ActionRegistry
3. Plugins register additional ActionDefinitions via hookspec
4. Core registers built-in NoteTypes into NoteTypeRegistry
5. Plugins register additional NoteTypes via hookspec
6. CLI Generator reads ActionRegistry -> produces Click command tree
7. MCP Generator reads ActionRegistry -> produces FastMCP tool registrations
```

**Runtime (per-invocation, CLI path):**

```
1. User runs `ztlctl <action> <args>`
2. Click dispatches to generated command handler
3. Handler applies CLI-specific transforms (interactive prompts, tuple->list)
4. Handler calls the ActionDefinition's bound service method
5. Service returns ServiceResult
6. Handler calls AppContext.emit(result) for output formatting
```

**Runtime (per-invocation, MCP path):**

```
1. Agent calls MCP tool with JSON params
2. FastMCP validates against auto-generated input schema
3. Generated handler calls the ActionDefinition's bound service method
4. Service returns ServiceResult
5. Handler converts to MCP response dict via _to_mcp_response()
```

## Core Design: ActionDefinition

This is the central abstraction. One definition produces both a CLI command and an MCP tool.

### Pattern: ActionDefinition as a Declarative Dataclass

```python
@dataclass(frozen=True)
class ActionParam:
    """One parameter of an action."""
    name: str
    type: type                          # Python type (str, int, bool, list[str])
    required: bool = True
    default: Any = None
    description: str = ""
    choices: list[str] | None = None    # for enums/constrained values
    cli_multiple: bool = False          # Click: --tags a --tags b
    cli_is_argument: bool = False       # Click: positional vs option

@dataclass(frozen=True)
class ActionDefinition:
    """One operation in the system."""
    name: str                           # e.g. "create_note"
    description: str                    # human-readable, used for both CLI help and MCP docs
    category: str                       # e.g. "creation", "query", "lifecycle"
    params: tuple[ActionParam, ...]
    handler: Callable[..., ServiceResult]  # bound to service method
    side_effect: Literal["read", "write"]

    # MCP-specific metadata (optional overrides)
    mcp_when_to_use: str = ""
    mcp_avoid_when: str = ""
    mcp_common_errors: tuple[str, ...] = ()

    # CLI-specific metadata (optional overrides)
    cli_group: str | None = None        # which Click group to attach to
    cli_examples: str = ""
    cli_interactive_params: tuple[str, ...] = ()  # params that prompt when interactive
```

**Why a dataclass, not a decorator:** Decorators are tempting but they couple definition to implementation. A dataclass can be constructed by core code or by plugins, serialized for introspection, and consumed by multiple generators. This is the same pattern used by the existing `ToolCatalogEntry` TypedDict, but formalized and typed.

### Pattern: ActionRegistry

```python
class ActionRegistry:
    """Singleton registry of all operations."""

    def register(self, action: ActionDefinition) -> None: ...
    def get(self, name: str) -> ActionDefinition: ...
    def list_actions(self, category: str | None = None) -> list[ActionDefinition]: ...
    def generate_click_commands(self) -> dict[str, click.Command]: ...
    def generate_mcp_tools(self, server: Any, vault: Any) -> None: ...
```

## Core Design: NoteType as Extensible Primitive

The existing `ContentModel` hierarchy and `CONTENT_REGISTRY` already support plugin-registered subtypes via `register_content_models()` hookspec. The v2 formalization wraps this into a first-class `NoteTypeDefinition` that bundles:

### Pattern: NoteTypeDefinition

```python
@dataclass(frozen=True)
class NoteTypeDefinition:
    """A formalized note type with its lifecycle and behavior."""
    name: str                                    # e.g. "decision", "knowledge"
    content_type: str                            # parent type: "note", "reference", "task"
    model_cls: type[ContentModel]                # Pydantic model for frontmatter
    transitions: dict[str, list[str]]            # status transition map
    template_name: str                           # Jinja2 body template
    required_sections: list[str] = field(default_factory=list)
    initial_status: str = ""                     # enforced on creation

    # Optional: auto-generate create/update actions
    auto_create_action: bool = True
    auto_update_action: bool = True
```

**Why formalize what already works:** The current system has content models, lifecycle maps, and template names spread across `content.py`, `lifecycle.py`, and template files. A `NoteTypeDefinition` bundles these into a single registrable unit that plugins can provide as one cohesive contribution -- model + lifecycle + template + action generation, all in one object.

### NoteTypeRegistry

```python
class NoteTypeRegistry:
    """Registry of all note types (built-in + plugin-contributed)."""

    def register(self, note_type: NoteTypeDefinition) -> None: ...
    def get(self, name: str) -> NoteTypeDefinition: ...
    def types_for(self, content_type: str) -> list[NoteTypeDefinition]: ...
    def generate_actions(self) -> list[ActionDefinition]: ...
```

The `generate_actions()` method is the bridge: for each registered note type with `auto_create_action=True`, it produces an `ActionDefinition` that knows how to call `CreateService.create_note(subtype=...)` with the right parameter schema. This is how a plugin that registers a new note type automatically gets both a CLI command and an MCP tool.

## Plugin Extension Points

### What Plugins Can Contribute (v2)

| Extension Point | Mechanism | Registration |
|----------------|-----------|--------------|
| **Custom note types** | `NoteTypeDefinition` | `register_note_types()` hookspec |
| **Custom actions** | `ActionDefinition` | `register_actions()` hookspec |
| **CLI commands** (legacy) | `CliCommandContribution` | `register_cli_commands()` hookspec (kept for escape hatch) |
| **MCP tools** (legacy) | `McpToolContribution` | `register_mcp_tools()` hookspec (kept for escape hatch) |
| **Templates** | Jinja2 template files | Template directory overlay |
| **Lifecycle hooks** | Pre/post event handlers | `post_create`, `post_update`, etc. hookspecs |
| **Source providers** | `SourceProviderContribution` | `register_source_providers()` hookspec |
| **Workflow modules** | `WorkflowModuleContribution` | `register_workflow_modules()` hookspec |

### Plugin Loading Sequence

```
1. PluginManager.discover_and_load()
   ├── Entry-point plugins (pkg metadata)
   └── Local plugins (<vault>/.ztlctl/plugins/)

2. NoteTypeRegistry collects:
   ├── Built-in: note, knowledge, decision, reference, task
   └── Plugin: pm.hook.register_note_types()

3. ActionRegistry collects:
   ├── Built-in core actions (hardcoded list)
   ├── Auto-generated from NoteTypeRegistry.generate_actions()
   └── Plugin: pm.hook.register_actions()

4. CLI Generator produces Click commands from ActionRegistry
5. MCP Generator produces FastMCP tools from ActionRegistry
```

## Patterns to Follow

### Pattern 1: Handler Binding via Lazy Service Construction

**What:** Action handlers should not hold service references. Instead, they receive a Vault and construct the service lazily (matching the existing `_impl` pattern in MCP tools).

**When:** Every action handler.

**Why:** Services are per-invocation. The Vault is the stable reference. This matches the existing convention where MCP `_impl` functions do `CreateService(vault).create_note(...)` inline.

```python
def _create_note_handler(vault: Any, **params: Any) -> ServiceResult:
    """Handler for the create_note action."""
    from ztlctl.services.create import CreateService
    return CreateService(vault).create_note(**params)
```

### Pattern 2: CLI-Specific Adapter Layer

**What:** The CLI generator wraps each action handler with CLI-specific concerns: interactive prompts, tuple-to-list conversion, `--session` flag, `--cost` tracking, output formatting via `AppContext.emit()`.

**When:** Generating Click commands from ActionDefinitions.

**Why:** CLI has concerns MCP does not: interactive prompts, TTY detection, progressive disclosure, exit codes. These should not leak into the action definition.

```python
def _build_click_command(action: ActionDefinition) -> click.Command:
    """Generate a Click command from an ActionDefinition."""
    # Convert ActionParams to Click options/arguments
    # Wrap handler with AppContext.emit() call
    # Add interactive prompt logic for cli_interactive_params
    ...
```

### Pattern 3: Schema-Driven MCP Registration

**What:** The MCP generator reads `ActionParam` types and produces FastMCP-compatible function signatures. It reuses the existing `ToolCatalogEntry` format for metadata.

**When:** Generating MCP tools from ActionDefinitions.

**Why:** FastMCP auto-generates input schemas from function signatures. The generator creates wrapper functions with correct type annotations, letting FastMCP's built-in schema generation handle the rest.

### Pattern 4: Presentation Escape Hatch

**What:** Keep the existing `register_cli_commands()` and `register_mcp_tools()` hookspecs as escape hatches for plugins that need full control over their CLI/MCP surface.

**When:** A plugin needs CLI behavior that cannot be expressed through ActionDefinition (e.g., custom Click types, multi-step interactive wizards, streaming output).

**Why:** The action registry handles 90% of cases. The escape hatch handles the remaining 10% without forcing every edge case through the abstraction.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Over-Abstracting the Service Layer

**What:** Trying to make services generic or driven by the action registry.

**Why bad:** Services contain nuanced business logic (6-stage create pipeline, 4-signal reweave scoring). Making them generic destroys the clear, testable implementations that v1 built carefully.

**Instead:** Keep services exactly as they are. The action registry is a thin declarative mapping layer on top, not a replacement for service logic.

### Anti-Pattern 2: Two-Way Binding Between Registry and Services

**What:** Having services register themselves into the action registry, or having the registry call into services to discover capabilities.

**Why bad:** Creates circular dependencies and makes the loading order fragile.

**Instead:** Core startup code explicitly registers actions. The registry is passive -- it collects definitions, it does not discover them.

### Anti-Pattern 3: Merging CLI and MCP Handlers

**What:** Having one handler function serve both CLI and MCP, with conditionals for presentation differences.

**Why bad:** CLI needs interactive prompts, output formatting, exit codes. MCP needs JSON schemas, catalog entries. Mixing these creates a handler that is neither clean CLI nor clean MCP.

**Instead:** One action definition, two generated handlers. Each handler adapts the action to its presentation context. The shared part is the service method call.

### Anti-Pattern 4: Plugin-Provided Lifecycle Maps Without Validation

**What:** Letting plugins register arbitrary status transition maps without checking for cycles, unreachable states, or conflicts.

**Why bad:** A malformed transition map can make notes permanently stuck in a status, or create cycles that break integrity checks.

**Instead:** The NoteTypeRegistry validates transition maps on registration: acyclic, all states reachable from initial, all terminal states are leaf nodes.

### Anti-Pattern 5: Action Registry as Event Bus

**What:** Using the action registry to dispatch events or trigger side effects.

**Why bad:** The EventBus already handles this well with WAL-backed async dispatch. Duplicating event semantics in the action registry creates two competing event systems.

**Instead:** Actions dispatch events through services (via `BaseService._dispatch_event()`). The action registry knows nothing about events.

## Scalability Considerations

| Concern | At 10 actions | At 50 actions | At 200+ actions (with plugins) |
|---------|---------------|---------------|-------------------------------|
| **Registry startup** | Negligible | Negligible | ~50ms for registration + CLI/MCP generation; acceptable for CLI cold start |
| **CLI help text** | Standard Click output | Need category grouping (already have ZtlGroup) | Plugin commands should be in separate groups to avoid overwhelming `--help` |
| **MCP tool list** | Trivial | Already have 29 tools in v1; `discover_tools` categorizes them | Need pagination or category filtering; existing `discover_tools` pattern handles this |
| **Action name conflicts** | Unlikely | Core names are reserved | Must enforce namespace prefixing for plugins (e.g., `myplugin.my_action`) |
| **Schema generation** | Instant | Instant | Profile if >100 actions; cache generated schemas |

## Suggested Build Order

Dependencies between components dictate a natural implementation sequence:

### Phase A: ActionDefinition + ActionRegistry (no generation yet)

- Define `ActionDefinition` and `ActionParam` dataclasses
- Implement `ActionRegistry` with `register()`, `get()`, `list_actions()`
- Register all existing core operations as ActionDefinitions
- **Test:** Registry can be populated and queried
- **No changes to CLI or MCP yet** -- this is pure infrastructure

### Phase B: NoteTypeDefinition + NoteTypeRegistry

- Define `NoteTypeDefinition` dataclass
- Implement `NoteTypeRegistry` with validation
- Migrate existing `CONTENT_REGISTRY` population to use `NoteTypeDefinition`
- Implement `generate_actions()` to auto-produce ActionDefinitions from note types
- **Test:** Plugin-registered note types produce correct ActionDefinitions
- **Depends on:** Phase A (produces ActionDefinitions)

### Phase C: MCP Generator (lower risk, fewer edge cases)

- Implement `ActionRegistry.generate_mcp_tools()`
- Replace hand-written `register_tools()` with generated tools
- Verify existing MCP tests pass with generated tools
- **Depends on:** Phase A
- **Why MCP before CLI:** MCP tools are simpler (no interactive prompts, no output formatting). Validating the generator against the simpler surface first reduces risk.

### Phase D: CLI Generator (higher complexity)

- Implement `ActionRegistry.generate_click_commands()`
- Handle interactive prompts, output formatting, CLI-specific types
- Replace hand-written command files with generated commands
- Keep escape-hatch commands (like `batch`) as hand-written
- **Depends on:** Phase A
- **Why last:** CLI has the most edge cases (interactive mode, progressive disclosure, `--json` flag). Solving MCP first validates the core pattern.

### Phase E: Plugin Integration

- Add `register_actions()` and `register_note_types()` hookspecs
- Plugins can now contribute full note types with auto-generated CLI/MCP
- Validate with a test plugin
- **Depends on:** Phases A-D

## Layer Dependency Map (v2)

```
commands (generated) ──> ActionRegistry ──> services ──> domain
                                │                         │
                                │                         v
mcp (generated) ───────────────>│              infrastructure
                                │                    │
                                v                    v
                         NoteTypeRegistry          Vault
                                │
                                v
                         PluginManager
                                │
                                v
                           EventBus
```

**New dependencies introduced:**
- ActionRegistry depends on: service method references (for handler binding), NoteTypeRegistry (for auto-generated actions)
- CLI Generator depends on: ActionRegistry, AppContext, Output layer
- MCP Generator depends on: ActionRegistry, FastMCP

**Dependencies removed:**
- CLI commands no longer import services directly (generated handlers do this)
- MCP tools no longer import services directly (generated handlers do this)
- No more duplicated parameter definitions between CLI and MCP

## Migration Strategy

The existing 29 MCP tools and 9+ CLI command files represent significant working code. Migration should be incremental, not big-bang:

1. **Parallel path:** New ActionDefinition-based commands coexist with existing hand-written commands during migration
2. **Feature parity tests:** For each migrated action, compare output of generated command vs. hand-written command
3. **Escape hatch preservation:** Commands that cannot be expressed as ActionDefinitions (batch, init, serve) remain hand-written

## Sources

- FastMCP tool registration: [FastMCP Tools Documentation](https://gofastmcp.com/servers/tools)
- MCP architecture: [MCP Architecture Overview](https://modelcontextprotocol.io/docs/learn/architecture)
- pluggy plugin system: [pluggy on PyPI](https://pypi.org/project/pluggy/)
- Click dynamic commands: [Real Python - Click CLI](https://realpython.com/python-click/)
- Existing ztlctl codebase analysis: `src/ztlctl/mcp/tools.py`, `src/ztlctl/commands/create.py`, `src/ztlctl/plugins/hookspecs.py`, `src/ztlctl/domain/content.py`

---

*Architecture research: 2026-03-19*
