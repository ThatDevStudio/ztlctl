# Phase 11: Developer Guide + API Reference - Research

**Researched:** 2026-03-20
**Domain:** Documentation tooling (mkdocstrings/griffe) + plugin API surface extraction
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**API reference generation**
- Use mkdocstrings with griffe backend for auto-generated API reference from Python docstrings/type hints
- Add `mkdocstrings[python]` to dev dependencies (griffe is included as a dependency of mkdocstrings-python)
- Configure in mkdocs.yml with `plugins: - mkdocstrings`
- Scope: plugin public API only — hookspecs, contracts, _version (PLUGIN_API_VERSION), ActionDefinition, ActionParam, ActionRegistry
- Do NOT document internal implementation (services, infrastructure, etc.)
- Create `docs/api-reference.md` that uses `::: ztlctl.plugins.hookspecs` style directives

**Plugin authoring guide**
- New `docs/plugin-guide.md` — tutorial-style walkthrough followed by reference sections
- Tutorial section: "Build Your First Plugin" covering plugin class with PLUGIN_API_VERSION = 1, a post_action hook, NoteTypeDefinition registration, plugin config schema, capability declaration, pyproject.toml entry point registration
- Reference section: All hookspecs with signatures, return types, and behavior notes
- Include a complete working example plugin (inline code, not a separate repo)

**Architecture documentation**
- Enhance `docs/development.md` with architecture overview covering 6-layer package structure diagram, 4-layer action model (Data/Service/Controller/Registry) with flow diagram, how CLI and MCP surfaces are auto-generated from ActionRegistry, plugin system integration points
- High-level mental model for contributors — not implementation-level detail

**CONTRIBUTING.md updates**
- Keep CONTRIBUTING.md as standalone file (GitHub convention)
- Add cross-links from dev guide to CONTRIBUTING.md for setup, branching, commit conventions
- Update CONTRIBUTING.md architecture section to reference the new detailed architecture page
- Ensure no contradictions between CONTRIBUTING.md and docs/development.md

**Nav structure**
```yaml
- Developer Guide:
  - dev/index.md
  - Contributing: development.md
  - Plugin Authoring: plugin-guide.md
  - API Reference: api-reference.md
  - MCP Server: mcp.md
```
- Update llms.txt and NAV_ORDER for new pages
- Regenerate llms-full.txt

### Claude's Discretion
- Exact mkdocstrings configuration options (show_source, heading_level, etc.)
- Whether to split plugin-guide.md into tutorial + reference or keep as one page
- Architecture diagram format (ASCII, mermaid, or prose with headings)
- Ordering of hookspecs in the reference section

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DVGD-01 | Plugin authoring guide — hookspecs, custom note types, config schemas, capability declarations, marketplace metadata | Full hookspec inventory below; GitPlugin + ReweavePlugin as real tutorial examples |
| DVGD-02 | Auto-generated API reference from Python docstrings/type hints via griffe/mkdocstrings | mkdocstrings[python] 2.0.3 + mkdocstrings 1.0.3 + griffe 2.0.0; mkdocs.yml plugin config documented |
| DVGD-03 | ActionRegistry and controller architecture documentation for core contributors | ActionDefinition, ActionParam, ActionRegistry public API fully inventoried; architecture flow documented |
| DVGD-04 | Update CONTRIBUTING.md with current architecture walkthrough and link to developer guide | Gap analysis between CONTRIBUTING.md and development.md documented; cross-link strategy defined |

</phase_requirements>

---

## Summary

Phase 11 is a pure documentation authoring phase. No production code changes; the only code change is adding `mkdocstrings[python]` to the dev dependency group and adding the `mkdocstrings` plugin to `mkdocs.yml`. The deliverables are three new or enhanced markdown files: `docs/plugin-guide.md` (new), `docs/api-reference.md` (new), enhanced `docs/development.md`, and updated `docs/dev/index.md`, `docs/llms.txt`, `scripts/gen_llms_full_txt.py`, and `CONTRIBUTING.md`.

The plugin API surface is well-documented in source code with docstrings and type hints, making it ideal mkdocstrings input. The griffe backend can statically analyze `src/ztlctl/` without importing the package. The two built-in plugins — GitPlugin and ReweavePlugin — serve as ready-made, tested tutorial examples for the "Build Your First Plugin" walkthrough.

The mkdocs-shadcn theme has explicit mkdocstrings support (listed in its plugin documentation). The compatibility is noted as "alpha status" in the theme's own docs, meaning it works but may have rendering edge cases. The recommended approach is to test locally with `mkdocs serve` and keep mkdocstrings config conservative (no mermaid inheritance diagrams, standard show_source=True).

**Primary recommendation:** Use `mkdocstrings[python]>=1.0.3` (installs mkdocstrings-python 2.0.3 + griffe 2.0.0 as deps), configure with `paths: [src]` and `docstring_style: google`, scope directives to 6 public API modules.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mkdocstrings[python] | >=1.0.3 | Auto-generates API reference from Python docstrings | Official mkdocstrings meta-package; pulls in mkdocstrings-python 2.0.3 + griffe 2.0.0 |
| griffe | 2.0.0 (transitive) | Static AST parser for Python source code | Included automatically as mkdocstrings-python dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| mkdocstrings-python | 2.0.3 (transitive) | Python handler for mkdocstrings | Installed automatically via `mkdocstrings[python]`; do not add separately |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `mkdocstrings[python]` | `mkdocstrings-python` direct | Both work; `mkdocstrings[python]` is the canonical install path per official docs |

**Installation (add to dev dependency group):**
```bash
uv add --group dev "mkdocstrings[python]>=1.0.3"
```

**Version verification (confirmed 2026-03-20):**
- mkdocstrings: 1.0.3 (released 2026-02-07)
- mkdocstrings-python: 2.0.3 (released 2026-02-20)
- griffe: 2.0.0 (transitive, latest)

---

## Architecture Patterns

### Recommended Project Structure (new files only)
```
docs/
├── plugin-guide.md       # NEW: Tutorial + reference for plugin authors
├── api-reference.md      # NEW: Auto-generated API via mkdocstrings directives
├── development.md        # ENHANCED: Architecture overview added
├── dev/
│   └── index.md          # UPDATED: New page entries in table
├── llms.txt              # UPDATED: New page entries
└── llms-full.txt         # REGENERATED: via scripts/gen_llms_full_txt.py

scripts/
└── gen_llms_full_txt.py  # UPDATED: NAV_ORDER with new pages

CONTRIBUTING.md           # UPDATED: Cross-links + architecture reference
mkdocs.yml                # UPDATED: mkdocstrings plugin + new nav entries
pyproject.toml            # UPDATED: mkdocstrings[python] in dev deps
```

### Pattern 1: mkdocstrings Plugin Configuration

**What:** Add mkdocstrings to the MkDocs plugin chain in `mkdocs.yml`. Use `paths: [src]` so griffe can find the package without the package being installed in the docs build env.

**When to use:** Any time `::: module.path` directives appear in markdown pages.

**Recommended configuration:**
```yaml
# Source: https://mkdocstrings.github.io/python/usage/
plugins:
  - search
  - redirects:
      redirect_maps: {}
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            docstring_style: google
            show_source: true
            heading_level: 2
            show_root_heading: true
            show_symbol_type_heading: true
            members_order: source
            filters:
              - "!^_"
            show_signature_annotations: true
            separate_signature: true
```

**Key option rationale (Claude's discretion items resolved):**
- `show_source: true` — plugin authors benefit from seeing real implementations
- `heading_level: 2` — default; matches the page's H2 structure
- `show_root_heading: true` — needed since each module gets its own page section
- `members_order: source` — preserves logical grouping (generic hooks first, deprecated last, extension hooks last) that is already intentional in hookspecs.py
- `filters: ["!^_"]` — excludes private members; all plugin-public API is public-named
- `docstring_style: google` — existing docstrings use Google-style format (confirmed by inspection of hookspecs.py, contracts.py)

### Pattern 2: API Reference Directive Usage

**What:** Use `::: module.path` directives in `docs/api-reference.md` to auto-render each module.

**Example (docs/api-reference.md):**
```markdown
# API Reference

## Plugin Hookspecs

::: ztlctl.plugins.hookspecs
    options:
      show_root_heading: true
      heading_level: 2

## Plugin Contracts

::: ztlctl.plugins.contracts
    options:
      show_root_heading: true
      heading_level: 2

## API Versioning

::: ztlctl.plugins._version
    options:
      heading_level: 2

## Action System

::: ztlctl.actions.definitions
    options:
      heading_level: 2

::: ztlctl.actions.registry
    options:
      heading_level: 2
```

### Pattern 3: Plugin Guide Structure

**What:** Single `docs/plugin-guide.md` with two logical halves — tutorial walkthrough then hookspec reference. The planner can optionally split into two files (`plugin-tutorial.md` + `plugin-reference.md`), but a single file is simpler to maintain and avoids a three-page nav expansion.

**Recommended single-file structure:**
```
# Plugin Authoring Guide

## Overview
## Tutorial: Build Your First Plugin
  ### 1. Create the Plugin Package
  ### 2. Add PLUGIN_API_VERSION
  ### 3. Implement post_action
  ### 4. Declare Capabilities
  ### 5. Add a Custom Note Type (NoteTypeDefinition)
  ### 6. Add Plugin Config (get_config_schema + initialize)
  ### 7. Register via Entry Point
  ### 8. Test Your Plugin

## Hookspec Reference
  ### Generic Action Hooks (Preferred)
  ### Plugin Lifecycle Hooks
  ### Extension Contribution Hooks
  ### Custom Note Type + Rendering Hooks
  ### Security — Capability Declarations
  ### Deprecated Per-Event Hooks (migration guide)

## Plugin Metadata (PluginMetadata)
## Compatibility and Versioning
```

### Pattern 4: Architecture Enhancement for development.md

**What:** Insert a new "Architecture Overview" section between "Architecture" (existing skeleton) and "Template Overrides".

**Content currently in development.md (existing, keep as-is):**
- Setup commands
- Development commands
- CI/CD pipeline
- Homebrew formula
- Architecture (6-layer diagram + dependency flow — already present)
- Template Overrides, Workflow Templates, Plugin Init Hooks
- Contributing cross-link

**New content to add to development.md:**
- 4-layer action model explanation (Data layer: ActionParam/ActionDefinition; Service layer: *Service classes; Controller layer: BaseController subclasses that wire ActionDefinitions to ServiceResult calls; Registry layer: ActionRegistry singleton that CLI and MCP generators read)
- How CLI auto-generation works: `list_actions(category=...)` → Click command builder
- How MCP auto-generation works: `list_actions()` → MCP tool descriptors
- Plugin integration points: where in the service call chain hooks fire

### Anti-Patterns to Avoid

- **Documenting internal modules:** Do NOT add `::: ztlctl.services.*`, `::: ztlctl.infrastructure.*`, etc. directives — these are not plugin API and would generate massive, unintended output.
- **Duplicating setup instructions:** development.md and CONTRIBUTING.md both have setup sections. The resolution is cross-links, not duplication. Keep each authoritative on its own domain: CONTRIBUTING.md owns contribution process; development.md owns architecture understanding.
- **Using `members: true` on hookspecs.py:** The `ZtlctlHookSpec` class has private helpers; the default filter `!^_` handles this automatically. Do not override with `members: true`.
- **Skipping `paths: [src]` in mkdocstrings config:** Without `paths: [src]`, griffe cannot locate `ztlctl` package source during `mkdocs build`. The docs CI workflow uses `pip install` not `uv`, so griffe needs the explicit path.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| API reference from docstrings | Manual parameter tables in markdown | mkdocstrings `::: module.path` directives | Manual tables drift from code; mkdocstrings auto-updates on next build |
| Hookspec signature rendering | Inline code blocks copied from source | mkdocstrings auto-renders signatures from type hints | Type hints are the source of truth; auto-render ensures accuracy |
| Docstring parsing | Custom extraction scripts | griffe (via mkdocstrings-python) | griffe handles `from __future__ import annotations`, TYPE_CHECKING blocks, conditional imports correctly |

**Key insight:** The plugin API source files (hookspecs.py, contracts.py, _version.py, definitions.py, registry.py) already have complete Google-style docstrings and type hints. mkdocstrings can render these with zero additional annotation work.

---

## Complete Plugin API Surface Inventory

This is the definitive list of public API items that Phase 11 must document. Extracted directly from source.

### Hookspecs (`src/ztlctl/plugins/hookspecs.py` — 291 lines)

**Generic Action Hooks (stable, preferred):**
| Hookspec | Signature | Behavior | firstresult? |
|----------|-----------|----------|-------------|
| `pre_action` | `(action_name: str, kwargs: dict[str, Any]) -> ActionRejection \| dict[str, Any] \| None` | Return `ActionRejection` to abort, modified kwargs dict to transform, or `None` to pass through | Yes (first non-None wins) |
| `post_action` | `(action_name: str, kwargs: dict[str, Any], result: Any) -> None` | Called after every action; all plugins receive regardless of outcome | No |

**Plugin Lifecycle Hooks:**
| Hookspec | Signature | Behavior | firstresult? |
|----------|-----------|----------|-------------|
| `get_config_schema` | `() -> type[BaseModel] \| None` | Return Pydantic model class for config validation; called once at load time | Yes |
| `initialize` | `(config: BaseModel \| None) -> None` | Called once after loading with validated config (or None) | No |

**Extension Contribution Hooks:**
| Hookspec | Return Type | Behavior |
|----------|-------------|----------|
| `register_content_models` | `dict[str, type[ContentModel]] \| None` | Extend CONTENT_REGISTRY with subtype -> ContentModel mappings |
| `register_cli_commands` | `list[CliCommandContribution] \| None` | Add Click commands to the CLI |
| `register_mcp_tools` | `list[McpToolContribution] \| None` | Add MCP tools |
| `register_mcp_resources` | `list[McpResourceContribution] \| None` | Add MCP resources |
| `register_mcp_prompts` | `list[McpPromptContribution] \| None` | Add MCP prompts |
| `register_workflow_modules` | `list[WorkflowModuleContribution] \| None` | Add workflow export modules |
| `register_workspace_profiles` | `list[WorkspaceProfileContribution] \| None` | Add workspace profiles |
| `register_vault_init_steps` | `list[VaultInitStepContribution] \| None` | Add ordered steps to `ztlctl init` pipeline |
| `register_source_providers` | `list[SourceProviderContribution] \| None` | Add source ingestion providers |
| `register_note_types` | `list[NoteTypeDefinition] \| None` | Register custom note types; PluginManager auto-creates CRUD ActionDefinitions |
| `register_render_contributions` | `list[RenderContribution] \| None` | Add rich_formatter + mcp_formatter for custom note types |

**Security Hook:**
| Hookspec | Signature | Valid Values |
|----------|-----------|-------------|
| `declare_capabilities` | `() -> set[str] \| None` | `{"filesystem", "network", "database", "git"}` |

**Deprecated Per-Event Hooks (warn_on_impl=DeprecationWarning since plugin API v2):**
- `post_create(content_type, content_id, title, path, tags)` → use `post_action` + filter
- `post_update(content_type, content_id, fields_changed, path)` → use `post_action` + filter
- `post_close(content_type, content_id, path, summary)` → use `post_action` + filter
- `post_reweave(source_id, affected_ids, links_added)` → use `post_action` + filter
- `post_session_start(session_id)` → use `post_action` + filter
- `post_session_close(session_id, stats)` → use `post_action` + filter
- `post_check(issues_found, issues_fixed)` → use `post_action` + filter
- `post_init(vault_name, client, tone)` → use `post_action` + filter
- `post_init_profile(vault_name, profile, tone, managed_paths)` → use `post_action` + filter

### Contracts (`src/ztlctl/plugins/contracts.py` — 237 lines)

**Action Hook Contracts:**
- `ActionRejection(reason: str, code: str = "plugin_rejected", detail: dict = {})` — return from `pre_action` to abort

**Extension Contribution Contracts:**
- `CliCommandContribution(name: str, command: click.Command)`
- `McpToolContribution(name: str, handler: Callable, catalog_entry: ToolCatalogEntry)`
- `McpResourceContribution(uri: str, description: str, handler: Callable)`
- `McpPromptContribution(name: str, description: str, handler: Callable, takes_vault: bool = True)`
- `WorkflowModuleContribution(name: str, render: Callable[[dict], str])`
- `WorkspaceProfileContribution(profile_id: str, description: str, aliases: tuple = (), managed_paths: tuple = (), init_scaffold: Callable | None = None)`
- `VaultInitStepContribution(step_id: str, description: str, run: Callable[[VaultInitContext], VaultInitStepResult], order: int = 500, profiles: tuple = ())`
- `SourceProviderContribution(name: str, description: str, schemes: tuple[str, ...], fetch: Callable[[SourceFetchRequest], SourceFetchResult])`
- `RenderContribution(note_type: str, rich_formatter: Callable[[dict], str], mcp_formatter: Callable[[dict], dict])`

**Vault Init Support Types:**
- `VaultInitContext(vault_root: Path, vault_name: str, profile: str, tone: str, topics: tuple = (), no_workflow: bool = False)`
- `VaultInitInstruction(instruction_id: str, title: str, body: str, items: tuple = (), kind: "manual" | "install" | "verify" = "manual")`
- `VaultInitStepResult(files_created: tuple = (), warnings: tuple = (), instructions: tuple[VaultInitInstruction, ...] = ())`

**Source Provider Support Types:**
- `SourceFetchRequest(content: str, input_kind: str, summary: str | None, provider: str | None, metadata: dict = {})`
- `SourceFetchResult(body_text: str, title: str | None, canonical_url: str | None, content_type: str | None, language: str | None, source_type: str | None, summary_hint: str | None, key_points: tuple = (), citations: tuple = (), metadata: dict = {}, warnings: tuple = ())`

**Plugin Marketplace Metadata:**
- `PluginMetadata(name: str, version: str, author: str, capabilities: tuple[str, ...], ztlctl_api_version: int, description: str = "")` — declared in `[tool.ztlctl-plugin]` pyproject.toml section

### API Versioning (`src/ztlctl/plugins/_version.py` — 64 lines)

- `PLUGIN_API_VERSION: int = 1` — current host-side version
- `PluginLoadError(Exception)` — raised for incompatible plugin API versions
- `check_plugin_api_version(plugin: object, plugin_name: str) -> list[str]` — returns warning strings; raises `PluginLoadError` for incompatible versions

**Compatibility window:** `_COMPATIBILITY_WINDOW = 2`. Plugins declaring versions ≤ (PLUGIN_API_VERSION - 2) are rejected. Plugins 1-2 versions behind get a warning. Exact match = fully compatible.

**Rule for plugin authors:** Declare `PLUGIN_API_VERSION = 1` on the plugin class. Missing attribute = treated as legacy (loaded without warning).

### Action System (`src/ztlctl/actions/`)

**ActionParam** (frozen dataclass):
- `name: str`, `type: type`, `required: bool = True`, `default: Any = None`
- `description: str`, `choices: tuple[str, ...] | None = None`
- `cli_multiple: bool`, `cli_is_argument: bool`, `cli_flag: bool`, `cli_name: str | None`
- `mcp_example: str`

**ActionDefinition** (frozen dataclass):
- Core: `name: str` (dotted, e.g. `"note.search"`), `description: str`, `category: str`, `params: tuple[ActionParam, ...]`, `handler: Callable[..., Any]`, `side_effect: "read" | "write"`
- MCP metadata: `mcp_when_to_use: str`, `mcp_avoid_when: str`, `mcp_common_errors: tuple[str, ...]`
- CLI metadata: `cli_group: str | None`, `cli_examples: str`, `cli_interactive_params: tuple[str, ...]`, `cli_name: str | None`
- Presentation: `custom_presentation: bool = False`

**ActionRegistry** (singleton):
- `register(action: ActionDefinition) -> None` — raises `ValueError` on duplicate name
- `get(name: str) -> ActionDefinition` — raises `KeyError` if not found
- `list_actions(*, category=None, side_effect=None, custom_presentation=None) -> list[ActionDefinition]`
- `get_action_registry() -> ActionRegistry` — module-level singleton accessor

**Plugin authors register custom note types via `register_note_types()` hookspec — PluginManager auto-creates ActionDefinitions. Direct ActionRegistry.register() is for advanced use only.**

### NoteTypeDefinition (`src/ztlctl/domain/registry.py`)

```python
@dataclass(frozen=True)
class NoteTypeDefinition:
    name: str                          # Unique registry key ("sprint", "kanban")
    content_type: str                  # Parent: "note", "reference", "task", "log"
    model_cls: type[ContentModel]      # Pydantic model class
    transitions: dict[str, list[str]]  # Lifecycle state machine
    template_name: str                 # Jinja2 template filename ("" for DB-only)
    required_sections: list[str] = []  # Required markdown body sections
    initial_status: str = ""           # "" = use first key of transitions
    is_subtype: bool = False           # True for decision, knowledge, article, etc.
    parent_type: str | None = None     # Required when is_subtype=True
```

---

## Common Pitfalls

### Pitfall 1: mkdocstrings and mkdocs-shadcn — Alpha Compatibility
**What goes wrong:** mkdocstrings support in mkdocs-shadcn is listed as "alpha status" in the theme's own documentation. Certain rendering features (inheritance diagrams, mermaid) may not render correctly.
**Why it happens:** mkdocs-shadcn uses its own template engine; mkdocstrings injects HTML via custom Jinja2 templates that the theme must accommodate.
**How to avoid:** Keep mkdocstrings config conservative. Do NOT enable `show_inheritance_diagram: true`. Test with `mkdocs serve` locally before committing. Standard signature rendering and docstring sections work.
**Warning signs:** HTML-bleed (raw `<div>` visible in output), heading level collisions.

### Pitfall 2: docs CI workflow cannot import ztlctl
**What goes wrong:** `mkdocs build` fails in CI because ztlctl is not installed in the docs build env (which uses bare pip, not uv).
**Why it happens:** Without `paths: [src]` in mkdocstrings config, griffe tries to import the package dynamically (inspection mode). ztlctl has complex dependencies (SQLAlchemy, pluggy, etc.) not installed in the minimal docs CI env.
**How to avoid:** Set `paths: [src]` in the mkdocstrings handler config. griffe then uses static AST analysis (visitor mode) without importing. Also set `allow_inspection: false` to force visitor mode.
**Warning signs:** `ModuleNotFoundError: No module named 'ztlctl'` during `mkdocs build`.

### Pitfall 3: TYPE_CHECKING imports not resolved by griffe visitor mode
**What goes wrong:** Parameter types declared inside `if TYPE_CHECKING:` blocks (like `ContentModel`, `NoteTypeDefinition`) appear as unresolved in rendered API docs.
**Why it happens:** griffe in visitor mode parses AST but does not execute TYPE_CHECKING blocks. The `from __future__ import annotations` at the top of hookspecs.py means annotations are strings, which griffe resolves from the AST.
**How to avoid:** griffe 2.0.0 handles `from __future__ import annotations` correctly. The TYPE_CHECKING pattern in hookspecs.py uses string-form annotations, which griffe can resolve. This is a known-good pattern as of griffe 2.0.0.
**Warning signs:** Parameter types showing as `~ztlctl.plugins.contracts.ActionRejection` instead of `ActionRejection` — this is normal cross-module ref formatting and is correct behavior.

### Pitfall 4: development.md and CONTRIBUTING.md duplication
**What goes wrong:** Both files have a "Development Setup" section with identical `uv sync --group dev` + `uv run pytest` commands. Adding more architecture content to development.md risks contradicting CONTRIBUTING.md.
**Why it happens:** development.md was written as a docs-site page; CONTRIBUTING.md as a standalone GitHub file. Their scopes partially overlap.
**How to avoid:** Strict division of ownership: development.md owns architecture understanding (what layers exist, why); CONTRIBUTING.md owns contribution process (how to branch, what CI checks, how to PR). Cross-link across the boundary. The architecture section in CONTRIBUTING.md (lines 44-60) should be updated to reference development.md rather than duplicate it.
**Warning signs:** Future contributor finds conflicting instructions in the two files.

### Pitfall 5: gen_llms_full_txt.py NAV_ORDER drift
**What goes wrong:** llms-full.txt is regenerated but the new pages (plugin-guide.md, api-reference.md) are missing from it because NAV_ORDER was not updated.
**Why it happens:** The script comment says "Keep NAV_ORDER in sync with mkdocs.yml nav" — this is manual maintenance.
**How to avoid:** Update NAV_ORDER in the same commit that adds the new nav entries to mkdocs.yml. Run `python scripts/gen_llms_full_txt.py` and commit the regenerated llms-full.txt.
**Warning signs:** llms-full.txt is smaller than expected after new pages are added.

### Pitfall 6: api-reference.md in CI mkdocs build
**What goes wrong:** `mkdocs build --strict` fails because api-reference.md references ztlctl modules that griffe cannot resolve in the CI docs env.
**Why it happens:** Even with `paths: [src]`, some transitive imports in ztlctl modules may trigger griffe warnings treated as errors in strict mode.
**How to avoid:** Do NOT run `mkdocs build --strict` in CI. The existing CI workflow (`.github/workflows/`) already uses `mkdocs gh-deploy` without `--strict`. Confirm this is still true. If strict mode is desired later, use `griffe_unsupported_logs: "debug"` option to suppress.

---

## Code Examples

### Complete Working Plugin (Tutorial Example)

Based directly on GitPlugin and ReweavePlugin patterns:

```python
# Source: src/ztlctl/plugins/builtins/git.py + contracts.py patterns
"""my_vault_plugin — Example plugin for ztlctl."""

from __future__ import annotations

from typing import Any

import pluggy
from pydantic import BaseModel

hookimpl = pluggy.HookimplMarker("ztlctl")


class MyPluginConfig(BaseModel):
    """Plugin configuration schema."""
    webhook_url: str = ""
    enabled: bool = True


class MyVaultPlugin:
    """Example ztlctl plugin."""

    PLUGIN_API_VERSION = 1

    def __init__(self) -> None:
        self._config = MyPluginConfig()

    @hookimpl
    def get_config_schema(self) -> type[BaseModel]:
        return MyPluginConfig

    @hookimpl
    def initialize(self, config: BaseModel | None) -> None:
        if config is not None:
            self._config = config  # type: ignore[assignment]

    @hookimpl
    def declare_capabilities(self) -> set[str]:
        return {"network"}

    @hookimpl
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        if not self._config.enabled:
            return
        if result is not None and not getattr(result, "ok", True):
            return
        if action_name in {"create_note", "create_reference"}:
            content_id = kwargs.get("content_id", "")
            # ... do something with content_id
```

**pyproject.toml entry point registration:**
```toml
[project.entry-points."ztlctl.plugins"]
my-plugin = "my_vault_plugin:MyVaultPlugin"
```

**User config (`.ztlctl/config.toml`):**
```toml
[plugins.my-plugin]
webhook_url = "https://example.com/hook"
enabled = true
```

### mkdocstrings Directive Usage

```markdown
<!-- Source: https://mkdocstrings.github.io/python/usage/ -->
::: ztlctl.plugins.hookspecs
    options:
      show_root_heading: true
      heading_level: 2
      members_order: source
      show_source: true
```

### NoteTypeDefinition Registration

```python
# Source: src/ztlctl/domain/registry.py pattern
from ztlctl.domain.registry import NoteTypeDefinition
from ztlctl.domain.content import NoteModel  # reuse a base model

my_type = NoteTypeDefinition(
    name="sprint",
    content_type="note",
    model_cls=NoteModel,
    transitions={"active": ["completed", "cancelled"], "completed": [], "cancelled": []},
    template_name="sprint.md.j2",
    required_sections=["## Goal", "## Stories"],
    initial_status="active",
)

@hookimpl
def register_note_types(self) -> list[NoteTypeDefinition]:
    return [my_type]
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-event hookspecs (post_create, post_update, ...) | Generic `post_action` with `action_name` filtering | Plugin API v2 | Deprecated hooks still work but emit DeprecationWarning; migrate to post_action |
| `mkdocstrings-python` direct install | `mkdocstrings[python]` meta-package | 2024+ | Same result; `mkdocstrings[python]` is the recommended install path in current docs |
| mkdocstrings 0.x series | mkdocstrings 1.0.3 + mkdocstrings-python 2.0.3 | Released 2026-02-07/20 | Major version bumps; configuration options largely stable but verify against current docs |

**Deprecated/outdated:**
- Per-event hookspecs (`post_create`, `post_update`, etc.): deprecated since plugin API v2; implemented via `warn_on_impl=DeprecationWarning` in hookspecs.py; still functional but will be removed in a future API version.
- `WorkspaceProfileContribution.init_scaffold`: "remains supported temporarily and is wrapped into the same ordered init pipeline for compatibility" (development.md line 119).

---

## What development.md Currently Covers vs What's Missing

### Currently Covered (development.md — 128 lines)
- Setup commands (uv sync, verify, pytest)
- Development commands (pytest coverage, ruff, mypy, pre-commit)
- CI/CD pipeline description (PR CI + Release Pipeline)
- Homebrew formula and release scripts
- Architecture (6-layer diagram + dependency flow arrow — brief, 3 lines)
- Template Overrides
- Workflow Templates
- Plugin Init Hooks (brief, ~10 lines)
- Contributing cross-link → CONTRIBUTING.md

### Missing from development.md (must add for DVGD-03)
1. **4-layer action model** — Data (ActionParam/ActionDefinition), Service (*Service classes), Controller (BaseController subclasses), Registry (ActionRegistry singleton)
2. **How CLI surface is auto-generated** — `get_action_registry().list_actions()` → Click command builder pattern
3. **How MCP surface is auto-generated** — same ActionRegistry → MCP tool descriptors
4. **Plugin system integration points** — where `pre_action`/`post_action` fire relative to the service call chain; how `register_note_types()` leads to auto-created ActionDefinitions
5. **ServiceResult contract** — the unified return type consumed by CLI, MCP, and plugins (referenced in CONTRIBUTING.md line 199 but not explained in development.md)

### What CONTRIBUTING.md Has That Must NOT Be Duplicated
- Development setup (lines 19-41) — keep in CONTRIBUTING.md; cross-link from development.md
- Branching model (lines 64-76) — CONTRIBUTING.md owns this
- Conventional commits table (lines 99-135) — CONTRIBUTING.md owns this
- Pre-submit checklist (lines 138-168) — CONTRIBUTING.md owns this
- Pull request requirements (lines 170-176) — CONTRIBUTING.md owns this
- Adding dependencies (lines 204-216) — CONTRIBUTING.md owns this

### CONTRIBUTING.md Updates Needed (DVGD-04)
1. Architecture section (lines 44-60): Replace inline architecture table with a reference to `docs/development.md#architecture` for the full overview
2. Add a "Developer Guide" cross-link paragraph in the intro pointing to `https://thatdevstudio.github.io/ztlctl/dev/` for plugin authoring, API reference
3. No content removal — only additions and reference links

---

## Open Questions

1. **mkdocs-shadcn alpha mkdocstrings support — rendering quality**
   - What we know: Theme docs say mkdocstrings is supported (listed in Plugins section); described as alpha status
   - What's unclear: Whether signature sections, docstring parameter tables, and source blocks render correctly with mkdocs-shadcn 0.10.2
   - Recommendation: Add a task to run `mkdocs serve` locally and visually verify output before marking done. The implementer should verify with a single test directive before writing all 5 module directives.

2. **Does the docs CI workflow need mkdocstrings added to pip install?**
   - What we know: The existing CI workflow installs mkdocs via `pip install mkdocs==1.6.1 mkdocs-shadcn==0.10.2 mkdocs-redirects==1.2.2`
   - What's unclear: Exact workflow file content (not read during research)
   - Recommendation: The planner should include a task to update the CI workflow pip install line to add `mkdocstrings[python]>=1.0.3`. This is a required change for DVGD-02 to work in CI.

3. **griffe strict mode / warning suppression in CI**
   - What we know: griffe may emit warnings for unresolvable cross-references in TYPE_CHECKING blocks
   - What's unclear: Whether any warnings would cause a CI failure
   - Recommendation: Use `allow_inspection: false` + `paths: [src]` to force visitor-only mode. If warnings appear, add `griffe_unsupported_logs: "debug"` option.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3 |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/test_docs.py -x` (if exists) |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

This is a documentation-only phase. The primary validation is `mkdocs build` succeeding cleanly, not pytest unit tests.

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DVGD-01 | plugin-guide.md exists with all hookspec signatures | manual | `mkdocs build` (build must pass) | ❌ Wave 0 (new file) |
| DVGD-02 | api-reference.md exists; mkdocstrings generates output for all 5 modules | manual | `mkdocs build` (griffe must not error) | ❌ Wave 0 (new file) |
| DVGD-03 | development.md contains action model + ActionRegistry sections | manual | visual review | existing file |
| DVGD-04 | CONTRIBUTING.md cross-links to developer guide | manual | visual review | existing file |

**Note on automated validation:** `mkdocs build` is the functional gate for DVGD-02. A passing build confirms griffe resolved all modules. For DVGD-01, DVGD-03, DVGD-04, the validation is human review of content accuracy.

### Sampling Rate
- **Per task commit:** `uv run mkdocs build` in the docs env (or skip if mkdocstrings not yet wired)
- **Per wave merge:** `uv run mkdocs build` must succeed cleanly
- **Phase gate:** `mkdocs build` clean + visual review of rendered output before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `docs/plugin-guide.md` — new file; no pre-existing content to test against
- [ ] `docs/api-reference.md` — new file; mkdocstrings directives must be written
- [ ] `pyproject.toml` dev dep: `uv add --group dev "mkdocstrings[python]>=1.0.3"` — required before any build test
- [ ] CI workflow update — add `mkdocstrings[python]` to pip install line (path not confirmed; planner should locate `.github/workflows/`)

---

## Sources

### Primary (HIGH confidence)
- https://mkdocstrings.github.io/python/usage/ — mkdocstrings-python config options, directive syntax
- https://mkdocstrings.github.io/python/usage/configuration/general/ — show_source, allow_inspection, paths options
- https://mkdocstrings.github.io/python/usage/configuration/headings/ — heading_level, show_root_heading
- https://mkdocstrings.github.io/python/usage/configuration/members/ — members_order, filters, inherited_members
- https://mkdocstrings.github.io/python/usage/configuration/docstrings/ — docstring_style, docstring_section_style
- https://pypi.org/project/mkdocstrings/ — version 1.0.3 confirmed, released 2026-02-07
- https://pypi.org/project/mkdocstrings-python/ — version 2.0.3 confirmed, released 2026-02-20
- `src/ztlctl/plugins/hookspecs.py` — all hookspec signatures extracted (source of truth)
- `src/ztlctl/plugins/contracts.py` — all contract dataclasses extracted (source of truth)
- `src/ztlctl/plugins/_version.py` — PLUGIN_API_VERSION, compatibility window
- `src/ztlctl/actions/definitions.py` — ActionParam, ActionDefinition (source of truth)
- `src/ztlctl/actions/registry.py` — ActionRegistry public API (source of truth)

### Secondary (MEDIUM confidence)
- https://asiffer.github.io/mkdocs-shadcn/ — confirmed mkdocstrings is listed in supported plugins (alpha status warning noted)
- https://github.com/mkdocstrings/griffe — griffe 2.0.0 latest version confirmed

### Tertiary (LOW confidence)
- WebSearch result on MkDocs 2.0 compatibility note — mentioned complex plugins like mkdocstrings may need coordinated builds; not yet relevant at mkdocs 1.6.1

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions confirmed from PyPI API directly
- Architecture: HIGH — extracted from source code (not training data)
- Pitfalls: MEDIUM-HIGH — mkdocs-shadcn alpha status is verified from official theme docs; import pitfall is standard mkdocstrings pattern documented in official usage guide
- Plugin API surface: HIGH — extracted verbatim from source files

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (30 days; mkdocstrings is in active development but config API is stable in 1.x)
