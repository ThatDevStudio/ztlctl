# Phase 5: Plugin Formalization - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning
**Source:** Auto-selected defaults (--auto flag)

<domain>
## Phase Boundary

Publish a stable, versioned plugin API. Third-party plugin authors can register custom note types (with custom lifecycles that automatically gain CLI commands and MCP tools), pre-action hooks (modify inputs or abort actions), and configuration (validated against plugin-declared schemas). Built-in GitPlugin and ReweavePlugin are ported to the new hookspecs to validate the API before marking it stable. Plugin marketplace metadata convention established for future discoverability. This phase does NOT add agent orchestration, progressive tool disclosure, or security hardening — those are Phase 6.

</domain>

<decisions>
## Implementation Decisions

### Plugin API versioning (PLUG-01)
- **Integer PLUGIN_API_VERSION constant** — plugins declare a target version, host validates compatibility at load time. Incompatible plugins are rejected with clear error messages.
- **@deprecated decorator** — warns for N versions before removal. Provides version-specific deprecation messages so plugin authors know exactly what to change.
- **Backward compatibility window** — 2 versions minimum before breaking changes. Plugin load emits warnings for deprecated hookspecs, errors for removed ones.

### Pre-action hooks (PLUG-02)
- **pluggy firstresult pattern** — synchronous dispatch before controller execution. Hooks receive the action name and kwargs.
- **Hooks can modify inputs or abort** — return modified kwargs to change inputs, return a rejection object to abort the action before execution. No modification = pass-through.
- **Fire in controller layer** — pre-hooks dispatch before the handler executes, post-hooks dispatch after. This aligns with the Phase 2 architecture: controllers orchestrate, services are pure logic.

### Plugin configuration (PLUG-03)
- **`[plugins.<name>]` in ztlctl.toml** — plugin config lives alongside vault config. Passed to plugins during initialization.
- **Pydantic schema validation** — plugins declare a Pydantic model for their config. Host validates at load time and passes the validated model to the plugin. Invalid config produces clear errors.

### Custom note types (PLUG-05, PLUG-06)
- **Plugins register NoteTypeDefinitions** — custom note types use the same NoteTypeDefinition primitive from Phase 1. Registration into ActionRegistry means they automatically gain CLI commands (via Phase 4 generator) and MCP tools (via Phase 3 generator). Define-once, use-everywhere.
- **Render contribution contracts** — plugins provide Rich CLI output format and MCP response format for their custom note types. A `RenderContribution` dataclass or protocol defines the interface.

### Marketplace metadata (PLUG-07)
- **`[tool.ztlctl-plugin]` in pyproject.toml** — structured metadata (name, version, author, capabilities, compatibility, target API version) for future discoverability. Convention-based, not enforced at load time.

### Built-in plugin migration (validation)
- **Port GitPlugin and ReweavePlugin to new hookspecs** — existing built-in plugins serve as the acid test for the new API. Both must work identically after porting. ObsidianPlugin stays as-is (init-only, not lifecycle-driven).
- **New hookspec: `pre_action` / `post_action`** — replaces the current per-event hookspecs (post_create, post_update, etc.) with a generic action-based pattern. Existing per-event hookspecs become convenience aliases that delegate to the generic hooks.

### Claude's Discretion
- **Hook dispatch implementation details** — exact pluggy configuration for firstresult, whether to use pluggy's `tryfirst`/`trylast` ordering.
- **NoteTypeDefinition registration flow** — how plugins register NoteTypeDefinitions (hookspec, decorator, or direct registry call) and when registration happens relative to ActionDefinition registration.
- **Render contribution protocol** — exact interface shape for Rich and MCP rendering contracts. Whether it's a Protocol, ABC, or dataclass.
- **Config schema declaration** — how plugins expose their Pydantic config model (class attribute, hookspec return, or registration call).
- **Hookspec migration strategy** — whether to deprecate old per-event hookspecs immediately or keep them as aliases for the transition period.
- **Source provider registration** — how `register_source_providers` hookspec relates to the new action-based model (source providers may not map cleanly to ActionDefinitions).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current plugin system
- `src/ztlctl/plugins/hookspecs.py` — 16 hookspecs: 8 lifecycle events (post_create, post_update, etc.) + 8 registration hooks (register_content_models, register_cli_commands, etc.)
- `src/ztlctl/plugins/manager.py` — PluginManager: pluggy-based discovery (entry points + local dir), registration, hook dispatch
- `src/ztlctl/plugins/contracts.py` — Typed contribution dataclasses (CliCommandContribution, McpToolContribution, etc.)
- `src/ztlctl/plugins/event_bus.py` — WAL-backed async event dispatch with sync mode

### Built-in plugins (porting targets)
- `src/ztlctl/plugins/builtins/git.py` — GitPlugin: implements 8 lifecycle hookspecs (post_create, post_update, etc.)
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — ReweavePlugin: post_create reweave trigger
- `src/ztlctl/plugins/builtins/obsidian.py` — ObsidianPlugin: init-only, not lifecycle-driven

### ActionRegistry (integration target)
- `src/ztlctl/actions/definitions.py` — ActionDefinition with handler, params, side_effect
- `src/ztlctl/actions/registry.py` — ActionRegistry singleton
- `src/ztlctl/actions/_register_core.py` — 59 built-in registrations

### Generators (auto-surface for plugin types)
- `src/ztlctl/mcp/generator.py` — MCP tool generator from ActionRegistry
- `src/ztlctl/commands/generator.py` — CLI command generator from ActionRegistry

### Domain model
- `src/ztlctl/domain/registry.py` — NoteTypeDefinition + NoteTypeRegistry (Phase 1)
- `src/ztlctl/domain/content.py` — ContentModel + CONTENT_REGISTRY
- `src/ztlctl/config/settings.py` — ZtlSettings Pydantic model (config patterns)

### Requirements
- `.planning/REQUIREMENTS.md` — PLUG-01 through PLUG-07

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `NoteTypeDefinition` + `NoteTypeRegistry` (Phase 1): Custom note types register into this — existing infrastructure
- `ActionRegistry.register()`: Plugins can register ActionDefinitions for their custom types — both generators will pick them up automatically
- `PluginManager._pm` (pluggy): Already configured for hookspec-based dispatch
- `ZtlSettings` (Pydantic): Config validation pattern to follow for plugin config schemas
- `contracts.py` contribution dataclasses: Existing pattern for typed plugin contributions

### Established Patterns
- **pluggy hookspec markers**: `@hookspec` decorator on ZtlctlHookSpec methods
- **Entry-point discovery**: `ztlctl.plugins` entry_point group + local dir scanning
- **Contribution collection**: `PluginManager.cli_command_contributions()`, `mcp_tool_contributions()`, etc.
- **Frozen dataclasses for contracts**: All contribution types are `@dataclass(frozen=True)`
- **BaseService._dispatch_event()**: Currently fires per-event hookspecs (post_create, etc.)

### Integration Points
- `BaseService._dispatch_event()`: Where lifecycle hooks fire — will add pre-action dispatch
- `ActionRegistry`: Where plugin-contributed ActionDefinitions register
- `NoteTypeRegistry`: Where plugin-contributed NoteTypeDefinitions register
- `commands/__init__.py`: CLI command registration — generators already iterate ActionRegistry
- `mcp/generator.py`: MCP tool registration — generators already iterate ActionRegistry
- `config/settings.py`: Where `[plugins.<name>]` config sections would be parsed

</code_context>

<specifics>
## Specific Ideas

- The define-once pipeline from Phases 2-4 means plugin note types that register a NoteTypeDefinition + ActionDefinitions automatically get CLI commands and MCP tools. This is the payoff of the 4-layer architecture.
- GitPlugin currently implements 8 separate hookspecs (post_create, post_update, etc.). The new `pre_action`/`post_action` generic hooks should let it register once with action-name filtering instead of 8 separate methods.
- ReweavePlugin's post_create hook is a good test case for pre/post action hooks — it triggers reweave after note creation, which maps directly to `post_action(action_name="create_note", ...)`.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-plugin-formalization*
*Context gathered: 2026-03-20 via --auto defaults*
