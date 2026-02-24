# ztlctl

[![CI](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/ztlctl)](https://pypi.org/project/ztlctl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Zettelkasten Control — CLI utility for managing a Zettelkasten note-taking system.

An agentic note-taking ecosystem leveraging zettelkasten, second-brain, and knowledge-garden paradigms — designed for both human users and AI agents to leverage.

## Installation

```bash
pip install ztlctl
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ztlctl
```

## Usage

```bash
ztlctl --help
ztlctl --version
```

## Development

```bash
uv sync --group dev                              # install all dev dependencies
uv run ztlctl --help                             # run the CLI
uv run pytest --cov --cov-report=term-missing    # run tests with coverage
uv run ruff check .                              # lint
uv run ruff format .                             # format
uv run mypy src/                                 # type check
uv run pre-commit run --all-files                # run all pre-commit hooks
```

## Contributing

This project uses [conventional commits](https://www.conventionalcommits.org/). All commit messages and PR titles must follow the format:

```
<type>(<scope>): <description>
```

Common types: `feat`, `fix`, `docs`, `test`, `refactor`, `ci`, `chore`

### Workflow

1. Branch from `develop`: `git checkout -b feature/<name> develop`
2. Make changes and commit with conventional messages
3. Open a PR targeting `develop`
4. Releases are automated when `develop` is merged to `main`

## License

[MIT](LICENSE)
