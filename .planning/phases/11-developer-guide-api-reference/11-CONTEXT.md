# Phase 11: Developer Guide + API Reference - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Write developer-facing documentation: plugin authoring guide (tutorial + reference), auto-generated API reference via mkdocstrings/griffe, ActionRegistry architecture overview for contributors, and CONTRIBUTING.md updates with cross-links. All content lives under the Developer Guide nav section. No new features or code changes beyond docs tooling setup.

</domain>

<decisions>
## Implementation Decisions

### API reference generation
- Use mkdocstrings with griffe backend for auto-generated API reference from Python docstrings/type hints
- Add `mkdocstrings[python]` to dev dependencies (griffe is included as a dependency of mkdocstrings-python)
- Configure in mkdocs.yml with `plugins: - mkdocstrings`
- Scope: plugin public API only — hookspecs, contracts, _version (PLUGIN_API_VERSION), ActionDefinition, ActionParam, ActionRegistry
- Do NOT document internal implementation (services, infrastructure, etc.) — that's not part of the plugin API contract
- Create `docs/api-reference.md` that uses `::: ztlctl.plugins.hookspecs` style directives

### Plugin authoring guide
- New `docs/plugin-guide.md` — tutorial-style walkthrough followed by reference sections
- **Tutorial section:** "Build Your First Plugin" — step-by-step from empty Python package to working plugin with:
  - Plugin class with `PLUGIN_API_VERSION = 1`
  - A `post_action` hook implementation
  - A custom `NoteTypeDefinition` registration
  - Plugin config schema (`get_config_schema` + `initialize`)
  - Capability declaration (`declare_capabilities`)
  - `pyproject.toml` entry point registration
- **Reference section:** All hookspecs with signatures, return types, and behavior notes
- Include a complete working example plugin (inline code, not a separate repo)

### Architecture documentation
- Enhance `docs/development.md` with architecture overview:
  - 6-layer package structure diagram (domain → infrastructure → config → services → output → commands)
  - 4-layer action model (Data/Service/Controller/Registry) with flow diagram
  - How CLI and MCP surfaces are auto-generated from ActionRegistry
  - Plugin system integration points (where hooks fire, how custom note types flow through)
- High-level mental model for contributors — not implementation-level detail

### CONTRIBUTING.md updates
- Keep CONTRIBUTING.md as standalone file (GitHub convention)
- Add cross-links from dev guide to CONTRIBUTING.md for setup, branching, commit conventions
- Update CONTRIBUTING.md architecture section to reference the new detailed architecture page
- Ensure no contradictions between CONTRIBUTING.md and docs/development.md

### Nav structure
- Developer Guide section in mkdocs.yml gets new pages:
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

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Plugin API source code (for accurate API docs)
- `src/ztlctl/plugins/hookspecs.py` — All hookspec signatures (290 lines, 15+ hookspecs)
- `src/ztlctl/plugins/contracts.py` — ActionRejection, RenderContribution, PluginMetadata (237 lines)
- `src/ztlctl/plugins/_version.py` — PLUGIN_API_VERSION, check_plugin_api_version, PluginLoadError (64 lines)
- `src/ztlctl/plugins/manager.py` — PluginManager lifecycle, registration, config injection (835 lines)
- `src/ztlctl/actions/definitions.py` — ActionDefinition, ActionParam frozen dataclasses
- `src/ztlctl/actions/registry.py` — ActionRegistry singleton

### Existing docs to enhance
- `docs/development.md` — Current 128-line dev setup doc (foundation for architecture section)
- `docs/mcp.md` — Current 105-line MCP doc (stays in dev guide, may need cross-links)
- `CONTRIBUTING.md` — Current 220-line contributor guide (needs cross-link updates)
- `docs/dev/index.md` — Developer Guide landing page (needs new page entries)

### Built-in plugins as examples
- `src/ztlctl/plugins/builtins/git.py` — Git plugin with post_action, PLUGIN_API_VERSION=1, declare_capabilities
- `src/ztlctl/plugins/builtins/reweave_plugin.py` — Reweave plugin with post_action filtering

### Prior phase context
- `.planning/phases/09-navigation-structure/09-CONTEXT.md` — Nav structure decisions
- `.planning/phases/10-user-guide-content/10-RESEARCH.md` — Plugin behavior details (Git: 6 config fields, Reweave: 5 skip conditions)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/development.md` (128 lines) — has setup, testing, architecture skeleton, branching model
- `CONTRIBUTING.md` (220 lines) — has development setup, architecture overview, commit conventions, pre-commit checklist
- Built-in plugins (git.py, reweave_plugin.py) — real examples of the plugin API in use
- Plugin API surface: 1426 lines across 4 files with type hints and docstrings — excellent mkdocstrings input

### Established Patterns
- mkdocs-shadcn supports mkdocstrings (alpha status per research)
- MkDocs nav is config-driven — new pages added via mkdocs.yml nav section
- llms.txt + gen_llms_full_txt.py need updates for any new pages

### Integration Points
- `mkdocs.yml` nav: Developer Guide section needs new entries
- `pyproject.toml`: needs `mkdocstrings[python]` dev dependency
- `docs/dev/index.md`: landing page needs updated page table
- `docs/llms.txt`: needs new page entries
- `scripts/gen_llms_full_txt.py`: NAV_ORDER needs new pages

</code_context>

<specifics>
## Specific Ideas

- User explicitly said: "developer users should be more technical and walk through how to build plugins with detailed API docs included"
- The plugin API is the primary contract — docs must be accurate against the actual hookspec signatures
- Built-in plugins (git.py, reweave_plugin.py) are the best tutorial examples since they're real, tested code
- mkdocstrings with griffe avoids manual API doc maintenance — docs stay current with code

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 11-developer-guide-api-reference*
*Context gathered: 2026-03-20*
