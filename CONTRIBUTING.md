# Contributing to ztlctl

Thank you for your interest in contributing to ztlctl! This guide covers everything you need to get started.

## Table of Contents

- [Development Setup](#development-setup)
- [Project Architecture](#project-architecture)
- [Branching Model](#branching-model)
- [Making Changes](#making-changes)
- [Conventional Commits](#conventional-commits)
- [Pre-Submit Checklist](#pre-submit-checklist)
- [Pull Request Requirements](#pull-request-requirements)
- [Code Standards](#code-standards)
- [Adding Dependencies](#adding-dependencies)
- [License](#license)

## Development Setup

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** — package manager and task runner
- **Git** — version control

### Getting Started

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

## Project Architecture

ztlctl follows a strict 6-layer package structure where dependencies flow downward:

```
commands → output → services → config/infrastructure → domain
```

| Layer | Directory | Purpose |
|-------|-----------|---------|
| Domain | `src/ztlctl/domain/` | Types, enums, lifecycle rules, ID patterns |
| Infrastructure | `src/ztlctl/infrastructure/` | SQLite/SQLAlchemy, NetworkX graph, filesystem |
| Config | `src/ztlctl/config/` | Pydantic config models, TOML discovery |
| Services | `src/ztlctl/services/` | Business logic (create, query, graph, reweave, ...) |
| Output | `src/ztlctl/output/` | Rich/JSON formatters |
| Commands | `src/ztlctl/commands/` | Click CLI commands |

Additional packages: `plugins/` (pluggy hook specs), `mcp/` (MCP adapter), `templates/` (Jinja2).

For the complete design specification, see [DESIGN.md](DESIGN.md).

## Branching Model

| Branch | Purpose | Merges to |
|--------|---------|-----------|
| `develop` | Trunk — all development and releases | — |
| `feature/<name>` | New features | `develop` |
| `fix/<name>` | Bug fixes | `develop` |

**Important:**
- Never commit directly to `develop`
- Always work on feature/fix branches created from `develop`
- PRs always target `develop`

## Making Changes

1. **Pull latest develop:**
   ```bash
   git checkout develop && git pull origin develop
   ```

2. **Create a feature or fix branch:**
   ```bash
   git checkout -b feature/<name>   # for new features
   git checkout -b fix/<name>       # for bug fixes
   ```

3. **Make changes** in small, focused commits with conventional messages.

4. **Run the full validation suite** (see [Pre-Submit Checklist](#pre-submit-checklist)).

5. **Push and create a PR:**
   ```bash
   git push -u origin feature/<name>
   ```

## Conventional Commits

All commit messages **and PR titles** must follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

PR titles use the same format because squash-merges use the PR title as the final commit message.

### Types and Version Effects

| Type | Version Bump | Description |
|------|-------------|-------------|
| `feat` | MINOR (0.x.0) | New feature |
| `fix` | PATCH (0.0.x) | Bug fix |
| `feat!` / `BREAKING CHANGE:` | MAJOR (x.0.0) | Breaking change |
| `docs` | None | Documentation only |
| `style` | None | Formatting, whitespace |
| `refactor` | None | Code change that neither fixes nor adds |
| `test` | None | Adding or updating tests |
| `ci` | None | CI/CD changes |
| `build` | None | Build system or dependencies |
| `chore` | None | Maintenance tasks |

### Examples

```
feat(graph): add bridge detection algorithm
fix(reweave): prevent duplicate edges on re-run
docs: update configuration reference
test(query): add decision-support edge cases
refactor(services): extract base service class
```

## Pre-Submit Checklist

Run all four checks before pushing:

```bash
uv run ruff check .              # Lint
uv run ruff format --check .     # Format check
uv run pytest                    # Tests
uv run mypy src/                 # Type check
```

Or as a single command:

```bash
uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/
```

All four must pass — CI enforces the same checks.

## Pull Request Requirements

- **Title**: Must use conventional commit format (e.g., `feat(graph): add bridge detection`)
- **Target**: `develop` branch
- **CI**: All checks must pass (lint, test, typecheck, security audit, commit lint)
- **Scope**: Keep PRs focused — one feature or fix per PR

## Code Standards

- **Line length**: 100 characters (enforced by ruff)
- **Type checking**: mypy strict mode — all public APIs must have type annotations
- **Linting/formatting**: ruff (configured in `pyproject.toml`)
- **Service contract**: All service-layer methods return `ServiceResult` — the unified contract consumed by CLI, MCP, and any future interface
- **Tests**: New features and bug fixes should include tests

## Adding Dependencies

Always use `uv add`:

```bash
# Runtime dependency
uv add <package>

# Development dependency (specify the group)
uv add --group dev <package>
uv add --group test <package>
uv add --group lint <package>
```

Never use `uv pip install` or `pip install` directly — dependency management goes through `pyproject.toml`.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
