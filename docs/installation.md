---
title: Installation
nav_order: 2
---

# Installation

## Quick Install

```bash
pip install ztlctl
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv tool install ztlctl
```

## Optional Extras

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

### Community Algorithms

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

## Requirements

- **Python 3.13+**
- SQLite with FTS5 support (included in standard Python builds)
