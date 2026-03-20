# Stack Research

**Domain:** Documentation site + agent accessibility layer for a Python CLI/MCP tool (ztlctl v2.1)
**Researched:** 2026-03-20
**Confidence:** HIGH

> This document covers NEW stack additions for v2.1. The existing stack (Python 3.13,
> Click, pluggy, Pydantic, FastMCP via `mcp` package) is established and unchanged.
> The Jekyll + Just the Docs GitHub Pages pipeline is also established — do not replace it.

---

## What Already Exists (Do Not Re-Research)

| Existing Capability | Status |
|---------------------|--------|
| Jekyll + `remote_theme: just-the-docs/just-the-docs` | Deployed; GitHub Pages auto-deploys `docs/` on push to `develop` |
| `docs/_config.yml` with `search_enabled: true` | Built-in Just the Docs JS search, already working |
| 16 `.md` files in `docs/` | In place |
| `src/ztlctl/mcp/resources.py` with `ztlctl://` URIs and `_impl` pattern | In place; the doc search resource follows this pattern exactly |
| Click command groups under `src/ztlctl/commands/` | In place; `ztlctl docs` is a new command group here |

---

## Recommended Stack — New Additions Only

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Just the Docs front matter (`parent:`, `nav_order:`, `has_children:`) | current remote theme (no version pin needed) | Multi-audience navigation sections (User Guide vs Developer Guide) | Zero new dependency. Pure front matter configuration. Current Just the Docs (v0.5+) supports unlimited nesting depth: set `parent: User Guide` on child pages and the theme builds the nav tree automatically. `has_children: true` is now redundant — omit it. `nav_order:` controls ordering within a section |
| griffe2md | 1.4.0 (2026-03-06) | Auto-generate API reference Markdown from Python docstrings + type annotations | Only maintained tool that does AST-based Python extraction (no import/runtime required) AND outputs Markdown (not HTML). Outputs files suitable for dropping into `docs/developer-guide/`. Actively maintained (17 releases, latest 2026-03-06). Uses Griffe 1.x — the same extraction engine behind mkdocstrings. Jinja2 templates are customizable. Config via `pyproject.toml` |
| `llms.txt` (hand-authored static file) | llmstxt.org spec v1 | Machine-readable documentation index for MCP clients and AI agents | The spec is trivially simple: one required H1 (`# ztlctl`), optional blockquote summary, H2 sections with markdown link lists. Served as a static file by GitHub Pages at `/ztlctl/llms.txt`. No build step, no library. The `llms-txt` PyPI package exists (v0.0.6, 2026-01-29) but is only needed for programmatic parsing — not for authoring |
| Python stdlib (`pathlib`, `re`) | 3.13 (stdlib) | `ztlctl docs <query>` CLI command — search docs directory content at runtime | At ~20 pages, full-text indexing is overhead with no benefit. Simple line-by-line regex match across `docs/*.md` returns ranked results in milliseconds. Follows the existing `_impl` pattern (testable without MCP package). Zero new dependencies on the published package |
| Existing FastMCP resource pattern | current (`mcp` package, already pinned) | `ztlctl://docs/search` MCP resource for agent-queryable documentation | The MCP adapter is already built. `resources.py` has 11 existing `ztlctl://` resources each with a `_<name>_impl` function. Add `ztlctl://docs/search` following the exact same pattern — same `_RESOURCE_CATALOG` entry, same `_impl` delegate. No new server, no new library |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `griffe` | 1.x (pulled in by griffe2md) | AST-based Python API extraction engine | Automatic dependency of griffe2md. Only interact directly if custom Jinja2 template overrides are needed beyond what griffe2md provides |
| `llms-txt` | 0.0.6 | Parse and validate `llms.txt` programmatically | Only if a CI lint step to validate `llms.txt` format is wanted. Not needed to write or serve the file |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| `griffe2md` CLI | Generate `docs/developer-guide/api-reference.md` from `src/ztlctl/` | Run via `uv run griffe2md src/ztlctl --output docs/developer-guide/api-reference.md --docstring-style google`. Config in `pyproject.toml` under `[tool.griffe2md]`. Output committed to `docs/` — GitHub Pages cannot run Python build steps |
| Thin wrapper script | Prepend Jekyll front matter to griffe2md output | griffe2md does not add `---\ntitle: ...\nparent: ...\n---` front matter. A 10-line Python script wraps the CLI call and prepends the required YAML block before writing to `docs/` |

---

## Installation

```bash
# API reference generation — dev dependency only, not shipped in ztlctl package
uv add --group dev griffe2md

# Optional: llms.txt CI validation
uv add --group dev llms-txt
```

No new runtime dependencies. The `ztlctl docs` command uses only Python stdlib.

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| griffe2md 1.4.0 | pdoc 16.0.0 | When HTML output is acceptable and no Jekyll integration is needed. pdoc is excellent but only outputs HTML — not compatible with the existing Jekyll/Just the Docs pipeline |
| griffe2md 1.4.0 | pydoc-markdown 4.8.2 | Never for new projects — last released June 2023; development pivoted to Novella integration which is not stable or maintained |
| griffe2md 1.4.0 | Sphinx + autodoc + sphinx-markdown-builder | When a standalone Sphinx site is desired. Adds a parallel build pipeline, RST authoring, and Ruby+Python coordination complexity — not worth it when Jekyll already works |
| Hand-authored `llms.txt` | sphinx-llms-txt (PyPI) | Only applicable when using Sphinx as the doc builder. Jekyll has no equivalent plugin |
| stdlib `pathlib`+`re` | Whoosh full-text index | If the docs set grows beyond ~100 pages and ranking quality matters. Whoosh is also unmaintained (last PyPI release 2013) |
| stdlib `pathlib`+`re` | sqlite FTS5 (already in ztlctl) | Technically feasible since ztlctl already uses SQLite+FTS5, but wiring the docs corpus into the vault database conflates documentation tooling with knowledge-base storage — avoid this coupling |
| Existing FastMCP `_impl` pattern | Dedicated docs MCP server | The MCP adapter is already built and working. A separate server process for docs would require Claude Desktop config changes and adds operational complexity for a low-value gain |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `pydoc-markdown` | Abandoned since 2023; Novella replacement is not stable | `griffe2md` |
| Whoosh | Unmaintained since 2013; overkill for a ~20-page corpus | Python stdlib `re` + `pathlib` |
| MkDocs | Replaces the entire Jekyll/GitHub Pages pipeline with no documentation quality advantage | Continue with Jekyll + Just the Docs |
| A separate documentation HTTP server | Adds an always-on runtime dependency for a CLI tool; doc search should work offline and locally | Stdlib text search embedded in `ztlctl docs` Click command |
| `has_children: true` in Just the Docs front matter | Redundant in current Just the Docs (v0.5+); was required in v0.3.x. Causes confusion when contributors copy old examples | Use only `parent:` on child pages; omit `has_children` |
| Runtime imports of `griffe` in production code | griffe is a dev/build tool; importing it at runtime would add a heavy unused dependency to installed ztlctl | Keep in `--group dev` only; run as a pre-commit or release step |
| Dynamically generating `llms.txt` at request time | Adds complexity for a file that changes only when docs change | Static committed file served by GitHub Pages |

---

## Stack Patterns by Feature

**Multi-audience navigation (User Guide vs Developer Guide):**

Create two top-level "section header" index pages:
- `docs/user-guide/index.md` with `nav_order: 2` (no `parent:`)
- `docs/developer-guide/index.md` with `nav_order: 3` (no `parent:`)

All user guide pages:
```yaml
---
title: Quick Start
parent: User Guide
nav_order: 1
---
```

All developer guide pages:
```yaml
---
title: Plugin Authoring Guide
parent: Developer Guide
nav_order: 1
---
```

No `_config.yml` changes needed. Just the Docs builds the nav tree entirely from front matter.

**`llms.txt` file structure:**

```markdown
# ztlctl

> CLI utility and MCP tool for managing a Zettelkasten knowledge system.
> Treats CLI and MCP as auto-generated surfaces over a unified ActionRegistry.

## User Guide

- [Installation](https://thatdevstudio.github.io/ztlctl/user-guide/installation): Setup and requirements
- [Quick Start](https://thatdevstudio.github.io/ztlctl/user-guide/quickstart): First vault in 5 minutes

## Developer Guide

- [Plugin Authoring](https://thatdevstudio.github.io/ztlctl/developer-guide/plugins): Hook specs, custom note types
- [API Reference](https://thatdevstudio.github.io/ztlctl/developer-guide/api-reference): Auto-generated from source

## Optional

- [Agentic Workflow Recipes](https://thatdevstudio.github.io/ztlctl/user-guide/agentic-workflows): Agent orchestration patterns
```

**`ztlctl docs <query>` CLI command — implementation sketch:**

```python
# src/ztlctl/commands/docs.py
def _docs_search_impl(query: str, docs_path: Path) -> list[dict]:
    """Testable without Click. Follows _impl pattern from mcp/resources.py."""
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results = []
    for md_file in sorted(docs_path.glob("**/*.md")):
        ...  # score: title match 3x, heading 2x, body 1x
    return sorted(results, key=lambda r: r["score"], reverse=True)[:10]
```

The `ztlctl://docs/search` MCP resource calls `_docs_search_impl` directly, just as `ztlctl://overview` calls `_overview_impl`.

**API reference generation workflow:**

```bash
# Generate (run manually or as CI step before release)
uv run python scripts/generate_api_ref.py
# → runs griffe2md, prepends Jekyll front matter, writes docs/developer-guide/api-reference.md
# → commit the output to docs/ (GitHub Pages has no Python build step)
```

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| griffe2md 1.4.0 | Python 3.9+ | Confirmed on PyPI; Python 3.13 is fully supported |
| griffe2md 1.4.0 | griffe 1.x | griffe2md pins to griffe 1.x; do not install griffe 0.x alongside it |
| llms-txt 0.0.6 | Python 3.9+ | Minimal package; no conflicts |
| Just the Docs (remote theme) | Jekyll 3.9.x (GitHub Pages) | Remote theme is version-locked by GitHub Pages infrastructure automatically |

---

## Sources

- [Just the Docs — Main Navigation](https://just-the-docs.com/docs/navigation/main/) — `parent`, `nav_order` front matter verified (HIGH)
- [Just the Docs — Child Pages](https://just-the-docs.com/docs/navigation/children/) — auto ToC, `has_toc: false` verified (HIGH)
- [Just the Docs — Ordering Pages](https://just-the-docs.com/docs/navigation/main/order/) — `nav_order` mechanics, `has_children` redundancy confirmed (HIGH)
- [griffe2md GitHub](https://github.com/mkdocstrings/griffe2md) — version 1.4.0 (2026-03-06), Markdown output, pyproject.toml config confirmed (HIGH)
- [griffe overview](https://mkdocstrings.github.io/griffe/) — AST extraction, zero-runtime-import design (HIGH)
- [llms.txt specification](https://llmstxt.org/) — required H1, optional blockquote, H2 sections, "Optional" section semantics (HIGH)
- [llms-txt PyPI](https://pypi.org/project/llms-txt/) — version 0.0.6, 2026-01-29 (HIGH)
- [pdoc PyPI](https://pypi.org/project/pdoc/) — version 16.0.0, HTML-only output confirmed (HIGH)
- [pydoc-markdown PyPI](https://pypi.org/project/pydoc-markdown/) — version 4.8.2, June 2023, development abandoned (MEDIUM)
- [FastMCP resources pattern](https://gofastmcp.com/servers/resources) — resource decorator, string return = TextResourceContents (MEDIUM)
- `src/ztlctl/mcp/resources.py` (direct inspection) — `_impl` pattern, `_RESOURCE_CATALOG`, `ztlctl://` URI scheme (HIGH)

---
*Stack research for: ztlctl v2.1 — Documentation overhaul with agent accessibility*
*Researched: 2026-03-20*
