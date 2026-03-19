# Domain Pitfalls

**Domain:** Plugin system formalization, CLI/MCP unification, agentic integration for a Zettelkasten CLI
**Researched:** 2026-03-19

---

## Critical Pitfalls

Mistakes that cause rewrites or major issues.

### Pitfall 1: Premature Plugin API Freeze

**What goes wrong:** The plugin API is formalized and documented before the "define-once" action model is proven. Plugin authors build against it. Then the action model needs changes (new parameters, different return shapes, renamed hooks), and every published plugin breaks. This is especially dangerous because ztlctl already has 8 hookspecs and plugin contribution contracts — the existing surface is the informal version that may not survive the unification.

**Why it happens:** Excitement to ship the formalized system before validating that the unified action/event model actually covers all the cases the current hand-crafted CLI and MCP tool surfaces handle. The current hookspecs (`post_create`, `post_update`, etc.) and contribution contracts (`CliCommandContribution`, `McpToolContribution`) were designed for v1's architecture. A "define-once" action model will likely change the shape of these hooks fundamentally — e.g., moving from `post_create(content_type, content_id, title, path, tags)` to a generic `post_action(action_name, action_result)` pattern.

**Consequences:** Plugin API churn destroys trust. Third-party plugin authors stop investing if the API breaks repeatedly. The existing GitPlugin and ReweavePlugin would need rewrites. The contribution contracts in `contracts.py` (8 frozen dataclasses) become dead code.

**Prevention:**
1. Mark the plugin API as `experimental` / `unstable` in the first release after formalization. Use a version prefix (e.g., `ztlctl.hooks.v1`) so old hooks coexist with new ones.
2. Build the action model and auto-generation layer first as internal-only. Only promote to plugin API after the core CLI and MCP surfaces are successfully generated from it.
3. Keep the existing hookspecs working as compatibility shims during transition. Deprecate, don't delete.
4. Write the three built-in plugins (Git, Reweave, and at least one test plugin) against the new API before declaring it stable.

**Detection:** If you find yourself needing to change a hook signature more than once during development, the model is not ready for external consumption. If the `register_content_models` hook cannot express a real custom note type with custom lifecycle, the abstraction is too narrow.

**Phase mapping:** Plugin System Formalization phase. Do not publish the formalized API until the CLI/MCP auto-generation phase proves the action model works.

---

### Pitfall 2: CLI/MCP Parity Regression During Unification

**What goes wrong:** The "define-once" action model introduces a code generation or registry layer between the service layer and the presentation layers (Click CLI + FastMCP tools). During this transition, capabilities that currently exist in one surface but not the other silently disappear, or parameter handling diverges because Click and MCP have fundamentally different type systems.

**Why it happens:** The current codebase has significant duplication between CLI commands (22 files in `commands/`) and MCP tools (29 `_impl` functions in `mcp/tools.py`). Each was hand-crafted with surface-specific concerns. Click commands handle `ctx.obj` AppContext, exit codes, Rich output formatting, and `--verbose`/`--log-json` flags. MCP tools handle vault injection, `_to_mcp_response()` conversion, and catalog metadata. A unified action definition must accommodate both, and the impedance mismatch is real:
- Click uses `click.Choice`, `click.Path`, `click.IntRange` — these have no MCP equivalent
- MCP tools return `dict[str, Any]`; CLI commands write to stdout/stderr with exit codes
- CLI has progressive disclosure (`--verbose`, `--json`); MCP has no equivalent concept
- Click options have `--help` text; MCP tools have `when_to_use` / `avoid_when` guidance

**Consequences:** Users who rely on CLI flags that have no MCP equivalent (like `--json` output mode or `--dry-run` on specific commands) lose functionality. Agents that depend on specific MCP tool response shapes get broken responses. The 1500-line `register_tools()` function in `mcp/tools.py` and the 22 command files represent ~3000 lines of presentation logic that cannot be trivially auto-generated.

**Prevention:**
1. Build a compatibility test suite before starting: for every CLI command, assert the equivalent MCP tool exists and accepts the same logical parameters. For every MCP tool, assert a CLI command exists. This becomes the regression gate.
2. Design the action definition to carry both Click-specific metadata (help text, types, groups) and MCP-specific metadata (catalog entries, side_effect classification) as separate annotation layers on a single definition.
3. Do not attempt full auto-generation in one pass. Start with read-only tools (discovery, query) where the impedance mismatch is smallest, then tackle write tools.
4. Keep the `_impl` functions as the service call boundary — they already abstract away MCP-specific concerns. The unification target is the layer above `_impl`, not below it.

**Detection:** If the generated CLI produces different results than a hand-crafted command for the same inputs, the generation layer is lossy. Run the existing 797+ tests after each generation step.

**Phase mapping:** CLI/MCP Unification phase. Must come after the action model is designed but may need to happen incrementally rather than all-at-once.

---

### Pitfall 3: Breaking Existing Vaults During Lifecycle Formalization

**What goes wrong:** Formalizing the note lifecycle (making "note types" and "status transitions" extensible primitives) requires changes to the domain layer (`lifecycle.py`, `content.py`) that invalidate existing vault data. Notes created under the informal system have frontmatter that the formalized system rejects, or status transition maps change so that previously valid state changes become illegal.

**Why it happens:** The current lifecycle is hard-coded in `domain/lifecycle.py` with four separate transition maps (`NOTE_TRANSITIONS`, `REFERENCE_TRANSITIONS`, `TASK_TRANSITIONS`, `DECISION_TRANSITIONS`). Formalizing this into an extensible primitive means moving from compile-time constants to runtime-registered lifecycle definitions. If the registration mechanism requires metadata that existing notes lack (e.g., a `lifecycle_version` field), every note in every vault is "invalid" until migrated.

**Consequences:** Users cannot upgrade ztlctl without running a migration. If the migration is lossy or introduces ambiguity (e.g., a note with `status: active` could map to two different formalized states), data corruption occurs silently. The `check --rebuild` command, which is the safety net, may itself break if it depends on the old lifecycle definitions.

**Prevention:**
1. The formalized lifecycle system must treat the current four lifecycle maps as the built-in defaults, not as something that replaces them. Existing notes with no `lifecycle_version` field are implicitly v1.
2. Add a schema version or lifecycle version to vault metadata (not per-note frontmatter) so the system knows which lifecycle rules to apply.
3. Write a `check --upgrade` or `upgrade` command that detects the vault schema version and applies forward-migrations before any other operation.
4. Test the migration path with real vaults created under v1. The 1256 existing tests create test vaults — use these as migration test fixtures.

**Detection:** If `check --rebuild` on a v1 vault produces warnings or errors after the formalization changes, the migration is incomplete. If any existing test in the 797-test CLI suite fails without code changes to the test itself, the formalization broke backward compatibility.

**Phase mapping:** Core Hardening phase (data model consistency) and Plugin System Formalization phase. The hardening phase should stabilize the lifecycle model before the plugin phase makes it extensible.

---

### Pitfall 4: Action Model Becomes a God Object

**What goes wrong:** The "define-once" action model tries to capture everything about an operation — its parameters, validation rules, CLI presentation, MCP metadata, event hooks, permissions, telemetry spans — in a single definition. This definition becomes a massive, deeply nested data structure that is harder to maintain than the duplication it replaced.

**Why it happens:** The motivation for unification is real: the current codebase has ~29 MCP tools, ~22 CLI command files, 8 hookspecs, and 6 services, all describing overlapping but non-identical views of the same operations. The temptation is to create a single `ActionDefinition` dataclass that captures all of these concerns. But different consumers need different things:
- CLI needs: help text, option groups, types, exit codes, output formatters
- MCP needs: tool descriptions, arg guidance, side_effect classification, when_to_use/avoid_when
- Events need: hook names, payload shapes, retry policies
- Telemetry needs: span names, metric labels
- Plugins need: pre/post hooks, capability checks

**Consequences:** The `ActionDefinition` becomes a 200-field monster that nobody can reason about. Changes to CLI presentation require touching the same definition as changes to MCP catalog entries. The single definition becomes the coupling point that makes all changes risky.

**Prevention:**
1. Use a layered annotation pattern, not a monolithic definition. The core action defines: name, parameters with types, validation rules, service method to call, and return type. CLI metadata, MCP metadata, event metadata, and telemetry metadata are separate, optional annotation layers that reference the core action by name.
2. Look at how Django REST Framework separates serializers, views, and URL routing — three separate declarations that reference the same model but serve different concerns.
3. Set a complexity budget: if the action definition for `create_note` exceeds 50 lines, the abstraction is too heavy. The current `_impl` function is 15 lines; the current CLI command is ~40 lines; the current catalog entry is ~15 lines. Combined they are ~70 lines across 3 files. A single definition should not exceed that.
4. Start with the simplest possible action definition (name + params + service method) and add layers only when a concrete consumer needs them.

**Detection:** If defining a new action requires filling in more than 10 fields, the model is too heavy. If changing a CLI help string requires modifying the same file as changing an MCP description, the concerns are not separated.

**Phase mapping:** Plugin System Formalization phase (action model design). This is the single most important design decision in v2.

---

## Moderate Pitfalls

### Pitfall 5: Plugin Discovery Race Condition with Entry Points

**What goes wrong:** The current `PluginManager` uses `importlib.metadata.entry_points()` for discovery. When the formalized plugin system allows plugins to register CLI commands and MCP tools, plugin loading order matters: a plugin that registers a CLI command group must be loaded before Click builds the command tree, and an MCP tool must be registered before `register_tools()` runs. If plugins are slow to load (e.g., importing heavy dependencies like `sentence-transformers`), the CLI or MCP server starts with an incomplete tool surface.

**Prevention:**
1. Split plugin discovery (finding what exists) from plugin activation (loading code). Discovery reads entry-point metadata only; activation imports the plugin module.
2. Use lazy activation: plugins are activated on first use, not at startup. This matches the existing lazy-import pattern used throughout the codebase (e.g., `from ztlctl.services.create import CreateService` inside `_impl` functions).
3. Set a hard timeout on plugin activation (the EventBus already has a 30-second timeout on futures — apply the same principle to plugin loading).

**Detection:** If `ztlctl --help` takes more than 500ms on a cold start with plugins installed, plugin loading is too eager.

**Phase mapping:** Plugin System Formalization phase.

---

### Pitfall 6: MCP Tool Explosion for Agents

**What goes wrong:** As the plugin system allows arbitrary tool registration, the MCP tool surface grows beyond what an LLM can effectively navigate. The current 29 tools are already at the upper bound of what most models handle well. Adding plugin-contributed tools pushes past 40-50 tools, degrading agent performance because the model spends context window on tool descriptions instead of user tasks.

**Why it happens:** The MCP protocol has no built-in mechanism for progressive tool disclosure. Every registered tool's description is included in the system prompt (or tool listing), consuming tokens proportional to the number of tools. The current tool catalog entries average ~150 tokens each; 50 tools = ~7,500 tokens just for tool descriptions.

**Prevention:**
1. Implement tool filtering by category (already partially supported via `discover_tools(category=...)`) and make this the default for agent sessions — agents start with only the `discovery` category active and activate others on demand.
2. Set a maximum tool count per MCP session (e.g., 40 tools). Plugin tools that exceed this limit are available via `discover_tools` but not auto-registered.
3. Design tool descriptions to be concise: the current `_render_tool_doc()` generates multi-line descriptions. Consider a compact mode for agents that only includes `description` + `args_guidance`, not `when_to_use` / `avoid_when`.
4. Implement tool namespacing: plugin tools are prefixed with the plugin name (e.g., `git_commit` not `commit`) to avoid collisions and help agents disambiguate.

**Detection:** If an agent consistently fails to pick the right tool on the first try, or if `discover_tools` response exceeds 4,000 tokens, the tool surface is too large.

**Phase mapping:** Agentic Integration phase.

---

### Pitfall 7: EventBus as Implicit Coupling Layer

**What goes wrong:** The existing EventBus (WAL-backed async dispatch via pluggy + ThreadPoolExecutor) becomes the de facto integration backbone for the formalized plugin system. But it was designed for fire-and-forget lifecycle notifications (post_create, post_update), not for request-response interactions that plugins need (e.g., "validate this custom note type before creation" or "transform this content before persistence").

**Why it happens:** The hookspecs are currently all `post_*` — they run after the operation completes and cannot influence the outcome. Formalizing "pre/post hooks on every core action" (per PROJECT.md) requires pre-hooks that can reject or modify the action. The EventBus's WAL-backed async dispatch is wrong for pre-hooks: you cannot asynchronously validate something that must complete before the action proceeds.

**Prevention:**
1. Separate the event dispatch (async, fire-and-forget, WAL-backed) from hook dispatch (synchronous, can return values, can raise to abort). Use pluggy's existing `firstresult` and `trylast`/`tryfirst` markers for synchronous pre-hooks.
2. Pre-hooks must be synchronous and run in the service method's transaction. Post-hooks can remain async via the EventBus.
3. Define a clear contract: pre-hooks receive the action's validated parameters and return either `None` (proceed) or raise `PluginRejectError` (abort with message). Post-hooks receive the action's result and cannot influence it.
4. Do not route pre-hooks through the WAL. They are synchronous and do not need retry semantics.

**Detection:** If you find yourself adding `sync=True` to every pre-hook dispatch, the EventBus is the wrong mechanism. If pre-hook failures leave WAL entries in `failed` state that get retried (nonsensically, since the action already completed or aborted), the abstraction is leaking.

**Phase mapping:** Plugin System Formalization phase. Must be resolved before pre-hooks are exposed to plugins.

---

### Pitfall 8: Agent State Assumptions Across Tool Calls

**What goes wrong:** Agents assume state persists between MCP tool calls (e.g., "I created a note, so the next `get_related` call will include it"). But the MCP server creates services per-call (each `_impl` function instantiates a new service), and graph materialization is not automatic. The agent's mental model of vault state diverges from actual state.

**Why it happens:** The current MCP server creates a single `Vault` instance in `create_server()` that persists across all tool calls within a session. Database writes are visible immediately. But graph-dependent operations (related, themes, rank, bridges, gaps) depend on the in-memory NetworkX graph, which may be stale if `invalidate()` was not called. Similarly, vector embeddings are only generated if `VectorService` is available and auto-embed is enabled. The agent has no way to know whether the graph or vector index reflects its recent writes.

**Prevention:**
1. After every write operation, include a `stale_indexes` field in the response indicating which indexes may be out of date (e.g., `{"graph": true, "vectors": true}`).
2. Auto-trigger `graph.invalidate()` after every write tool call (this is a no-op if no graph operations follow).
3. Document in tool descriptions that graph-based tools may not reflect very recent writes unless `graph materialize` has been run.
4. Consider adding an `ensure_fresh` parameter to graph tools that triggers a lightweight invalidation before the operation.

**Detection:** If an agent creates a note and immediately calls `get_related` for that note and gets zero results, the staleness problem is real. Test this flow explicitly.

**Phase mapping:** Agentic Integration phase (MCP tool surface completeness).

---

### Pitfall 9: Copier Template Trust Escalation via Plugins

**What goes wrong:** The existing `WorkflowService` already executes Copier templates from external URLs (flagged in CONCERNS.md as a security risk). If plugins can register workflow modules (`register_workflow_modules` hookspec) and vault init steps (`register_vault_init_steps` hookspec), a malicious plugin could register a workflow that executes arbitrary code via Copier's Jinja2 hooks.

**Prevention:**
1. Plugin-contributed workflow templates must be restricted to local paths only — no URL-based templates from plugins.
2. Add a plugin capability/permission model: plugins declare what they need (`capabilities: [cli_commands, mcp_tools]`), and the system only grants those capabilities. A plugin that requests `workflow_modules` gets extra scrutiny.
3. Run Copier with `--trust=false` for plugin-contributed templates (Copier 9.x supports this).
4. Log all plugin-initiated template executions at WARNING level so the user can audit them.

**Detection:** If a plugin can cause code execution without the user's explicit knowledge, the trust boundary is broken. Audit by searching for `run_copy` and `run_update` calls that originate from plugin-contributed paths.

**Phase mapping:** Security Hardening phase (must be addressed before plugins can contribute workflows).

---

## Minor Pitfalls

### Pitfall 10: Test Infrastructure Collapse During Refactoring

**What goes wrong:** The current test suite (1256 tests) was built against the hand-crafted CLI and MCP surfaces. Introducing an auto-generation layer changes the code paths those tests exercise. Tests that mock specific Click commands or `_impl` functions may pass even though the generated surface is broken, because the mocks bypass the generation layer.

**Prevention:**
1. Add integration tests that exercise the generated CLI commands end-to-end (invoke Click commands via `CliRunner`, not by calling service methods directly).
2. Do not delete the existing tests during the transition. Instead, add a parallel test layer for the generated surfaces.
3. The existing MCP `_impl` functions should remain testable as-is — they are the right abstraction boundary. Test the generation layer by asserting that generated wrappers produce the same results as direct `_impl` calls.

**Phase mapping:** All phases. Every refactoring step should run the full test suite before committing.

---

### Pitfall 11: Over-Engineering Custom Note Types

**What goes wrong:** The formalized "plugins can register custom note types with custom lifecycles" feature leads to note types that are too complex (custom frontmatter schemas, custom validation rules, custom rendering) and cannot interoperate with the core query, graph, and reweave engines. A custom note type that does not conform to the base `ContentModel` contract breaks `QueryService.search()`, `GraphService.related()`, and `ReweaveService.reweave()`.

**Prevention:**
1. Custom note types must extend `ContentModel`, not replace it. The base fields (`id`, `type`, `status`, `title`, `tags`, `links`) are non-negotiable — they are what the query, graph, and reweave engines index on.
2. Custom lifecycle maps must be supersets of the base transitions (can add states, cannot remove `active` or `archived`).
3. Validate at registration time that a custom note type passes a conformance test: can it be created, queried, linked, and archived using the standard service methods?
4. Provide a `CustomNoteType` base class in the plugin SDK that enforces these constraints.

**Detection:** If a custom note type cannot be found via `search()` or does not appear in `graph themes`, it violates the interoperability contract.

**Phase mapping:** Plugin System Formalization phase.

---

### Pitfall 12: Token Budget Miscalculation for Agent Context

**What goes wrong:** The current token estimation uses `len(text) // 4` (a rough English heuristic). As agents use ztlctl with non-English vaults or with notes containing dense JSON/YAML frontmatter, the estimate diverges. Context assembly (`ContextAssembler.assemble()`) overruns the requested budget, causing the agent to receive truncated or overly large context that degrades performance.

**Prevention:**
1. Replace the `len(text) // 4` heuristic with `tiktoken` for accurate counts when the `tiktoken` package is available, falling back to the heuristic otherwise.
2. Add a safety margin (e.g., assemble to 90% of the requested budget) to absorb estimation error.
3. Include the actual token count (estimated or exact) in the `agent_context` response so the agent can validate its context window usage.

**Detection:** If `agent_context(budget=4000)` returns content that actually consumes 5,500+ tokens, the estimation is dangerously wrong. Test with frontmatter-heavy notes.

**Phase mapping:** Agentic Integration phase.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Core Hardening | Breaking existing vaults during lifecycle cleanup | Test migration with real v1 vaults; add schema version to vault metadata |
| Core Hardening | `check --rebuild` depends on assumptions that change during hardening | Run rebuild integration tests after every hardening change |
| Plugin System Formalization | Premature API freeze before action model is validated | Keep API marked `experimental`; validate with all 3 built-in plugins first |
| Plugin System Formalization | Action model becomes a god object | Use layered annotations, not monolithic definitions; complexity budget of 50 lines per action |
| Plugin System Formalization | EventBus misused for synchronous pre-hooks | Separate sync hook dispatch from async event dispatch |
| CLI/MCP Unification | Parity regression — features lost during auto-generation | Build parity test suite before starting; migrate incrementally (read-only first) |
| CLI/MCP Unification | Click and MCP type system impedance mismatch | Design type mapping layer; accept that some CLI-specific features cannot be auto-generated |
| Agentic Integration | Tool explosion beyond LLM effective limit (~30-40 tools) | Implement progressive tool disclosure; cap auto-registered tools |
| Agentic Integration | Agent assumes fresh state after writes but graph/vector indexes are stale | Return `stale_indexes` in write responses; auto-invalidate graph after writes |
| Security Hardening | Plugin-contributed workflows escalate to arbitrary code execution | Restrict plugin workflows to local paths; enforce Copier `--trust=false` |

---

## Sources

- [HiddenLayer: MCP Model Context Pitfalls in an Agentic World](https://hiddenlayer.com/innovation-hub/mcp-model-context-pitfalls-in-an-agentic-world/) (MCP security pitfalls, tool poisoning, permission issues)
- [Thoughtworks: MCP Impact on 2025](https://www.thoughtworks.com/en-us/insights/blog/generative-ai/model-context-protocol-mcp-impact-2025) (MCP ecosystem maturity and adoption risks)
- [PySpector Plugin Sandbox Bypass CVE-2026-33139](https://advisories.gitlab.com/pkg/pypi/pyspector/CVE-2026-33139/) (plugin system security validation bypass via `getattr()`)
- [Builder.io: Good vs Bad Refactoring](https://www.builder.io/blog/good-vs-bad-refactoring) (formalization and abstraction pitfalls)
- [pluggy Documentation](https://pluggy.readthedocs.io/en/stable/) (hookspec patterns, firstresult, trylast/tryfirst)
- ztlctl codebase analysis: `src/ztlctl/plugins/hookspecs.py`, `src/ztlctl/plugins/contracts.py`, `src/ztlctl/mcp/tools.py`, `src/ztlctl/plugins/event_bus.py`, `src/ztlctl/services/base.py`, `.planning/codebase/CONCERNS.md`
