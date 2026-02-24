# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ztlctl** (Zettelkasten Control) is a CLI utility for managing a Zettelkasten note-taking system. It is an agentic note-taking ecosystem leveraging zettelkasten, second-brain, and knowledge-garden paradigms — designed for both human users and AI agents to leverage.

- **Repository**: github.com/ThatDevStudio/ztlctl
- **Main branch**: `develop`

## Tech Stack

- **Language**: Python 3.13
- **Package manager**: uv
- **CLI framework**: Click
- **Linting/formatting**: ruff
- **Commit convention**: Commitizen (conventional commits)
- **Versioning**: Semantic versioning via `cz bump`

## Development Commands

```bash
uv sync --group dev                      # install all dev dependencies
uv run ztlctl                            # run the CLI
uv run pytest                            # run all tests
uv run pytest path/to/test.py::test_name # run single test
uv run ruff check .                      # lint
uv run ruff format .                     # format
uv run mypy src/                         # type check
uv run pre-commit run --all-files        # run all pre-commit hooks
uv run cz check --message "feat: msg"   # validate a commit message
```

## Git Workflow

### Branching Model

| Branch | Purpose | Merges to |
|---|---|---|
| `main` | Production releases (every merge = tagged release) | — |
| `develop` | Integration branch (default, PR target) | `main` |
| `feature/<name>` | New features | `develop` |
| `fix/<name>` | Bug fixes | `develop` |
| `hotfix/<name>` | Urgent production fixes | `main` AND `develop` |

### Conventional Commits

All commit messages MUST follow the conventional commits format:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

**Types and version effects:**

| Type | Version bump | Description |
|---|---|---|
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

### Feature Development Workflow

1. Branch from develop: `git checkout -b feature/<name> develop`
2. Commit with conventional format: `git commit -m "feat(scope): description"`
3. Push and create PR to develop: `gh pr create --base develop`
4. After CI passes, squash-merge to develop
5. When ready to release: PR from `develop` to `main`
6. Automation handles: version bump, changelog, tag, GitHub Release, PyPI publish

### Hotfix Workflow

1. Branch from main: `git checkout -b hotfix/<name> main`
2. Fix and commit: `git commit -m "fix(scope): description"`
3. PR to `main` (triggers release after merge)
4. After release, merge `main` back into `develop` to sync the version bump

### What NOT to Do

- **Don't commit directly to `main` or `develop`** — always use PRs
- **Don't use non-conventional commit messages** — pre-commit hook and CI will reject them
- **Don't manually edit version numbers** — `cz bump` manages `pyproject.toml` and `src/ztlctl/__init__.py`
- **Don't manually edit CHANGELOG.md** — `cz bump --changelog` generates it
- **Don't create git tags manually** — the release workflow creates annotated tags
- **Don't push to `main` directly** — merge via PR from `develop` or `hotfix/*`

## CI/CD Pipeline

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR/push to `develop` or `main` | Lint, test, typecheck, security audit, commit lint |
| `release.yml` | Push to `main` | Version bump, changelog, annotated tag, GitHub Release |
| `publish.yml` | GitHub Release published | Build and publish to PyPI via OIDC |

## Architecture

- Click-based CLI with entry point: `ztlctl`
- Project is in early scaffolding phase
