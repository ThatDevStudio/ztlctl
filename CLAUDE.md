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

### Feature Development Lifecycle

1. **Pull latest develop:**
   ```bash
   git checkout develop && git pull origin develop
   ```
2. **Create feature/fix branch from develop** — never stack branches on unmerged work:
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
6. **Wait for all CI workflows to pass** — check with `gh pr checks <number> --watch`. If any check fails, fix the issue, push, and wait again. Only declare the PR ready for review once ALL checks are green.
7. **User reviews, approves, and squash-merges** — address review feedback with additional commits
8. **Watch the release pipeline after merge** — check with `gh run list --branch develop`. If the release pipeline fails, create a `fix/*` branch from develop, fix the issue, and open a new PR (repeating steps 4-7).
9. **Publish gate** — once the GitHub Release is created, the publish workflow triggers (PyPI, manual approval). Notify the user that publish is ready for approval. User approves or says "skip".
10. **Cleanup** — only after publish approval/skip, delete all involved branches (feature + any fix branches) locally and remotely, then pull develop:
    ```bash
    git checkout develop && git pull origin develop
    git branch -D feature/<name> && git push origin --delete feature/<name>
    ```

**Do NOT use git worktrees** — work directly on feature/fix branches in the main repo checkout.

### What NOT to Do

- **Don't commit directly to `develop`** — always use feature/fix branches with PRs
- **Don't stack branches** — never create a branch on top of an unmerged branch; always branch from develop
- **Don't declare a PR ready before CI passes** — wait for all workflows to complete successfully
- **Don't consider work done after merge** — watch the release pipeline and fix failures before moving on
- **Don't use non-conventional commit messages** — pre-commit hook and CI will reject them
- **Don't use non-conventional PR titles** — squash-merge uses the PR title as the commit message
- **Don't manually edit version numbers** — `cz bump` manages `pyproject.toml` and `src/ztlctl/__init__.py`
- **Don't manually edit CHANGELOG.md** — `cz bump --changelog` generates it
- **Don't create git tags manually** — the release workflow creates annotated tags
- **Don't merge PRs** — the user reviews and merges; Claude only creates PRs and addresses feedback
- **Don't use git worktrees** — work directly on feature/fix branches
- **Don't use `uv pip install`** — always use `uv add` (or `uv add --group <group>` for dev deps)
- **Don't leave stale branches** — delete all branches (feature + fix) after publish approval/skip

## CI/CD Pipeline

| Workflow | Trigger | Purpose |
|---|---|---|
| `pr-ci.yml` | PR to `develop` | Lint, test, typecheck, security audit, commit lint |
| `release-pipeline.yml` | Push to `develop` | Validate → version bump → changelog → tag → GitHub Release → PyPI publish (manual approval) → Homebrew tap sync |

## Documentation Rules

**Rule:** If a PR adds or modifies actions, commands, config options, or MCP resources, the same PR MUST update the relevant docs.

### Docs Update Checklist

Before marking a PR ready for review, verify all that apply:

- [ ] Relevant docs page updated (new feature, changed behavior, new config option)
- [ ] `docs/llms.txt` entry current (new page added, stale description corrected)
- [ ] CLI examples verified against `uv run ztlctl <command> --help` (flag names from source)
- [ ] MCP tool count accurate in `docs/mcp.md` if tools were added or removed

**Where to find things:**
- User-facing docs: `docs/` directory, registered in `mkdocs.yml` nav
- LLM index: `docs/llms.txt` and `docs/llms-full.txt` (hand-maintained)
- Command reference: `docs/commands.md`
- MCP reference: `docs/mcp.md`

### GSD Phase Documentation Convention (DINF-03)

Every GSD feature phase plan MUST include a Documentation Tasks block. When planning a phase that adds or changes user-facing behavior, include at least one task that updates the relevant docs page, llms.txt entry, and command examples. This is structural — not optional.

### Documentation Conventions

Quality standards for all docs pages. Enforced by review — Vale and pymarkdownlnt catch structural violations.

**CLI syntax (Google developer style):**
- Optional arguments: `[--flag VALUE]`
- Required arguments: `REQUIRED`
- Shell prompts: use bare `ztlctl` in inline references, `$ ztlctl` only in standalone code blocks
- Flag names must match `uv run ztlctl <command> --help` output exactly — never from memory

**Admonition taxonomy (3 types only):**
- `!!! warning` — danger, breaking changes, data loss risks
- `!!! note` — context, background information, important caveats
- `!!! tip` — recommendations, best practices, efficiency suggestions

Do not use `info`, `danger`, `example`, `abstract`, or other admonition types. Three types keep the signal clear.

**Cross-referencing:**
- Every page ends with a "What's next" section containing 2-3 links to related pages
- Use relative Markdown links: `[Page title](page.md)` (not absolute URLs)
- Link text should be the target page's title, not "click here" or "see this"

**Headings:**
- Sentence case (e.g., "Getting started" not "Getting Started") — consistent with Vale Google style
- H1 is the page title (one per page), H2 for major sections, H3 for subsections

**Diataxis content types:**
- Tutorial: learning-oriented, guided experience ("Follow along to...")
- How-to: task-oriented, goal-driven ("How to configure...")
- Reference: information-oriented, complete catalog ("All available commands...")
- Explanation: understanding-oriented, conceptual ("Why ztlctl uses...")
- Do not mix types in a single page — if a page serves two purposes, split or pick the primary purpose

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
