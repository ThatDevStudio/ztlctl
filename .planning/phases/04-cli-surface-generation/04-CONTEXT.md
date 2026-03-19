# Phase 4: CLI Surface Generation - Context

**Gathered:** 2026-03-19
**Status:** Ready for planning
**Source:** Auto-selected defaults (--auto flag)

<domain>
## Phase Boundary

Auto-generate CLI commands from the ActionRegistry, replacing hand-crafted Click command files (~2650 lines across 20+ files). Standard CRUD-style commands are generated; complex commands (batch, init wizard, serve, interactive create) retain hand-written implementations via the `custom_presentation` escape hatch (ACTN-05). Generated commands support `--verbose`, `--json`, progressive disclosure, and exit codes identically to hand-written predecessors. The Phase 3 parity test suite continues to pass, confirming CLI/MCP equivalence is maintained by construction (ACTN-04).

</domain>

<decisions>
## Implementation Decisions

### CLI generation strategy
- **Runtime generation** — iterate the ActionRegistry at CLI startup and dynamically create Click commands from ActionDefinitions. Matches the Phase 3 MCP generation pattern. No static codegen step.
- **AppContext pattern preserved** — generated commands use the existing AppContext (lazy Vault, emit(), OutputSettings) via `@click.pass_obj`. No new DI pattern for CLI.
- **cli_group field drives group assignment** — ActionDefinition.cli_group maps directly to Click command groups. `None` means top-level. Generator creates groups as needed.
- **Non-custom_presentation actions auto-generated** — the ~54 standard ActionDefinitions become auto-generated Click commands. The 5 `custom_presentation` actions retain hand-written implementations.

### custom_presentation handling (ACTN-05)
- **Hand-written commands preserved for complex operations** — batch (multi-file JSON input), init wizard (interactive multi-step), serve (server lifecycle), workflow init/update (Copier integration). These need interactive prompts, wizard flows, or server management that can't be auto-generated.
- **Custom commands still call controllers** — hand-written commands call the same controller layer as generated commands. Architecture invariant maintained: controller is the only way to expose functionality.
- **Registry awareness** — custom_presentation actions are still registered in the ActionRegistry (discoverable, hookable) but the CLI generator skips them, leaving their hand-written Click commands in place.

### Output formatting & progressive disclosure
- **Generic output formatter** — generated commands pass ServiceResult through the existing `format_result()` + `OutputSettings` pipeline. `--verbose` and `--json` flags handled uniformly by AppContext.emit().
- **Exit codes via emit()** — ServiceResult.ok maps to exit 0 (success) / exit 1 (error). Same pattern as current hand-written commands.
- **Progressive disclosure preserved** — summary output by default, `--verbose` for details, `--json` for machine-readable. Generated commands get this for free via the output formatter.

### Migration & cleanup
- **Delete auto-generatable command files** — standard command files (query.py, graph.py, reweave.py, update.py, etc.) replaced by the generator. Keep `_context.py` (AppContext), `_base.py` (ZtlGroup), and custom_presentation files (create.py batch ops, init_cmd.py wizard, serve.py server, workflow.py Copier).
- **Both unit tests for generator + CLI integration tests** — generator tests verify Click command creation from ActionDefinitions. CLI integration tests use Click's CliRunner for end-to-end command invocation. Matches Phase 3 testing approach.
- **Parity test extension** — extend the Phase 3 parity test suite to also verify CLI↔ActionDefinition mapping, not just MCP↔ActionDefinition.

### Claude's Discretion
- **ActionParam to Click type mapping** — how ActionParam.type (Python types) maps to Click types (STRING, INT, BOOL, Choice). ActionParam already has `choices`, `cli_multiple`, `cli_is_argument`, `cli_flag` fields to guide this.
- **Interactive prompt generation** — how `cli_interactive_params` triggers Click prompts for specified parameters when `--interactive` is set. Whether to use Click's built-in prompt or a custom mechanism.
- **Generator module organization** — file naming and structure for the CLI generation code. Whether it lives in `commands/` or a new `cli/` package.
- **Help text generation** — how ActionDefinition.description and ActionParam.description map to Click help strings and command docstrings.
- **Subtype validation** — current `_validate_subtype()` callback pattern in create.py handles dynamic subtypes. How to replicate this for generated commands.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ActionRegistry (generation source)
- `src/ztlctl/actions/definitions.py` — ActionParam + ActionDefinition with CLI metadata fields (cli_group, cli_examples, cli_interactive_params, custom_presentation)
- `src/ztlctl/actions/registry.py` — ActionRegistry singleton with list_actions(custom_presentation=False) filter
- `src/ztlctl/actions/_register_core.py` — All 59 built-in registrations showing cli_group assignments

### Phase 3 generator (pattern to follow)
- `src/ztlctl/mcp/generator.py` — MCP tool generator using ActionRegistry iteration pattern. Phase 4 CLI generator should follow the same approach.
- `src/ztlctl/mcp/response.py` — McpResponse Pydantic model. CLI equivalent uses existing format_result().

### Current CLI layer (to be replaced)
- `src/ztlctl/commands/` — 20+ hand-written Click command files (~2650 lines total)
- `src/ztlctl/commands/_context.py` — AppContext (lazy Vault, emit(), OutputSettings) — KEEP
- `src/ztlctl/commands/_base.py` — ZtlGroup (Click group customization) — KEEP
- `src/ztlctl/output/formatters.py` — format_result() + OutputSettings — KEEP (used by generated commands)

### Custom presentation commands (to be preserved)
- `src/ztlctl/commands/create.py` — batch JSON input, interactive subtype validation
- `src/ztlctl/commands/init_cmd.py` — multi-step wizard flow
- `src/ztlctl/commands/serve.py` — server lifecycle management
- `src/ztlctl/commands/workflow.py` — Copier integration

### Requirements
- `.planning/REQUIREMENTS.md` — ACTN-04 (auto-generated CLI), ACTN-05 (escape hatch preservation)

### Prior phase context
- `.planning/phases/03-mcp-surface-generation/03-CONTEXT.md` — Phase 3 decisions: runtime generation, Pydantic responses, single registration path

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `ActionDefinition.cli_group/cli_examples/cli_interactive_params`: CLI metadata already captured per action — generator reads these directly
- `AppContext.emit()`: Centralized result emission with exit codes, --verbose, --json — generated commands use this unchanged
- `format_result()` + `OutputSettings`: Rich/JSON formatters already handle ServiceResult → CLI output
- `ZtlGroup`: Custom Click group class with command sorting — generated groups should use this
- `mcp/generator.py`: Proven pattern for iterating ActionRegistry and producing runtime registrations

### Established Patterns
- **AppContext on ctx.obj via @click.pass_obj**: All commands access Vault and settings through this pattern
- **Lazy Vault init**: AppContext.vault property — `--help` and `--version` never trigger DB access
- **Factory lambda handlers**: `lambda vault, **kw: Controller(vault).method(**kw)` — same handlers used by MCP generator
- **Click callback validators**: `_validate_subtype()` pattern in create.py — needed for generated commands with choices

### Integration Points
- `src/ztlctl/commands/__init__.py`: Root CLI group where generated commands are registered
- `src/ztlctl/output/formatters.py`: Output pipeline that generated commands flow through
- `tests/mcp/test_parity.py`: Parity test suite to extend for CLI verification

</code_context>

<specifics>
## Specific Ideas

- Phase 3's MCP generator proved the ActionRegistry→presentation pattern works. Phase 4 applies the same pattern to CLI, completing the "define-once, use-everywhere" vision from PROJECT.md.
- The `custom_presentation` flag was designed specifically for this phase — actions that need hand-written CLI (batch, init wizard, serve) are already marked. The generator skips them by construction.
- AppContext.emit() is the CLI equivalent of McpResponse.from_result() — both convert ServiceResult to presentation-layer output.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-cli-surface-generation*
*Context gathered: 2026-03-19 via --auto defaults*
