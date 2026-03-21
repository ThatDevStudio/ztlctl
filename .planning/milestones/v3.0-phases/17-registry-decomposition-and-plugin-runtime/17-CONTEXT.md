# Phase 17: Registry Decomposition and Plugin Runtime - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Decompose the monolithic `_register_core.py` (2303 lines, 59+ ActionDefinitions) into feature-local registration modules. Centralize PluginManager construction so plugin/profile/workflow/init discovery uses a single coherent runtime owner instead of 4+ independent constructions. Fix `load_plugin_commands` to participate in config injection. Pure infrastructure — no user-facing command changes.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — pure infrastructure phase. Key constraints from prior phases:
- Feature-local modules should be colocated with relevant service/controller code (e.g., `actions/create.py`, `actions/query.py`)
- PluginManager is currently constructed independently in: `commands/__init__.py:35`, `services/init.py:158`, `workspace_profiles.py:162`, `services/workflow.py:200`, and `infrastructure/vault.py`
- `load_plugin_commands` currently creates its own PluginManager without `inject_configs` support (DEBT-07)
- The singleton ActionRegistry pattern (`get_action_registry()`) should inform the centralized plugin runtime design

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/ztlctl/actions/_register_core.py` — 2303-line monolith to decompose (59+ ActionDefinitions across 15 controller imports)
- `src/ztlctl/actions/registry.py` — singleton ActionRegistry with `get_action_registry()`
- `src/ztlctl/actions/definitions.py` — ActionDefinition and ActionParam models
- `src/ztlctl/plugins/manager.py` — PluginManager with `discover_and_load()`, `inject_configs()`, `cli_command_contributions()`

### Established Patterns
- Lazy imports inside function bodies to avoid circular imports (used extensively in `_register_core.py`)
- Module-load-time registration via `__init__.py` import (e.g., `import ztlctl.actions` triggers `_register_core_actions()`)
- `PluginManager.discover_and_load(local_dir=...)` pattern for plugin discovery

### Integration Points
- `src/ztlctl/actions/__init__.py` — triggers `_register_core_actions()` on import
- `src/ztlctl/commands/__init__.py` — `load_plugin_commands()` creates PluginManager independently
- `src/ztlctl/commands/generator.py` — reads ActionRegistry to generate CLI commands
- `src/ztlctl/infrastructure/vault.py` — creates PluginManager for vault runtime
- `tests/actions/test_core_registrations.py` — validates all registrations

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase

</specifics>

<deferred>
## Deferred Ideas

None

</deferred>
