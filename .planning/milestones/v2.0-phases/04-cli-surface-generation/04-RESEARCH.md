# Phase 4: CLI Surface Generation - Research

**Researched:** 2026-03-19
**Domain:** Click dynamic command generation from ActionRegistry; Python runtime introspection
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Runtime generation** — iterate the ActionRegistry at CLI startup and dynamically create Click commands from ActionDefinitions. Matches the Phase 3 MCP generation pattern. No static codegen step.
- **AppContext pattern preserved** — generated commands use the existing AppContext (lazy Vault, emit(), OutputSettings) via `@click.pass_obj`. No new DI pattern for CLI.
- **cli_group field drives group assignment** — ActionDefinition.cli_group maps directly to Click command groups. `None` means top-level. Generator creates groups as needed.
- **Non-custom_presentation actions auto-generated** — the ~54 standard ActionDefinitions become auto-generated Click commands. The 5 `custom_presentation` actions retain hand-written implementations.
- **Hand-written commands preserved for complex operations** — batch (multi-file JSON input), init wizard (interactive multi-step), serve (server lifecycle), workflow init/update/export_assets (Copier integration). These need interactive prompts, wizard flows, or server management that can't be auto-generated.
- **Custom commands still call controllers** — hand-written commands call the same controller layer as generated commands. Architecture invariant maintained: controller is the only way to expose functionality.
- **Registry awareness** — custom_presentation actions are still registered in the ActionRegistry (discoverable, hookable) but the CLI generator skips them, leaving their hand-written Click commands in place.
- **Generic output formatter** — generated commands pass ServiceResult through the existing `format_result()` + `OutputSettings` pipeline. `--verbose` and `--json` flags handled uniformly by AppContext.emit().
- **Exit codes via emit()** — ServiceResult.ok maps to exit 0 (success) / exit 1 (error). Same pattern as current hand-written commands.
- **Progressive disclosure preserved** — summary output by default, `--verbose` for details, `--json` for machine-readable. Generated commands get this for free via the output formatter.
- **Delete auto-generatable command files** — standard command files (query.py, graph.py, reweave.py, update.py, etc.) replaced by the generator. Keep `_context.py`, `_base.py`, and custom_presentation files.
- **Both unit tests for generator + CLI integration tests** — generator tests verify Click command creation from ActionDefinitions. CLI integration tests use Click's CliRunner for end-to-end command invocation. Matches Phase 3 testing approach.
- **Parity test extension** — extend the Phase 3 parity test suite to also verify CLI↔ActionDefinition mapping, not just MCP↔ActionDefinition.

### Claude's Discretion
- **ActionParam to Click type mapping** — how ActionParam.type (Python types) maps to Click types (STRING, INT, BOOL, Choice). ActionParam already has `choices`, `cli_multiple`, `cli_is_argument`, `cli_flag` fields to guide this.
- **Interactive prompt generation** — how `cli_interactive_params` triggers Click prompts for specified parameters when `--interactive` is set. Whether to use Click's built-in prompt or a custom mechanism.
- **Generator module organization** — file naming and structure for the CLI generation code. Whether it lives in `commands/` or a new `cli/` package.
- **Help text generation** — how ActionDefinition.description and ActionParam.description map to Click help strings and command docstrings.
- **Subtype validation** — current `_validate_subtype()` callback pattern in create.py handles dynamic subtypes. How to replicate this for generated commands.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ACTN-04 | Auto-generated CLI commands from ActionDefinitions — replaces hand-crafted Click command files; handles interactive prompts, AppContext.emit(), exit codes, --verbose/--json flags, progressive disclosure | ActionParam CLI metadata fields (`cli_group`, `cli_is_argument`, `cli_flag`, `cli_multiple`, `choices`, `cli_interactive_params`) provide all generator inputs; AppContext.emit() already handles all output concerns; `_make_tool_fn` in mcp/generator.py is the exact pattern to follow |
| ACTN-05 | Escape hatch preservation — batch operations, init wizard, serve command, and other complex commands retain hand-written implementations where the ActionDefinition abstraction doesn't fit | `custom_presentation=True` on 5 ActionDefinitions (create_batch, init_vault, init_workflow, update_workflow, export_assets) gates generator skipping; corresponding hand-written files already exist |
</phase_requirements>

---

## Summary

Phase 4 applies the exact same registry-iteration pattern proven in Phase 3 (MCP generation) to the CLI surface. The `mcp/generator.py` module is the canonical blueprint: iterate `get_action_registry().list_actions()`, build a function per action with proper metadata, and register it with the presentation layer (MCP server or Click group). For CLI, "registration" means `group.command()(fn)` instead of `server.tool()(fn)`.

The ActionDefinition dataclass already contains all the CLI-specific metadata needed: `cli_group` (which Click group to register under), `cli_examples` (--examples flag content), `cli_interactive_params` (params to prompt when --interactive), `custom_presentation` (generator skip flag), and per-param fields `cli_is_argument`, `cli_flag`, `cli_multiple`, `choices`. The generator's sole job is to read these fields and call Click's API accordingly.

The migration scope is well-bounded: 54 standard ActionDefinitions become generated commands; 5 `custom_presentation` actions (create_batch, init_vault, init_workflow, update_workflow, export_assets) keep hand-written implementations. The files to delete are identifiable now. The `catalogs.py` `_CLI_COMMAND_CATALOG` static list must be replaced with a dynamic catalog derived from the ActionRegistry, mirroring what Phase 3 did for `tool_catalog()`.

**Primary recommendation:** Build `src/ztlctl/commands/generator.py` mirroring the structure and patterns of `src/ztlctl/mcp/generator.py`. Use `registry.list_actions(custom_presentation=False)` to filter, map ActionParam fields to Click parameter constructors, and call `group.add_command()` or `cli.add_command()` to register. Replace `register_commands()` in `commands/__init__.py` to call `generate_commands(cli)` + re-add custom_presentation hand-written commands.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.x (project-pinned) | Command creation, parameter types, group registration | Already used throughout; `click.command()`, `click.Group`, `click.Option`, `click.Argument` are the target APIs |
| click.testing.CliRunner | same | Integration test invocation | Already used in all `tests/commands/test_*.py` — no change |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| ZtlGroup / ZtlCommand | project-internal | Custom Click group/command with --examples flag | Use for all generated groups and commands to preserve --examples pattern |
| AppContext | project-internal | Vault access + emit() | `@click.pass_obj` on every generated command — unchanged from hand-written pattern |
| ActionRegistry | project-internal | Source of ActionDefinitions | `get_action_registry().list_actions(custom_presentation=False)` is the generator input |

**Installation:** No new dependencies required. All needed libraries are already present.

---

## Architecture Patterns

### Recommended Project Structure
```
src/ztlctl/commands/
├── _context.py           # KEEP — AppContext unchanged
├── _base.py              # KEEP — ZtlGroup, ZtlCommand, RootZtlGroup unchanged
├── generator.py          # NEW — CLI generator (mirrors mcp/generator.py)
├── __init__.py           # MODIFY — replace register_commands() to use generator
├── create.py             # KEEP (custom_presentation: create_batch batch ops, interactive subtype)
├── init_cmd.py           # KEEP (custom_presentation: init_vault wizard)
├── serve.py              # KEEP (custom_presentation: server lifecycle)
├── workflow.py           # KEEP (custom_presentation: Copier integration)
├── [all others]          # DELETE after generator produces equivalent commands
```

### Pattern 1: CLI Command Function Factory (mirror of `_make_tool_fn`)

The core pattern is building a Click command callback dynamically — setting `__name__`, `__doc__`, and attaching Click parameter objects.

**What:** Build a `click.Command` (or `ZtlCommand`) for a given `ActionDefinition` by:
1. Mapping each `ActionParam` to a `click.Argument` or `click.Option`
2. Creating a callback that unpacks kwargs and calls `action.handler(app.vault, **kwargs)` then `app.emit(result)`
3. Setting `__name__`, `__doc__` from action metadata
4. Wrapping with `@click.pass_obj` semantics

**When to use:** For every ActionDefinition where `custom_presentation=False`.

**Example:**
```python
# Source: pattern derived from src/ztlctl/mcp/generator.py _make_tool_fn
import click
from ztlctl.commands._base import ZtlCommand
from ztlctl.actions.definitions import ActionDefinition, ActionParam

def _param_to_click(p: ActionParam) -> click.Parameter:
    """Map one ActionParam to a Click parameter."""
    if p.cli_is_argument:
        return click.Argument([p.name])
    if p.cli_flag:
        return click.Option([f"--{p.name.replace('_', '-')}"], is_flag=True, default=False, help=p.description)
    if p.choices is not None:
        return click.Option(
            [f"--{p.name.replace('_', '-')}"],
            type=click.Choice(list(p.choices)),
            default=p.default,
            required=p.required,
            help=p.description,
        )
    if p.cli_multiple:
        return click.Option(
            [f"--{p.name.replace('_', '-')}"],
            multiple=True,
            default=(),
            help=p.description,
        )
    click_type = {int: click.INT, float: click.FLOAT, bool: click.BOOL}.get(p.type, click.STRING)
    return click.Option(
        [f"--{p.name.replace('_', '-')}"],
        type=click_type,
        default=p.default,
        required=p.required,
        help=p.description,
    )


def _make_command(action: ActionDefinition) -> click.Command:
    """Build a ZtlCommand from an ActionDefinition."""
    params = [_param_to_click(p) for p in action.params]

    # Inject @click.pass_obj via pass_context=False, obj=True pattern
    @click.pass_obj
    def callback(app, **kwargs):  # type: ignore[no-untyped-def]
        # cli_multiple params arrive as tuples — convert to list | None
        for p in action.params:
            if p.cli_multiple and p.name in kwargs:
                val = kwargs[p.name]
                kwargs[p.name] = list(val) if val else None
        result = action.handler(app.vault, **kwargs)
        app.emit(result)

    callback.__name__ = action.name

    cmd = ZtlCommand(
        name=action.name.replace("_", "-"),
        callback=callback,
        params=params,
        help=action.description,
        examples=action.cli_examples or None,
    )
    return cmd
```

**Critical detail:** `cli_multiple` params arrive as empty tuples `()` from Click when no values are passed, but handlers expect `list | None`. The callback must normalize `() -> None` and `("a", "b") -> ["a", "b"]`.

### Pattern 2: Group Creation and Registration

**What:** Groups are created lazily on demand keyed by `action.cli_group`. Top-level (`cli_group=None`) actions go directly on the root CLI group.

```python
# Source: pattern from src/ztlctl/commands/__init__.py register_commands()
def generate_commands(cli: click.Group) -> None:
    """Register all non-custom_presentation actions as Click commands."""
    from ztlctl.actions import _ensure_registered  # triggers _register_core_actions()
    from ztlctl.actions.registry import get_action_registry

    registry = get_action_registry()
    groups: dict[str, click.Group] = {}

    for action in registry.list_actions(custom_presentation=False):
        group_name = action.cli_group
        cmd = _make_command(action)

        if group_name is None:
            cli.add_command(cmd)
        else:
            if group_name not in groups:
                groups[group_name] = ZtlGroup(name=group_name)
                cli.add_command(groups[group_name])
            groups[group_name].add_command(cmd)
```

### Pattern 3: Custom Presentation Escape Hatch

The 5 custom_presentation files stay registered manually in `commands/__init__.py` alongside the generator call. The generator never sees them because `list_actions(custom_presentation=False)` filters them out.

```python
def register_commands(cli: click.Group) -> None:
    # Auto-generate standard commands
    generate_commands(cli)

    # Register custom_presentation commands (hand-written, must be added manually)
    from ztlctl.commands.create import create      # batch ops
    from ztlctl.commands.init_cmd import init_cmd  # wizard
    from ztlctl.commands.serve import serve        # server lifecycle
    from ztlctl.commands.workflow import workflow  # Copier integration
    cli.add_command(create)
    cli.add_command(init_cmd)
    cli.add_command(serve)
    cli.add_command(workflow)
```

**Note:** The generated `create note`, `create reference`, `create task` commands will conflict with the custom `create` group unless the create group is the custom_presentation vehicle. Looking at the registry: `create_note`, `create_reference`, `create_task` have `cli_group="create"` and `custom_presentation=False`, while `create_batch` has `custom_presentation=True`. This means: the generator creates the `create` group and registers note/reference/task under it; the custom `create.py` provides only the `batch` subcommand. The hand-written `create.py` file is restructured (keep only batch) or the generator is responsible for the full group including the batch command being hand-registered as an additional member.

**Recommended approach:** Generator creates the `create` group and its standard subcommands. The `batch` subcommand from `create.py` is imported and added to the generated group. This avoids group-name collision.

### Pattern 4: ActionParam → Click Type Mapping

Full mapping table derived from existing ActionParam fields:

| ActionParam field | Click construction |
|---|---|
| `cli_is_argument=True` | `click.Argument([name])` |
| `cli_flag=True` | `click.Option([--name], is_flag=True, default=False)` |
| `choices != None` | `click.Option([--name], type=click.Choice(choices), ...)` |
| `cli_multiple=True` | `click.Option([--name], multiple=True, default=())` |
| `type=int` | `click.Option([--name], type=click.INT, ...)` |
| `type=float` | `click.Option([--name], type=click.FLOAT, ...)` |
| `type=bool, cli_flag=False` | `click.Option([--name], type=click.BOOL, ...)` |
| `type=str` (default) | `click.Option([--name], type=click.STRING, ...)` |
| `type=list, cli_multiple=False` | `click.Option([--name], type=click.STRING, ...)` — JSON string input |
| `type=dict` | `click.Option([--name], type=click.STRING, ...)` — JSON string, parsed in callback |

**Special case: `dict` params** — `update.changes`, `init_vault.links` are `dict`-typed. The current hand-written `update.py` decomposes the dict into separate --title/--status/--tags options rather than taking a raw `--changes` JSON string. This is a user-experience decision in Claude's discretion. The generator can either:
1. Render `dict` params as `--param-json` JSON string options (consistent but less ergonomic)
2. Skip dict params and require callers to use MCP or batch

Given that the update.py hand-written command decomposes changes into individual flags, and ActionDefinition.update has `changes: dict` as a single param, the generator must handle dict params gracefully. **Recommended:** render dict params as `--changes '{"key": "val"}'` (JSON string with parse-in-callback). Add a note in help text that JSON format is required.

### Pattern 5: Interactive Prompts via `cli_interactive_params`

When `--interactive` is passed and `settings.no_interact` is False and stdin is a tty, the callback checks `cli_interactive_params` and fires `click.prompt()` for each listed param if not already provided.

```python
# Integrated into generated callback
if action.cli_interactive_params and _is_interactive(app):
    for param_name in action.cli_interactive_params:
        if kwargs.get(param_name) is None:
            kwargs[param_name] = click.prompt(param_name.replace("_", " ").title())
```

`_is_interactive()` already exists in `create.py` and can be moved to `generator.py` or `_context.py`.

### Pattern 6: Command Name Normalization

ActionDefinition names use underscore convention (`create_note`, `work_queue`). Click commands use hyphen convention (`create-note`, `work-queue`). The mapping is: `action.name.replace("_", "-")`.

**Exception:** Some existing commands have different CLI names than action names:
- `list_items` → CLI name `list` (not `list-items`)
- `materialize_metrics` → CLI name `materialize`
- `log_entry` → CLI name `log`
- `export_markdown` → CLI name `markdown`
- `export_indexes` → CLI name `indexes`
- `export_graph` → CLI name `graph`
- `export_dashboard` → CLI name `dashboard`
- `check_pending` → CLI name `check` (inside upgrade group)
- `reindex_all` → CLI name `reindex` (probably)

**Resolution:** Add a `cli_name` field or use a naming convention. The simplest approach: add a `cli_name: str | None = None` field to ActionDefinition (or derive via stripping group prefix). Alternatively, accept underscore-to-hyphen as the sole transform and update existing test invocations.

**Recommended:** Let the generator use `action.name.replace("_", "-")` as the default CLI name. For actions where the old CLI name differs (like `list` for `list_items`), the ActionDefinition should carry an explicit `cli_name` field, OR the generator strips the group prefix (e.g., `export_markdown` in group `export` → strip `export_` → `markdown`). The group-prefix-strip approach requires no schema change and aligns with the existing CLI naming convention.

### Anti-Patterns to Avoid

- **Importing service layer directly in generator**: Hand-written commands import services; generated commands must invoke `action.handler(app.vault, **kwargs)` via the controller layer. The generator never imports services.
- **Using functools.wraps on the generated callback**: `mcp/generator.py` explicitly avoids `functools.wraps` because it overwrites `__annotations__`. Same discipline applies here.
- **Creating groups eagerly before knowing all their commands**: Build all groups after iterating all actions to ensure consistent group construction.
- **Assuming all `cli_multiple` params return lists**: Click returns tuples for `multiple=True` options. Always normalize `tuple -> list | None` in the callback.
- **Hard-coding group help text in generator**: Group descriptions should come from a consistent source. Use the first action's category description, a fixed mapping, or a new field. The existing hand-written groups have hand-crafted group-level help text ("Traverse and analyze the knowledge graph.") — this needs a source.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Type mapping | Custom type resolver | Direct Click type constants (click.INT, click.FLOAT, click.BOOL, click.STRING, click.Choice) | Click's type system handles validation, error messages, tab completion |
| Multiple values | Custom accumulator | `click.Option(..., multiple=True)` | Click handles the tuple accumulation; generator normalizes afterward |
| Flag options | Custom boolean logic | `click.Option(..., is_flag=True)` | Click's is_flag handles --flag/--no-flag semantics correctly |
| CLI testing | subprocess calls | `click.testing.CliRunner` | CliRunner is the canonical Click integration test tool, already used |
| Choice validation | Custom string validator | `click.Choice([...])` | Click validates and provides error messages for bad choices automatically |
| Interactive prompts | Custom input() calls | `click.prompt()` | Click's prompt handles TTY detection, default display, and non-interactive bypass |

**Key insight:** Click's parameter construction API is the entire abstraction. The generator is thin glue between ActionParam metadata and Click constructors — resist the urge to build anything that Click already provides.

---

## Common Pitfalls

### Pitfall 1: Group Name Collision with Custom Presentation Commands

**What goes wrong:** The generator creates a `create` group for `create_note/create_reference/create_task`, and the hand-written `create.py` also defines a `create` group. Registering both causes a duplicate command error or silent shadowing.

**Why it happens:** Generator and manual registration both call `cli.add_command(create_group)` with the same group name.

**How to avoid:** The generator owns the group object. Hand-written batch command's function is imported and added as a subcommand to the generator-owned group. In `register_commands()`:
```python
generate_commands(cli)
# Add batch subcommand to the generated 'create' group
from ztlctl.commands.create import batch
cli.commands["create"].add_command(batch)  # attach to already-registered group
```

**Warning signs:** `click.exceptions.Exit` with "Command 'create' already exists" or silent override where batch is unreachable.

### Pitfall 2: `cli_multiple` Empty Tuple vs. None

**What goes wrong:** Click returns `()` (empty tuple) for `multiple=True` options when no values are passed. Handler expects `None` for "no tags provided". Passing `()` instead of `None` to a service method causes subtle bugs (empty list vs. no override).

**Why it happens:** Click's multiple option semantics differ from the optional-list semantics the service layer expects.

**How to avoid:** In every generated callback, normalize:
```python
for p in action.params:
    if p.cli_multiple and p.name in kwargs:
        val = kwargs[p.name]
        kwargs[p.name] = list(val) if val else None
```

**Warning signs:** Tags/aliases/etc. getting silently cleared on update when user doesn't pass the option.

### Pitfall 3: `dict`-typed ActionParam CLI Representation

**What goes wrong:** `update.changes` and similar dict params have no natural CLI representation. The generator naively creates `--changes STRING`, but users must pass raw JSON strings, and validation only happens at the service layer.

**Why it happens:** The ActionParam type system's `dict` type has no direct Click equivalent.

**How to avoid:** For dict params, generate a `--param-json` option that accepts a JSON string, parse it in the callback before passing to the handler:
```python
if p.type is dict:
    raw = kwargs.pop(f"{p.name}")
    kwargs[p.name] = json.loads(raw) if raw else p.default
```
Include `[JSON]` in the help text. This mirrors how the MCP generator handles dict params (they become `dict[str, Any]` annotations).

**Warning signs:** "json.decoder.JSONDecodeError" at service layer, or dict params silently getting None defaults when non-None was expected.

### Pitfall 4: CLI Name Divergence Breaking Existing Tests

**What goes wrong:** Existing `tests/commands/test_*.py` use the current CLI command names (e.g., `["query", "list"]`, `["graph", "materialize"]`). If the generator produces different names (e.g., `list-items`, `materialize-metrics`), all existing tests fail.

**Why it happens:** Action names use the full compound form (`list_items`), but existing CLI commands used shortened names (`list`).

**How to avoid:** Either (a) add `cli_name` override field to ActionDefinition, or (b) implement group-prefix stripping in the generator (strip `{cli_group}_` prefix from action name when present). Option (b) requires no schema change:
- `export_markdown` in group `export` → strip `export_` → `markdown` ✓
- `list_items` in group None → no prefix to strip → `list-items` (still wrong)
- For cases where no group prefix matches, a fallback mapping dict in the generator works.

**Recommended:** Use explicit `cli_name` field on ActionDefinition for the handful of actions where the names diverge. This is surgical and auditable. Alternatively, document that some existing test invocations must be updated, treating it as an intentional cleanup.

**Warning signs:** Mass test failures in `tests/commands/test_query.py`, `test_graph.py`, etc. immediately on generator integration.

### Pitfall 5: `@click.pass_obj` Application to Generated Callback

**What goes wrong:** `click.pass_obj` is a decorator that wraps the function. Applying it to a dynamically created callback requires careful sequencing — the decorator must be applied before the Command is constructed, not after.

**Why it happens:** Python decorator application order. If `pass_obj` is applied after the Command wraps the callback, Click's context injection doesn't work.

**How to avoid:** Apply `@click.pass_obj` to the inner callback function BEFORE wrapping it in `ZtlCommand`:
```python
@click.pass_obj
def callback(app, **kwargs):
    ...
cmd = ZtlCommand(name=..., callback=callback, params=...)
```
This is the correct order — `callback` is already decorated when passed to ZtlCommand.

**Warning signs:** `TypeError: callback() missing 1 required positional argument` or `app` is `None`/a Click Context instead of an AppContext.

### Pitfall 6: ActionRegistry Not Loaded at Generator Call Time

**What goes wrong:** `_register_core_actions()` is called lazily via `ztlctl.actions.__init__`. If the generator runs before the registry is populated, `list_actions()` returns an empty list.

**Why it happens:** Python module import order. `commands/generator.py` importing `get_action_registry()` at call time is fine; importing at module level may cause circular imports.

**How to avoid:** Trigger registration with a lazy import inside `generate_commands()`:
```python
def generate_commands(cli: click.Group) -> None:
    import ztlctl.actions  # triggers _register_core_actions() via __init__
    from ztlctl.actions.registry import get_action_registry
    ...
```
This mirrors how `mcp/generator.py` handles it by importing `get_action_registry` inside the function body.

**Warning signs:** `generate_commands()` produces zero commands, or `list_actions()` returns `[]` on first call.

---

## Code Examples

Verified patterns from the existing codebase:

### MCP Generator Pattern (exact model to follow)
```python
# Source: src/ztlctl/mcp/generator.py generate_tools()
def generate_tools(server: Any, vault: Any) -> None:
    set_vault(vault)
    registry = get_action_registry()
    for action in registry.list_actions():  # all actions for MCP
        fn = _make_tool_fn(action, vault)
        server.tool()(fn)
    _register_plugin_tools(server, vault)
```

CLI equivalent uses `list_actions(custom_presentation=False)` and adds to Click groups.

### AppContext.emit() — the CLI output pipeline
```python
# Source: src/ztlctl/commands/_context.py AppContext.emit()
def emit(self, result: ServiceResult) -> None:
    settings = OutputSettings(
        json_output=self.settings.json_output,
        quiet=self.settings.quiet,
        verbose=self.settings.verbose,
    )
    output = format_result(result, settings=settings)
    if result.ok:
        click.echo(output)
        if not settings.json_output:
            for warning in result.warnings:
                click.echo(f"WARNING: {warning}", err=True)
    else:
        click.echo(output, err=True)
        raise SystemExit(1)
```

Generated commands call `app.emit(action.handler(app.vault, **kwargs))` — this is the complete output pipeline.

### ActionRegistry filter for generator
```python
# Source: src/ztlctl/actions/registry.py ActionRegistry.list_actions()
# Filter custom_presentation=False to get only auto-generatable actions:
actions = registry.list_actions(custom_presentation=False)
# Currently returns ~54 of 59 total actions (5 have custom_presentation=True)
```

### Click's CliRunner (integration test pattern)
```python
# Source: tests/commands/test_graph.py (all tests follow this pattern)
from click.testing import CliRunner
from ztlctl.cli import cli

def test_related_basic(self, cli_runner: CliRunner, tmp_path: Path) -> None:
    result = cli_runner.invoke(cli, ["--json", "graph", "related", id_map["Alpha"]])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["ok"] is True
```

Generated commands must pass these same CliRunner invocations without modification.

### ZtlCommand/ZtlGroup base classes
```python
# Source: src/ztlctl/commands/_base.py
class ZtlCommand(click.Command):
    def __init__(self, *args: Any, examples: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if examples:
            _add_examples_option(self, examples)

class ZtlGroup(click.Group):
    command_class = ZtlCommand
    def __init__(self, *args: Any, examples: str | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        if examples:
            _add_examples_option(self, examples)
```

Generator uses `ZtlCommand(name=..., callback=..., params=..., examples=action.cli_examples or None)` and `ZtlGroup(name=..., help=..., examples=...)`.

### Parity test structure to extend
```python
# Source: tests/mcp/test_parity.py — extend for CLI
def test_all_actions_have_mcp_tools(parity_server):
    registry_names = {a.name for a in registry.list_actions()}
    tool_names = set(server.tools.keys())
    assert registry_names <= tool_names

# CLI equivalent: verify every non-custom_presentation action has a Click command
def test_all_actions_have_cli_commands(cli_group):
    registry = get_action_registry()
    expected = {a.name for a in registry.list_actions(custom_presentation=False)}
    # verify each name maps to a registered Click command (normalized name)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-written Click command files (~2650 lines across 20+ files) | Generated from ActionRegistry | Phase 4 (now) | Eliminates duplication; CLI/MCP parity enforced by construction |
| Service layer called directly from commands (`GraphService(app.vault).related(...)`) | Controller layer called via `action.handler(app.vault, **kwargs)` | Phase 2 introduced controllers; Phase 4 cements the routing | Commands no longer need to know service signatures |
| Static `_CLI_COMMAND_CATALOG` list in `catalogs.py` | Dynamic catalog derived from ActionRegistry | Phase 4 (now) | Catalog never goes stale; plugins auto-appear in catalog |

**Deprecated/outdated:**
- `commands/query.py`, `commands/graph.py`, `commands/reweave.py`, `commands/update.py`, `commands/archive.py`, `commands/supersede.py`, `commands/extract.py`, `commands/check.py`, `commands/upgrade.py`, `commands/session.py` (via agent.py), `commands/export.py`, `commands/ingest.py`, `commands/vector.py`, `commands/garden.py`: All replaced by generator. Delete after generator is verified.
- `_CLI_COMMAND_CATALOG` in `catalogs.py`: Replace `cli_command_catalog()` with a dynamic derivation from ActionRegistry, same as `tool_catalog()` was replaced in Phase 3.

---

## Open Questions

1. **Command name mapping strategy for actions without clean prefix-stripping**
   - What we know: `list_items` has cli_group=None and current CLI name `list` under the `query` group. The action has no `cli_group="query"` — it has no group assignment.
   - What's unclear: Looking more carefully at _register_core.py — `search`, `get`, `list_items`, `work_queue`, etc. all have NO `cli_group` set (None). But the hand-written `query.py` wraps them in a `query` group. This means: either (a) the current ActionDefinitions are missing `cli_group="query"`, or (b) the "query" group is custom_presentation.
   - **Resolution needed:** The planner must check whether `cli_group` assignments need to be added to query/lifecycle/reweave/check/upgrade/session/ingest/export/vector/init ActionDefinitions in `_register_core.py`, OR accept that these generate as flat top-level commands. Looking at the registry data: `search`, `get`, `list_items` etc. have no `cli_group` — they would generate as top-level commands, which contradicts the existing CLI structure.
   - **Recommendation:** Add `cli_group` assignments to all ActionDefinitions that currently lack them. This is a required `_register_core.py` update in Wave 0 of the plan. The MCP generator didn't need groups; the CLI generator does.

2. **`update` command CLI interface: decomposed flags vs. --changes JSON**
   - What we know: The existing `update.py` decomposes changes into individual --title/--status/--tags/--topic/--body/--maturity flags. The ActionDefinition has `update(content_id, changes: dict)` — a single dict param.
   - What's unclear: Should the generator produce the decomposed interface (better UX), or a `--changes '{"key": "val"}'` JSON interface (simpler generator)?
   - **Recommendation:** The update command's UX is complex enough to qualify as custom_presentation, or the ActionDefinition should be updated to have individual ActionParams matching the decomposed flags (title, status, tags, topic, body, maturity). The latter makes the action discoverable and auto-generated without sacrificing UX. The planner should choose: update ActionDefinition params OR keep update.py as custom_presentation.

3. **`catalogs.py` `_CLI_COMMAND_CATALOG` update**
   - What we know: `cli_command_catalog()` returns a static tuple. It's used in `commands/__init__.py` `load_plugin_commands()` to get reserved names.
   - What's unclear: Should `cli_command_catalog()` be replaced with a dynamic derivation (like `tool_catalog()` was in Phase 3), or just updated?
   - **Recommendation:** Replace with a dynamic derivation from ActionRegistry for consistency. The `load_plugin_commands()` reservation check should be: `reserved = {a.name for a in registry.list_actions(custom_presentation=False)}`.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (uv run pytest) |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `uv run pytest tests/commands/ tests/mcp/test_parity.py -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACTN-04 | Generator creates Click commands from ActionDefinitions | unit | `uv run pytest tests/commands/test_generator.py -x` | ❌ Wave 0 |
| ACTN-04 | Generated CLI commands invoke action handlers and emit results | integration | `uv run pytest tests/commands/test_graph.py tests/commands/test_query.py -x` | ✅ (existing, must pass after migration) |
| ACTN-04 | --verbose, --json, exit codes work on generated commands | integration | `uv run pytest tests/commands/ -x -q` | ✅ (existing) |
| ACTN-05 | custom_presentation commands (create batch, init, serve, workflow) still work | integration | `uv run pytest tests/commands/test_batch_create.py tests/commands/test_init.py tests/commands/test_serve.py tests/commands/test_workflow_cmd.py -x` | ✅ (existing) |
| ACTN-04 | CLI↔ActionDefinition parity: every non-custom action has a CLI command | unit | `uv run pytest tests/mcp/test_parity.py -x` (extended) | ✅ (extend existing) |
| ACTN-04 | ActionParam CLI metadata fully maps: arguments, flags, choices, multiple | unit | `uv run pytest tests/commands/test_generator.py -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/commands/ tests/mcp/test_parity.py -x -q`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/commands/test_generator.py` — unit tests for `_param_to_click()`, `_make_command()`, `generate_commands()`, param normalization (cli_multiple tuple→list), dict param JSON parsing
- [ ] `tests/mcp/test_parity.py` extension — add CLI parity assertions (all non-custom_presentation actions have registered Click commands)
- [ ] `_register_core.py` updates — add `cli_group` assignments to ActionDefinitions currently missing them (query, lifecycle/archive/supersede, reweave, session, check, upgrade, init, vector, export, ingest categories)

---

## Sources

### Primary (HIGH confidence)
- Direct code inspection: `src/ztlctl/mcp/generator.py` — authoritative pattern for registry-iteration-based generation
- Direct code inspection: `src/ztlctl/actions/definitions.py` — ActionParam/ActionDefinition field inventory
- Direct code inspection: `src/ztlctl/actions/_register_core.py` — all 59 ActionDefinitions with CLI metadata
- Direct code inspection: `src/ztlctl/commands/` — all 20+ hand-written command files (scope of replacement)
- Direct code inspection: `src/ztlctl/commands/_context.py` — AppContext.emit() output pipeline
- Direct code inspection: `src/ztlctl/commands/_base.py` — ZtlCommand/ZtlGroup base classes
- Direct code inspection: `tests/mcp/test_parity.py` — parity test structure to extend
- Direct code inspection: `tests/commands/test_graph.py` — CliRunner integration test pattern

### Secondary (MEDIUM confidence)
- Click documentation pattern (click.Option, click.Argument, click.Choice, click.testing.CliRunner) — well-established stable API, no external verification needed given existing codebase usage

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in project, no new dependencies
- Architecture: HIGH — generator pattern is verified in Phase 3 MCP generator; ActionParam fields are explicitly designed for CLI generation
- Pitfalls: HIGH — identified from direct code inspection of existing command implementations and data structures
- Open questions: MEDIUM — cli_group gaps and update command design require planner decisions

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (stable internal codebase; no external library churn)
