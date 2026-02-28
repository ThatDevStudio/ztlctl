# ZettelControl (ztlctl)

[![CI](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml/badge.svg)](https://github.com/ThatDevStudio/ztlctl/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/ztlctl)](https://pypi.org/project/ztlctl/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://thatdevstudio.github.io/ztlctl/)

**ZettelControl** (`ztlctl`) is a CLI utility and agentic note-taking ecosystem that combines zettelkasten, second-brain, and knowledge-garden paradigms into a single tool designed for both human users and AI agents.

ztlctl manages your knowledge vault as structured markdown files backed by a SQLite index, connected through a weighted knowledge graph, and accessible via CLI, MCP server, or direct Python API.

## Installation

```bash
pip install ztlctl
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ztlctl
```

Optional extras: `pip install ztlctl[mcp]` (MCP server), `pip install ztlctl[semantic]` (vector search), `pip install ztlctl[community]` (advanced graph algorithms).

See the [Installation Guide](docs/installation.md) for details.

## Quick Start

```bash
# 1. Initialize a new vault
ztlctl init my-vault --topics "python,architecture,devops"

# 2. Enter the vault directory
cd my-vault

# 3. Start a research session
ztlctl agent session start "Learning Python async patterns"

# 4. Create notes as you learn
ztlctl create note "Asyncio Event Loop" --tags "lang/python,concept/concurrency"
ztlctl create note "Async vs Threading" --tags "lang/python,concept/concurrency"

# 5. Create references to external sources
ztlctl create reference "Python asyncio docs" --url "https://docs.python.org/3/library/asyncio.html"

# 6. Track tasks that emerge
ztlctl create task "Refactor API to use async" --priority high --impact high

# 7. Let the graph grow — reweave discovers connections
ztlctl reweave --auto-link-related

# 8. Search your knowledge
ztlctl query search "async patterns" --rank-by relevance

# 9. Close the session when done
ztlctl agent session close --summary "Mapped async patterns, identified refactoring task"
```

## Features

- **4 content types** with enforced lifecycle state machines — notes, references, tasks, and session logs ([Core Concepts](docs/concepts.md))
- **Knowledge graph** with 4-signal reweave scoring (BM25, tag overlap, graph proximity, topic match) for automated link discovery ([Tutorial](docs/tutorial.md))
- **Session-based agentic workflows** with token-budgeted 5-layer context assembly ([Agentic Workflows](docs/agentic-workflows.md))
- **Digital garden maturity** tracking — seed, budding, and evergreen stages ([Knowledge Paradigms](docs/paradigms.md))
- **Full-text + semantic search** with BM25/vector hybrid ranking and three ranking modes ([Command Reference](docs/commands.md))
- **MCP server** with 12 tools, 6 resources, and 4 prompts for AI client integration ([MCP Server](docs/mcp.md))
- **Export** to markdown, indexes, and graph formats (DOT, JSON) ([Tutorial](docs/tutorial.md#step-8-export-and-share))
- **Plugin system** via pluggy event bus with built-in git integration ([Development](docs/development.md))
- **Structured JSON output** on every command for scripting and agent consumption (`--json` flag)
- **Vault integrity** checking, auto-fix, full rebuild, and rollback ([Troubleshooting](docs/troubleshooting.md))

## Documentation

| Guide | Description |
|-------|-------------|
| [Installation](docs/installation.md) | Install via pip/uv, optional extras |
| [Quick Start](docs/quickstart.md) | Your first vault in 9 commands |
| [Tutorial](docs/tutorial.md) | Step-by-step vault building guide |
| [Core Concepts](docs/concepts.md) | Content types, lifecycle, vault structure, graph |
| [Command Reference](docs/commands.md) | All CLI commands, options, and filters |
| [Configuration](docs/configuration.md) | `ztlctl.toml` settings and environment variables |
| [Agentic Workflows](docs/agentic-workflows.md) | Sessions, context assembly, batch, scripting |
| [Knowledge Paradigms](docs/paradigms.md) | Zettelkasten, second brain, digital garden |
| [MCP Server](docs/mcp.md) | Model Context Protocol integration |
| [Development](docs/development.md) | Contributing, architecture, local setup |
| [Troubleshooting](docs/troubleshooting.md) | Common issues and solutions |

Full documentation is also available at [thatdevstudio.github.io/ztlctl](https://thatdevstudio.github.io/ztlctl/).

## Architecture

ztlctl follows a strict 6-layer package structure where dependencies flow downward:

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

See [Development](docs/development.md) for details and [DESIGN.md](DESIGN.md) for the complete internal design specification.

## Contributing

This project uses [conventional commits](https://www.conventionalcommits.org/). See [CONTRIBUTING.md](CONTRIBUTING.md) for the full guide.

1. Branch from `develop`: `git checkout -b feature/<name> develop`
2. Make changes and commit with conventional messages
3. Open a PR targeting `develop`
4. Releases are automated when `develop` is merged to `main`

## Community

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [Support](SUPPORT.md)

## License

[MIT](LICENSE)
