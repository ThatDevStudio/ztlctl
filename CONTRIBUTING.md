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
| `codex/<name>` | Focused work branch for features, fixes, and CI changes | `develop` |

**Important:**
- Never commit directly to `develop`
- Always work on feature/fix branches created from `develop`
- PRs always target `develop`
- Branch protection requires the `Validate PR` status check before merge

## Making Changes

1. **Pull latest develop:**
   ```bash
   git checkout develop && git pull --ff-only origin develop
   ```

2. **Create a feature or fix branch:**
   ```bash
   git checkout -b codex/<name>     # preferred local branch naming
   ```

3. **Make changes** in small, focused commits with conventional messages.

4. **Run the PR validation suite** (see [Pre-Submit Checklist](#pre-submit-checklist)).

5. **Push and create a PR:**
   ```bash
   git push -u origin codex/<name>
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

The `PR CI` workflow exposes a single required `Validate PR` status. Before pushing, run the
closest local equivalent:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest --cov --cov-report=term-missing
uv build
uvx pip-audit
uv sync --group test --extra mcp
uv run pytest tests/mcp/test_stdio_integration.py -q
uv run cz check --rev-range origin/develop..HEAD
```

After merging to `develop`, the `Release Pipeline` workflow runs the merge validation profile
before any release activity:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest --cov --cov-report=term-missing
uv build
uvx pip-audit
uv sync --group test --extra mcp
uv run pytest tests/mcp/test_stdio_integration.py -q
uv sync --group test --group semantic-ci
uv run pytest tests/integration/test_semantic_extra.py -q
```

## Pull Request Requirements

- **Title**: Must use conventional commit format (e.g., `feat(graph): add bridge detection`)
- **Target**: `develop` branch
- **CI**: The `Validate PR` workflow check must pass
- **Scope**: Keep PRs focused — one feature or fix per PR

## Release Recovery

Releases are created by the `Release Pipeline` workflow after `Validate Merge` passes on
`develop`. The workflow builds a `release-manifest.json` file and uses it as the source of truth
for release version, tag, tarball path, download URL, and source hash.

If a release partially succeeds after tag creation, recover it with a manual workflow dispatch:

```text
Workflow: Release Pipeline
Input: release_tag=vX.Y.Z
```

Recovery mode rebuilds the manifest from the existing tag, re-uploads release assets if needed,
retries PyPI publish safely when the version is absent, and re-syncs the Homebrew tap only when
the generated formula differs.

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
