---
title: Development
nav_order: 11
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

## Template Overrides

Vault-specific Jinja2 overrides can live under `.ztlctl/templates/`.

- Self-document templates: `.ztlctl/templates/self/identity.md.j2` or `.ztlctl/templates/identity.md.j2`
- Content body templates: `.ztlctl/templates/content/note.md.j2` or `.ztlctl/templates/note.md.j2`

ztlctl checks those override paths first and falls back to the bundled package templates when no user template exists.

## Workflow Templates

`ztlctl workflow init` and `ztlctl workflow update` scaffold vault workflow guidance using a packaged Copier template.

- Choices: source control (`git|none`), viewer (`obsidian|vanilla`), workflow (`claude-driven|agent-generic|manual`), skill set (`research|engineering|minimal`)
- Answers file: `.ztlctl/workflow-answers.yml`
- Generated guidance: `.ztlctl/workflow/`

`ztlctl init` applies the default workflow scaffold automatically unless `--no-workflow` is passed.

## Contributing

See [CONTRIBUTING.md](https://github.com/ThatDevStudio/ztlctl/blob/develop/CONTRIBUTING.md) for the full contribution guide, including:

- Branching model and PR workflow
- Conventional commit format
- Pre-submit checklist
- Code standards and dependency management
