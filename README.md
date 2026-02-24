# ztlctl

Zettelkasten Control — CLI utility for managing a Zettelkasten note-taking system.

An agentic note-taking ecosystem leveraging zettelkasten, second-brain, and knowledge-garden paradigms — designed for both human users and AI agents to leverage.

## Installation

```bash
uv sync
```

## Usage

```bash
ztlctl --help
ztlctl --version
```

## Development

```bash
uv sync --group dev                      # install all dev dependencies
uv run ztlctl --help                     # run the CLI
uv run pytest --cov --cov-report=term-missing  # run tests with coverage
uv run ruff check .                      # lint
uv run ruff format .                     # format
uv run mypy src/                         # type check
uv run pre-commit run --all-files        # run all pre-commit hooks
```

## License

MIT
