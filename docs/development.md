---
title: Development
---

# Development

## Setup

```bash
# Clone the repository
git clone https://github.com/ThatDevStudio/ztlctl.git
cd ztlctl

# Install all development dependencies
uv sync --group dev

# Verify the installation
uv run ztlctl --version

# Run the test suite
uv run pytest
```

## Development Commands

```bash
uv run ztlctl --help                             # Run the CLI
uv run pytest --cov --cov-report=term-missing    # Tests with coverage
uv run ruff check .                              # Lint
uv run ruff format .                             # Format
uv run mypy src/                                 # Type check
uv run pre-commit run --all-files                # All pre-commit hooks
```

## CI/CD Pipeline

GitHub Actions exposes two CI/CD workflows:

- `PR CI` runs on pull requests to `develop` and exposes the required `Validate PR` check.
- `Release Pipeline` runs only after changes land on `develop`, then performs merge validation,
  release, publish, and Homebrew sync as dependent jobs.

`Validate PR` covers lint, format, type checking, package build, security audit, the full pytest
suite, the MCP stdio integration test, and commit lint. `Validate Merge` in the release pipeline
re-runs the merge validation after landing on `develop` and adds the semantic CI smoke test using
the lightweight internal `semantic-ci` dependency group.

The release workflow builds `dist/release-manifest.json` and treats it as the source of truth
for release version, tag, asset path, download URL, and source tarball hash. Downstream publish
and Homebrew steps consume that manifest instead of rediscovering release metadata.

## Homebrew Formula

The Homebrew tap publishes `ztlctl` at `ThatDev/ztlctl`.

```bash
# Build release assets for an existing tag
python3 scripts/build_release_manifest.py --release-tag v1.7.1 --output dist/release-manifest.json

# Generate the Homebrew formula from the release manifest
python3 scripts/update_homebrew_formula.py --manifest dist/release-manifest.json --output dist/ztlctl.rb
```

The formula is now a derived release artifact rather than a checked-in source file. It uses the
release tarball as the stable source, installs the CLI into a Python virtualenv, and derives both
runtime and build-backend resources from the repository's `uv.lock`.

## Architecture

ztlctl follows a strict 6-layer package structure where dependencies flow downward:

```
commands → output → services → config/infrastructure → domain
```

```
src/ztlctl/
├── domain/          # Types, enums, lifecycle rules, ID patterns
├── infrastructure/  # SQLite/SQLAlchemy, NetworkX graph, filesystem
├── config/          # Pydantic config models, TOML discovery
├── services/        # Business logic (create, query, graph, reweave, ...)
├── output/          # Rich/JSON formatters
├── commands/        # Click CLI commands
├── plugins/         # Pluggy hook specs and built-in plugins
├── mcp/             # MCP server adapter
└── templates/       # Jinja2 templates for content creation
```

For the complete internal design specification (architecture decisions, invariants, implementation details), see [DESIGN.md](https://github.com/ThatDevStudio/ztlctl/blob/develop/DESIGN.md) in the repository.

### Action Model

ztlctl uses a 4-layer action model that connects user-facing surfaces (CLI, MCP) to service logic:

| Layer | Components | Role |
|-------|-----------|------|
| **Data** | `ActionParam`, `ActionDefinition` | Frozen dataclasses describing an action's name, params, side effect, and surface metadata |
| **Service** | `*Service` classes | Business logic that executes the action and returns a `ServiceResult` |
| **Controller** | `BaseController` subclasses | Wires one `ActionDefinition` to one `Service` call; handles input coercion and error wrapping |
| **Registry** | `ActionRegistry` (singleton) | Indexed map of all registered `ActionDefinition` objects; queried at startup |

**How CLI auto-generation works:**
At startup, the CLI generator calls `get_action_registry().list_actions(category=...)` for each command group. It iterates the returned `ActionDefinition` objects and builds Click commands from `ActionParam` metadata (`cli_is_argument`, `cli_flag`, `cli_multiple`, `cli_name`). No code generation — the CLI surface is driven entirely by the registry at import time.

**How MCP auto-generation works:**
The MCP adapter calls `get_action_registry().list_actions()` and converts each `ActionDefinition` into an MCP tool descriptor using `mcp_when_to_use`, `mcp_avoid_when`, `mcp_common_errors`, and `mcp_example` fields. Same registry, different surface formatter.

**Plugin integration points:**
1. `pre_action` fires before the Controller calls the Service — plugins can abort (return `ActionRejection`) or transform kwargs
2. `post_action` fires after the Controller returns the `ServiceResult` — all plugins receive the call regardless of success/failure
3. `register_note_types()` returns `NoteTypeDefinition` objects — PluginManager creates `ActionDefinition` entries in the registry for CRUD operations on each custom type
4. `register_content_models()` extends the `CONTENT_REGISTRY` so new note subtypes are recognized by `CreateService`

**ServiceResult contract:**
Every Service method returns `ServiceResult`. Controllers unwrap it to emit exit codes (CLI) or structured responses (MCP). Plugins receive the raw `ServiceResult` via `post_action(result=...)`.

## Template Overrides

Vault-specific Jinja2 overrides can live under `.ztlctl/templates/`.

- Self-document templates: `.ztlctl/templates/self/identity.md.j2` or `.ztlctl/templates/identity.md.j2`
- Content body templates: `.ztlctl/templates/content/note.md.j2` or `.ztlctl/templates/note.md.j2`

ztlctl checks those override paths first and falls back to the bundled package templates when no user template exists.

## Workflow Templates

`ztlctl workflow init` and `ztlctl workflow update` scaffold vault workflow guidance using a packaged Copier template.

- Choices: source control (`git|none`), profile (dynamic installed profile ids, with deprecated `none` and `vanilla` aliases resolving to `core`), workflow (`claude-driven|agent-generic|manual`), skill set (`research|engineering|minimal`)
- Answers file: `.ztlctl/workflow-answers.yml`
- Generated guidance: `.ztlctl/workflow/`

`ztlctl init` applies the default workflow scaffold automatically unless `--no-workflow` is passed.

## Plugin Init Hooks

Plugins can now contribute ordered init steps through `register_vault_init_steps()`.

- Each step receives a normalized `VaultInitContext`
- Steps can create files, emit warnings, and return structured setup instructions
- `ztlctl init` aggregates those instructions into the result payload and prints them under `Next steps`
- The first-party Obsidian profile plugin uses this surface to scaffold `.obsidian/`, seed `garden/`, and print plugin-install guidance before handing `.obsidian/` off to the user for further customization

Legacy `WorkspaceProfileContribution.init_scaffold` remains supported temporarily and is wrapped into the same ordered init pipeline for compatibility.

## Further Reading

- [Plugin Authoring Guide](plugin-guide.md) — build plugins with hookspecs, custom note types, and capability declarations
- [API Reference](api-reference.md) — auto-generated reference for `ActionDefinition`, `ActionRegistry`, hookspecs, and plugin contracts

## Contributing

See [CONTRIBUTING.md](https://github.com/ThatDevStudio/ztlctl/blob/develop/CONTRIBUTING.md) for the full contribution guide, including:

- Branching model and PR workflow
- Conventional commit format
- Pre-submit checklist
- Code standards and dependency management
- Dependency management (always use `uv add`, never `uv pip install`)
