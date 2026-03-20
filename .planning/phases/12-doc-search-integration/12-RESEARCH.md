# Phase 12: Doc Search Integration - Research

**Researched:** 2026-03-20
**Domain:** stdlib-only doc search, ActionDefinition pattern, MCP resource pattern
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Search behavior:**
- Search returns ranked list of matching pages with: title, relevance score, and excerpt (first matching paragraph)
- Default top 5 results, configurable with `--limit N`
- Search scope: title + headings + body text; title matches weighted 3x, heading matches 2x, body 1x
- Case-insensitive matching
- Multi-word queries: all terms must appear in the page (AND logic)

**Docs path resolution:**
- Primary: look for `docs/` directory relative to the ztlctl package install location (e.g., `Path(__file__).parent.parent.parent / "docs"`)
- Override: `ZTLCTL_DOCS_PATH` environment variable points to an alternate docs directory
- Fallback: if docs not found, return clear error with instructions to set `ZTLCTL_DOCS_PATH`
- At runtime, walk `docs/*.md` and `docs/guide/*.md` and `docs/dev/*.md` — the ~18 page corpus

**CLI command design:**
- `ztlctl docs <query>` — positional query argument (required)
- `--limit N` — max results (default 5)
- `--json` — structured JSON output
- Default output: Rich table with columns (Title, Score, Excerpt)
- Progressive disclosure: table shows top results; `--json` gives full structured data
- Register as a Click command group `docs` with `search` as default subcommand
- Follow existing ActionDefinition pattern: register in ActionRegistry, auto-generate CLI command

**MCP resource design:**
- `ztlctl://docs/search` — parameterized resource accepting `query` string, returns ranked results
- `ztlctl://docs/index` — static resource returning navigation map (mirrors llms.txt structure)
- Both follow existing `_impl` pattern in `resources.py`
- Results format: list of dicts with `{title, path, score, excerpt}` fields

**Shared _impl function:**
- `_docs_search_impl(query: str, limit: int = 5, docs_path: Path | None = None) -> list[dict]`
- Lives in a new module: `src/ztlctl/services/docs.py` (or `src/ztlctl/docs/search.py`)
- Pure function: takes query + path, returns results — testable without MCP or CLI
- CLI command calls `_docs_search_impl()` and renders with Rich
- MCP resource calls `_docs_search_impl()` and wraps in resource response

**Output format:**
- CLI default: Rich table with columns (Title, Score, Excerpt)
- CLI `--json`: `{"results": [{"title": "...", "path": "...", "score": 0.85, "excerpt": "..."}]}`
- MCP: same JSON structure as `--json` output

### Claude's Discretion

- Exact scoring algorithm (simple weighted term frequency is fine)
- Whether to strip markdown formatting from excerpts
- Module placement (`services/docs.py` vs `docs/search.py`)
- Whether `docs` is a command group or standalone command

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGNT-03 | `ztlctl docs <query>` CLI command for local documentation search with ranked results | ActionDefinition + `_docs_search_impl` + CLI generator wiring; `--json` flag via `AppContext.emit()`; Rich table via custom renderer |
| AGNT-04 | `ztlctl://docs/search` MCP resource for agent-queryable documentation following existing `_impl` pattern | `register_resources()` addition; `_RESOURCE_CATALOG` entry; `docs_search_impl` and `docs_index_impl` in `resources.py` |
</phase_requirements>

---

## Summary

Phase 12 adds in-tool documentation search: `ztlctl docs <query>` CLI command and two MCP resources (`ztlctl://docs/search`, `ztlctl://docs/index`). The implementation is entirely stdlib-based — no new dependencies. The search logic lives in a shared pure function module, called from both CLI and MCP surfaces following the `_impl` pattern that the codebase already uses for all 15 existing MCP resources.

The project has a fully established architecture for this pattern. Every moving part has an existing analogue: the `_impl` function style is in `resources.py`, the ActionDefinition registration is in `_register_core.py`, the CLI generator auto-builds commands from ActionDefinitions, and the MCP generator does the same for tools. The only non-standard wrinkle is that the `docs search` command has a `--json` flag (not the global `--json-output`), which means it either needs `custom_presentation=True` or a careful look at how to thread that flag through.

The docs corpus (`docs/*.md`, `docs/guide/*.md`, `docs/dev/*.md`) is 18 pages at ~3000 lines — well within range for naive TF-based scoring without any indexing overhead. The `docs/llms.txt` file is ready-made content for the `ztlctl://docs/index` static resource.

**Primary recommendation:** Place the pure search function in `src/ztlctl/services/docs.py`. Register a `docs_search` ActionDefinition with `cli_group="docs"` and `cli_name="search"`. Add both MCP resources to `resources.py` following the existing pattern. Wire MCP resources in `register_resources()` in `resources.py`.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pathlib | stdlib | Path resolution, file walking | Already used throughout the codebase |
| re | stdlib | Case-insensitive regex scoring, heading detection | Already used throughout the codebase |
| os | stdlib | `ZTLCTL_DOCS_PATH` env var lookup | Standard env override pattern |
| json | stdlib | MCP resource serialization | Used by every existing resource |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| rich | existing dep | Table output for CLI default display | CLI Rich table renderer (same pattern as other formatters) |

**No new dependencies required.** Everything needed is either stdlib or already installed.

**Installation:** No installation step — zero new packages.

---

## Architecture Patterns

### Recommended Project Structure

```
src/ztlctl/
├── services/
│   └── docs.py          # NEW: _docs_search_impl, _docs_index_impl, _resolve_docs_path
├── controllers/
│   └── docs.py          # NEW: DocsController.search() — wraps _docs_search_impl, returns ServiceResult
├── actions/
│   └── _register_core.py  # MODIFY: add docs_search ActionDefinition
├── commands/
│   └── __init__.py        # MODIFY: add docs group help text to _GROUP_HELP in generator.py
├── mcp/
│   └── resources.py       # MODIFY: add _docs_search_impl, _docs_index_impl, register_resources additions
```

### Pattern 1: Pure `_impl` Function (the canonical pattern)

**What:** A standalone function (no vault dependency, no CLI/MCP coupling) that takes plain args and returns serializable data. Used by both CLI and MCP.

**When to use:** Any cross-surface logic. All 15 existing MCP resources follow this pattern.

**Example from `resources.py`:**
```python
def capture_spec_impl(_vault: Any) -> dict[str, Any]:
    """Return the agent-facing capture contract for source bundle ingest."""
    return {
        "version": 1,
        "workflow": [...],
        "bundle_fields": {...},
    }
```

**New `_impl` signature (decided):**
```python
# src/ztlctl/services/docs.py
from __future__ import annotations

import os
import re
from pathlib import Path


def _resolve_docs_path() -> Path | None:
    """Resolve the docs/ directory. Checks ZTLCTL_DOCS_PATH first, then package-relative."""
    env_override = os.environ.get("ZTLCTL_DOCS_PATH")
    if env_override:
        p = Path(env_override)
        return p if p.is_dir() else None
    # Package-relative: src/ztlctl/services/docs.py -> src/ztlctl -> src -> project_root -> docs/
    candidate = Path(__file__).parent.parent.parent.parent / "docs"
    return candidate if candidate.is_dir() else None


def _docs_search_impl(
    query: str,
    limit: int = 5,
    docs_path: Path | None = None,
) -> list[dict]:
    """Search the docs corpus. Pure function — no MCP or CLI coupling."""
    ...
```

### Pattern 2: ActionDefinition Registration

**What:** A frozen dataclass registered in `_register_core.py` that drives both CLI and MCP auto-generation.

**Key fields:**
- `name`: unique action name (e.g. `"docs_search"`)
- `cli_group`: determines the Click group name (e.g. `"docs"` → `ztlctl docs search`)
- `cli_name`: overrides the derived command name (e.g. `"search"`)
- `handler`: `lambda vault, **kw: DocsController(vault).search(**kw)`
- `side_effect`: `"read"` — no vault mutations

**Important note on `--json` flag:** The existing `ActionParam` system supports `cli_flag=True` for boolean options. The `AppContext.emit()` method checks `settings.json_output` for JSON formatting. For a command-local `--json` flag (not the global `--json-output`), there are two options:
1. Pass a `json_output` param through the ActionDefinition and let the controller inspect it — this requires `custom_presentation=True` because the emit behavior changes
2. Or: use `custom_presentation=False` and have a param named `json_output` that overrides the global setting

Looking at the existing codebase: the global `--json-output` flag sets `settings.json_output`. The simplest approach for a command-local `--json` is `custom_presentation=True` with a hand-written command. However, the CONTEXT.md says "Follow existing ActionDefinition pattern" — this suggests option 2 is preferred. A `json_output` param named with `cli_name="json"` would map to `--json`.

**Registration example (closest analogue is `search` in `_register_core.py`):**
```python
registry.register(
    ActionDefinition(
        name="docs_search",
        description="Search the ztlctl documentation corpus.",
        category="docs",
        params=(
            ActionParam(
                "query",
                str,
                required=True,
                description="Search query string.",
                cli_is_argument=True,
                mcp_example="how to create a note",
            ),
            ActionParam(
                "limit",
                int,
                required=False,
                default=5,
                description="Maximum number of results to return.",
            ),
            ActionParam(
                "json_output",
                bool,
                required=False,
                default=False,
                description="Output results as JSON.",
                cli_flag=True,
                cli_name="json",
            ),
        ),
        handler=lambda vault, **kw: DocsController(vault).search(**kw),
        side_effect="read",
        mcp_when_to_use=(
            "Finding documentation pages relevant to a topic without leaving the tool."
        ),
        mcp_avoid_when="You are searching vault notes, not documentation.",
        cli_group="docs",
        cli_name="search",
    )
)
```

**Note:** The `json_output` param with `cli_flag=True, cli_name="json"` will generate `--json` as a bool flag on the CLI. The DocsController.search() method can inspect this and emit JSON or Rich table accordingly. However, since the standard `app.emit(result)` path uses `settings.json_output`, the controller needs to either (a) set a different return format in the ServiceResult metadata, or (b) this should use `custom_presentation=True` with a hand-written Click command. See the **Pitfalls** section.

### Pattern 3: DocsController

**What:** A thin controller that wraps the `_impl` function and returns a `ServiceResult`. Does NOT require a vault since docs search is vault-independent.

**Key insight:** The existing `BaseController.__init__` takes a `Vault`. For docs search, the vault is not needed — but the `handler` lambda signature in ActionDefinition always passes `vault` as the first arg. The controller should accept vault but not use it.

```python
# src/ztlctl/controllers/docs.py
from __future__ import annotations

from ztlctl.controllers.base import BaseController
from ztlctl.services.docs import _docs_search_impl, _docs_index_impl


class DocsController(BaseController):
    def search(self, query: str, limit: int = 5, json_output: bool = False) -> ...:
        results = _docs_search_impl(query, limit=limit)
        # Wrap in ServiceResult with appropriate data
        ...
```

### Pattern 4: MCP Resource Registration

**What:** Two new entries in `_RESOURCE_CATALOG` tuple and two new `@server.resource(...)` decorators in `register_resources()`.

**For `ztlctl://docs/search`** — parameterized: The existing MCP resources are all static (no query params). The CONTEXT.md says the `ztlctl://docs/search` resource accepts a `query` string parameter. Looking at the current `resources.py`, all resources take only `vault` — they are static. For a parameterized resource, FastMCP supports URI templates like `ztlctl://docs/search/{query}`. This is an important distinction.

**For `ztlctl://docs/index`** — static: Reads `docs/llms.txt` content. Simple file read, no params.

```python
# In _RESOURCE_CATALOG:
{"uri": "ztlctl://docs/search", "description": "Search the ztlctl documentation corpus."},
{"uri": "ztlctl://docs/index", "description": "Navigation map of all documentation pages."},

# In register_resources():
@server.resource("ztlctl://docs/index")  # type: ignore[untyped-decorator]
def docs_index_resource() -> str:
    """Navigation map of all documentation pages."""
    return docs_index_impl()

@server.resource("ztlctl://docs/search/{query}")  # type: ignore[untyped-decorator]
def docs_search_resource(query: str) -> str:
    """Search the ztlctl documentation corpus."""
    import json
    return json.dumps(docs_search_impl(query), indent=2)
```

**Note:** The CONTEXT.md specifies the URI as `ztlctl://docs/search` (parameterized, accepting `query`). FastMCP resource templates use `{param}` in the URI. The catalog entry should use the base URI `ztlctl://docs/search` for documentation; the registration should use the template form. Verify FastMCP version in use for correct template syntax.

### Pattern 5: Docs Path Resolution at Runtime

**What:** The `_resolve_docs_path()` function needs to locate `docs/` at runtime whether the package is installed via `uv` (editable), installed globally, or run from source.

**Path derivation:**
- In development (editable install): `__file__` for `src/ztlctl/services/docs.py` is `<repo>/src/ztlctl/services/docs.py` — so `Path(__file__).parent.parent.parent.parent` is `<repo>/`, and `<repo>/docs/` exists.
- In a production install (site-packages): `<site-packages>/ztlctl/services/docs.py` — so `Path(__file__).parent.parent.parent.parent` is site-packages' parent, NOT the repo. The `docs/` dir won't exist there unless installed as package data.
- `ZTLCTL_DOCS_PATH` env var override covers the production install case.

**Package data consideration:** The CONTEXT.md says "Primary: look for `docs/` directory relative to the ztlctl package install location." For a production install, this means `docs/` must be included as package data in `pyproject.toml` (via `[tool.setuptools.package-data]` or `[tool.hatch.build.targets.wheel.include]`). Check `pyproject.toml` to verify whether `docs/` is currently included as package data.

### Anti-Patterns to Avoid

- **Building a custom CLI command without ActionDefinition**: The generator auto-wires everything. Register via ActionDefinition + `_register_core.py` so the generator handles both CLI and MCP tool registration.
- **Adding vault dependency to the docs controller**: Docs search is vault-independent. Don't force a vault connection just to match the base class pattern — accept `vault` but don't call `vault.engine` or anything else.
- **Inline scoring in the MCP resource handler**: Keep `_docs_search_impl` pure and in `services/docs.py`, not inside `resources.py`. The 15 existing resource functions call services, not the reverse.
- **Using a non-standard URI for parameterized resource**: FastMCP uses `{param}` URI templates. Don't invent a custom query-string syntax.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CLI command generation | Manual Click command | ActionDefinition + `_register_core.py` + generator | Generator handles param mapping, JSON parsing, `app.emit()` |
| MCP tool registration | Manual `server.tool()` call | ActionDefinition + `generate_tools()` | Same generator path; consistent docstring, annotations |
| Result formatting | Custom JSON dumper | `json.dumps(..., indent=2)` in resource wrapper | All 15 existing resources use this exact pattern |
| Scoring | External search library | Weighted term-frequency in stdlib re | Corpus is 18 pages; no indexing needed |
| Heading detection | Custom parser | `re.match(r"^#{1,6}\s+", line)` | Standard markdown heading pattern |

**Key insight:** The ActionRegistry + generator duo is the single source of truth for all CLI/MCP surface. Anything bypassing it diverges from the established pattern and creates a maintenance split.

---

## Common Pitfalls

### Pitfall 1: The `--json` Flag vs `settings.json_output`

**What goes wrong:** The existing `app.emit(result)` path reads `settings.json_output` (the global `--json-output` flag). A command-local `--json` param with `cli_flag=True` gets passed to the controller but `app.emit()` won't know to switch to JSON output — it still uses the global flag.

**Why it happens:** The CLI generator always calls `app.emit(result)`, which formats based on `app.settings.json_output`. There's no mechanism to pass a local JSON flag to `emit()`.

**How to avoid:** Two options:
1. **Recommended:** Use `custom_presentation=True` for `docs_search` and write a hand-written Click command in `src/ztlctl/commands/docs.py`. This is what `update`, `garden`, `workflow`, and `serve` do. Register it in `commands/__init__.py` the same way those are registered. The controller and `_impl` function remain unchanged.
2. **Alternative:** Have the controller return a ServiceResult whose `data` contains a `"_format": "json"` sentinel that a custom result formatter detects. But this doesn't exist yet and is over-engineered.

**Warning signs:** If you see `json_output` being threaded through ActionParam to controller to emit(), that's a sign the pattern is being abused. Check `commands/__init__.py` for examples of `custom_presentation` commands.

### Pitfall 2: Docs Path Not Found in Production Install

**What goes wrong:** `Path(__file__).parent.parent.parent.parent / "docs"` works in development but not in a site-packages install where `docs/` is not present.

**Why it happens:** `docs/` is not a Python package and won't be included in a wheel unless explicitly declared as package data.

**How to avoid:** Check `pyproject.toml` for `[tool.hatch.build.targets.wheel.include]` or similar. If `docs/` is not included, either (a) add it, or (b) ensure the fallback error message clearly instructs setting `ZTLCTL_DOCS_PATH`. The CONTEXT.md already specifies a clear fallback error.

**Warning signs:** `_resolve_docs_path()` returns `None` in CI test runs — indicates the path derivation doesn't work from the test execution context.

### Pitfall 3: FastMCP Parameterized Resource URI Template Syntax

**What goes wrong:** Registering `@server.resource("ztlctl://docs/search")` without a template param produces a static resource that can't accept a `query` argument.

**Why it happens:** All 15 existing resources are static (no params). The parameterized form with `{query}` in the URI is a different FastMCP feature that hasn't been used in this codebase yet.

**How to avoid:** Use `@server.resource("ztlctl://docs/search/{query}")` and add `query: str` to the resource function signature. Add `"ztlctl://docs/search"` (without template) to `_RESOURCE_CATALOG` for documentation/catalog purposes.

**Warning signs:** FastMCP raises a registration error if the function signature has params not reflected in the URI template.

### Pitfall 4: AND Logic with Multi-Word Queries

**What goes wrong:** A naive "any term matches" search for "create note" returns every page that mentions either "create" or "note", flooding results with irrelevant pages.

**Why it happens:** OR logic is the default in text search; AND logic requires explicit per-term filtering.

**How to avoid:** Split query on whitespace, compute per-term score, then require all terms have score > 0 before including a page in results. The CONTEXT.md specifies AND logic.

**Warning signs:** Search for "create note" returns the troubleshooting page because it mentions "note" but not in the create context.

### Pitfall 5: Circular Import via `_register_core.py`

**What goes wrong:** `_register_core.py` uses lazy imports inside `_register_core_actions()` to avoid circular imports. Adding `from ztlctl.controllers.docs import DocsController` at module level would break startup.

**Why it happens:** The module is imported at startup; controller imports can pull in service imports which can pull in infrastructure imports.

**How to avoid:** Follow the existing pattern — `from ztlctl.controllers.docs import DocsController` must be inside the `_register_core_actions()` function body, not at module level.

---

## Code Examples

Verified patterns from existing source code:

### Scoring Algorithm (recommended approach)

```python
# src/ztlctl/services/docs.py
import re
from pathlib import Path


_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


def _score_page(text: str, title: str, terms: list[str]) -> float:
    """Weighted term frequency: title=3x, headings=2x, body=1x."""
    text_lower = text.lower()
    title_lower = title.lower()
    headings = [m.group(1).lower() for m in _HEADING_RE.finditer(text)]

    score = 0.0
    for term in terms:
        t = term.lower()
        # AND logic: if any term is absent entirely, score = 0 (handled by caller)
        title_count = title_lower.count(t)
        heading_count = sum(h.count(t) for h in headings)
        body_count = text_lower.count(t)
        score += title_count * 3 + heading_count * 2 + body_count * 1

    return score


def _extract_excerpt(text: str, terms: list[str]) -> str:
    """Return first paragraph that contains any search term."""
    paragraphs = re.split(r"\n\n+", _FRONTMATTER_RE.sub("", text))
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped or para_stripped.startswith("#"):
            continue
        para_lower = para_stripped.lower()
        if any(t.lower() in para_lower for t in terms):
            # Optionally strip markdown formatting
            excerpt = re.sub(r"[*_`#\[\]()]", "", para_stripped)
            return excerpt[:200].strip()
    return ""
```

### ActionDefinition Registration (closest analogue: `search` in `_register_core.py`)

```python
# Inside _register_core_actions() in _register_core.py
from ztlctl.controllers.docs import DocsController  # lazy import

registry.register(
    ActionDefinition(
        name="docs_search",
        description="Search the ztlctl documentation corpus.",
        category="docs",
        params=(
            ActionParam(
                "query",
                str,
                required=True,
                description="Search query string.",
                cli_is_argument=True,
                mcp_example="how to create a note",
            ),
            ActionParam(
                "limit",
                int,
                required=False,
                default=5,
                description="Maximum number of results to return.",
            ),
        ),
        handler=lambda vault, **kw: DocsController(vault).search(**kw),
        side_effect="read",
        mcp_when_to_use=(
            "Finding documentation pages relevant to a query without leaving the tool."
        ),
        mcp_avoid_when="You are searching vault notes, not ztlctl documentation.",
        cli_group="docs",
        cli_name="search",
    )
)
```

### MCP Resource Registration (from `resources.py` pattern)

```python
# In _RESOURCE_CATALOG:
{
    "uri": "ztlctl://docs/search",
    "description": "Search the ztlctl documentation corpus by query string.",
},
{
    "uri": "ztlctl://docs/index",
    "description": "Navigation map of all ztlctl documentation pages.",
},

# In register_resources():
@server.resource("ztlctl://docs/index")  # type: ignore[untyped-decorator]
def docs_index_resource() -> str:
    """Navigation map of all ztlctl documentation pages."""
    return docs_index_impl()


@server.resource("ztlctl://docs/search/{query}")  # type: ignore[untyped-decorator]
def docs_search_resource(query: str) -> str:
    """Search the ztlctl documentation corpus."""
    import json

    return json.dumps(docs_search_impl(query), indent=2)
```

### Custom Presentation Command (if `--json` flag required)

```python
# src/ztlctl/commands/docs.py
import click
from ztlctl.commands._base import ZtlGroup

@click.group("docs", help="Search ztlctl documentation.")
def docs_group() -> None:
    pass

@docs_group.command("search")
@click.argument("query")
@click.option("--limit", default=5, help="Maximum number of results.")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON.")
@click.pass_obj
def docs_search(app, query: str, limit: int, json_output: bool) -> None:
    from ztlctl.services.docs import _docs_search_impl
    results = _docs_search_impl(query, limit=limit)
    if json_output:
        import json
        click.echo(json.dumps({"results": results}, indent=2))
    else:
        # Rich table rendering
        from rich.table import Table
        from rich.console import Console
        table = Table(show_header=True)
        table.add_column("Title")
        table.add_column("Score")
        table.add_column("Excerpt")
        for r in results:
            table.add_row(r["title"], f"{r['score']:.2f}", r["excerpt"])
        Console().print(table)
```

```python
# In commands/__init__.py register_commands():
from ztlctl.commands.docs import docs_group
cli.add_command(docs_group)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-written MCP tools in `tools.py` | ActionRegistry + `generate_tools()` | Phase 6/7 | All new CLI+MCP actions must go through ActionDefinition |
| Static MCP resources only | FastMCP URI templates for parameterized resources | — | `ztlctl://docs/search/{query}` uses URI template syntax |

**Deprecated/outdated:**
- `mcp/tools.py`: Replaced by `mcp/generator.py`. Do NOT add tools directly there.
- Hand-writing Click commands for standard actions: The generator handles all non-`custom_presentation` actions automatically.

---

## Open Questions

1. **Is `custom_presentation=True` needed for the `--json` flag?**
   - What we know: The generator always calls `app.emit(result)`, which reads `settings.json_output`. A local `--json` flag passed as an ActionParam doesn't reach `emit()`.
   - What's unclear: Whether passing `json_output=True` to the controller and returning a specially-marked ServiceResult could thread through `emit()` without changes.
   - Recommendation: Use `custom_presentation=True` and write a hand-written command in `commands/docs.py`. This is the established escape hatch used by `update`, `garden`, `workflow`, `serve`.

2. **FastMCP parameterized resource syntax: `{query}` in URI or query-string?**
   - What we know: All 15 existing resources are static (no params). The FastMCP docs/version in use must be checked.
   - What's unclear: Whether FastMCP supports `ztlctl://docs/search/{query}` URI templates or requires a different approach.
   - Recommendation: Check `uv run python -c "import fastmcp; print(fastmcp.__version__)"` and review FastMCP docs for resource template syntax before implementing. If URI templates are not supported, the resource can accept no params and return a catalog/index instead, relying on the MCP tool (via ActionDefinition) for actual search.

3. **`docs/` as package data in production installs?**
   - What we know: `Path(__file__).parent.parent.parent.parent / "docs"` works in editable install. Production installs need `docs/` in the wheel.
   - What's unclear: Whether `pyproject.toml` includes `docs/` in wheel build targets.
   - Recommendation: Check `pyproject.toml` before implementing. Add the relevant `include` directive if needed, or document `ZTLCTL_DOCS_PATH` as the production configuration path.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/mcp/test_resources.py tests/services/test_docs.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGNT-03 | `_docs_search_impl` returns ranked results with title/score/excerpt | unit | `uv run pytest tests/services/test_docs.py -x` | ❌ Wave 0 |
| AGNT-03 | AND logic: multi-word query only matches pages with all terms | unit | `uv run pytest tests/services/test_docs.py::test_and_logic -x` | ❌ Wave 0 |
| AGNT-03 | `_resolve_docs_path` finds docs/ in dev context | unit | `uv run pytest tests/services/test_docs.py::test_resolve_path -x` | ❌ Wave 0 |
| AGNT-03 | `_resolve_docs_path` respects `ZTLCTL_DOCS_PATH` env var | unit | `uv run pytest tests/services/test_docs.py::test_env_override -x` | ❌ Wave 0 |
| AGNT-03 | Docs search ActionDefinition registered in registry | unit | `uv run pytest tests/actions/test_registry.py -x` | ✅ (extend) |
| AGNT-04 | `docs_search_impl` / `docs_index_impl` return correct structure | unit | `uv run pytest tests/mcp/test_resources.py -x` | ✅ (extend) |
| AGNT-04 | `ztlctl://docs/index` and `ztlctl://docs/search` in resource catalog | unit | `uv run pytest tests/mcp/test_resources.py::TestResourceCatalog -x` | ✅ (extend) |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/services/test_docs.py tests/mcp/test_resources.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/services/test_docs.py` — covers AGNT-03 search logic, path resolution, AND logic, scoring weights
- [ ] `tests/controllers/test_docs.py` — covers DocsController.search() result structure (optional, if controller logic is non-trivial)

*(Existing test files `tests/mcp/test_resources.py` and `tests/actions/test_registry.py` need new test cases but the files already exist.)*

---

## Sources

### Primary (HIGH confidence)

- Direct code read: `src/ztlctl/mcp/resources.py` — `_impl` pattern, `_RESOURCE_CATALOG`, `register_resources()` shape
- Direct code read: `src/ztlctl/actions/_register_core.py` — ActionDefinition registration pattern, lazy controller imports
- Direct code read: `src/ztlctl/actions/definitions.py` — ActionParam and ActionDefinition field reference
- Direct code read: `src/ztlctl/commands/generator.py` — CLI auto-generation logic, `_GROUP_HELP` dict, `custom_presentation` bypass
- Direct code read: `src/ztlctl/commands/__init__.py` — `register_commands()` custom_presentation additions
- Direct code read: `src/ztlctl/controllers/base.py` — BaseController interface
- Direct code read: `src/ztlctl/mcp/generator.py` — MCP tool generation, `generate_tools()`
- Direct code read: `tests/mcp/test_resources.py` — test pattern for `_impl` functions

### Secondary (MEDIUM confidence)

- `docs/llms.txt` — confirmed as ready-made content for `ztlctl://docs/index` resource
- `docs/` directory listing — confirmed 18-page corpus across `docs/*.md`, `docs/guide/*.md`, `docs/dev/*.md`

### Tertiary (LOW confidence)

- FastMCP URI template syntax for parameterized resources — not verified against FastMCP source; check version before implementing

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies, all stdlib
- Architecture patterns: HIGH — directly observed from codebase reading
- ActionDefinition/CLI wiring: HIGH — all patterns read from source
- MCP resource pattern: HIGH — 15 existing examples to follow exactly
- FastMCP parameterized resource syntax: LOW — not verified, flagged as open question
- Pitfalls: HIGH — derived from direct codebase analysis

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable codebase, no fast-moving dependencies)
