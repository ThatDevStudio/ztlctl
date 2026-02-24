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
```

## Git Workflow

- The default branch is `develop`, not `main`
- Target PRs against `develop`

## Architecture

- Click-based CLI with entry point: `ztlctl`
- Project is in early scaffolding phase
