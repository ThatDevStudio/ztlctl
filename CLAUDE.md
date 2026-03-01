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

### Roles

**Claude (you):**
- Create `feature/*` or `fix/*` branches from `develop`
- Write code and commit with conventional commit messages
- Push branches and create PRs targeting `develop`
- PR titles MUST use conventional commit format (see below)
- Address review feedback on open PRs

**User (human):**
- Reviews PRs, approves, and merges (squash-merge)

**Automation (CI/CD):**
- Runs lint, test, typecheck, security, commit-lint on every PR
- On merge to `develop`: if version-bumping commits exist, bumps version, updates changelog, creates tag + GitHub Release
- On GitHub Release: builds and publishes to PyPI (manual approval)

### Branching Model

| Branch | Purpose | Merges to |
|---|---|---|
| `develop` | Trunk — all development and releases | — |
| `feature/<name>` | New features | `develop` |
| `fix/<name>` | Bug fixes | `develop` |

### Conventional Commits

All commit messages AND PR titles MUST follow the conventional commits format:

```
<type>(<optional scope>): <description>

[optional body]

[optional footer(s)]
```

**PR titles must also use this format** because squash-merges use the PR title as the commit message. Example: `feat(notes): add zettel linking command`

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

1. **Pull latest develop** — if diverged, reset to match origin:
   ```bash
   git checkout develop && git pull origin develop
   ```
2. **Create feature/fix branch:**
   ```bash
   git checkout -b feature/<name>
   ```
3. **Work in small, frequent commits** using conventional messages
4. **Run full validation before PR:**
   ```bash
   uv run ruff check . && uv run ruff format --check . && uv run pytest && uv run mypy src/
   ```
   Fix any issues and commit fixes.
5. **Push and create PR to develop:**
   ```bash
   git push -u origin feature/<name>
   gh pr create --base develop --title "feat(scope): description"
   ```
   Provide the PR link for the user to review.
6. **Address review feedback** — push additional commits to the same branch
7. Wait for user to review, approve, and squash-merge

**Do NOT use git worktrees** — work directly on feature/fix branches in the main repo checkout.

### Post-Release

After a version-bumping merge, the release workflow pushes a version bump commit directly to `develop`. Pull before starting new work:

```bash
git checkout develop && git pull origin develop
```

### What NOT to Do

- **Don't commit directly to `develop`** — always use feature/fix branches with PRs
- **Don't use non-conventional commit messages** — pre-commit hook and CI will reject them
- **Don't use non-conventional PR titles** — squash-merge uses the PR title as the commit message
- **Don't manually edit version numbers** — `cz bump` manages `pyproject.toml` and `src/ztlctl/__init__.py`
- **Don't manually edit CHANGELOG.md** — `cz bump --changelog` generates it
- **Don't create git tags manually** — the release workflow creates annotated tags
- **Don't merge PRs** — the user reviews and merges; Claude only creates PRs and addresses feedback
- **Don't use git worktrees** — work directly on feature/fix branches
- **Don't use `uv pip install`** — always use `uv add` (or `uv add --group <group>` for dev deps)

## CI/CD Pipeline

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | PR/push to `develop` | Lint, test, typecheck, security audit, commit lint |
| `release.yml` | Push to `develop` | Auto version bump, changelog, tag, GitHub Release (if version-bumping commits) |
| `publish.yml` | GitHub Release published | Build and publish to PyPI via OIDC (manual approval) |

## Architecture

- **Entry point**: `ztlctl` (Click CLI)
- **6-layer package structure** under `src/ztlctl/`:
  - `domain/` — types, enums, lifecycle rules, ID patterns (no external deps beyond pydantic)
  - `infrastructure/` — SQLite/SQLAlchemy Core, NetworkX graph engine, filesystem ops
  - `config/` — Pydantic config models, TOML discovery/loading
  - `services/` — business logic (imports domain, infrastructure, config)
  - `output/` — Rich/JSON formatters (imports services)
  - `commands/` — Click command groups/commands (imports services, output, config)
  - `plugins/` — pluggy hook specs and built-in plugins
  - `mcp/` — optional MCP adapter (guarded imports)
  - `templates/` — Jinja2 templates for content creation
