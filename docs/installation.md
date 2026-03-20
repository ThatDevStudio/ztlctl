---
title: Installation
---

# Installation

## System Requirements

- **Python 3.13+** (required — `requires-python = ">=3.13"`)
- SQLite with FTS5 support (included in all standard Python 3.13 builds)
- Operating system: Linux, macOS, or Windows

## Install Methods

### pip

```bash
pip install ztlctl
```

### uv (recommended for isolated installs)

```bash
uv tool install ztlctl
```

`uv tool install` places `ztlctl` on your PATH as an isolated tool — no virtual environment management needed.

### pipx

```bash
pipx install ztlctl
```

### Homebrew (macOS)

```bash
brew tap ThatDev/ztlctl
brew install ThatDev/ztlctl/ztlctl
```

The Homebrew formula installs the base CLI. Optional extras (MCP support, semantic search) are not available through Homebrew — install them via pip or uv after the base install.

## Optional Extras

Install extras alongside the base package to unlock additional capabilities.

### MCP Server Support

For [Model Context Protocol](mcp.md) integration with AI clients like Claude Desktop:

```bash
pip install ztlctl[mcp]
```

### Semantic Search

For vector-based similarity search using sentence-transformers:

```bash
pip install ztlctl[semantic]
```

### Community Detection Algorithms

For advanced graph algorithms (Leiden community detection):

```bash
pip install ztlctl[community]
```

### All Extras

```bash
pip install ztlctl[mcp,semantic,community]
```

## Verify Installation

```bash
ztlctl --version
```

Expected output:

```
ztlctl, version 1.16.0
```

Run a help check to confirm all commands are registered:

```bash
ztlctl --help
```

## Development Install

To contribute to ztlctl or run the test suite locally:

```bash
git clone https://github.com/ThatDevStudio/ztlctl.git
cd ztlctl
uv sync --group dev
```

This installs all runtime dependencies plus the dev group (pytest, mypy, ruff, pre-commit, mkdocs).

Verify the dev install:

```bash
uv run ztlctl --version
uv run pytest --tb=short -q
```

## Upgrading

```bash
# pip
pip install --upgrade ztlctl

# uv tool
uv tool upgrade ztlctl

# Homebrew
brew upgrade ThatDev/ztlctl/ztlctl
```

## Next Steps

Run `ztlctl init` to create your first vault, then follow the [Quick Start](quickstart.md) guide.
