# Phase 14: Documentation Content Refinement and Quality Pass - Research

**Researched:** 2026-03-20
**Domain:** Technical documentation authoring — content quality, source verification, agent artifact hardening
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- Enhance existing 18 pages in-place — no structural reorganization of nav or file locations
- Add new pages when they add genuine value: `docs/best-practices.md` and `docs/agents.md` confirmed
- Three audiences served: End Users (mentor/teacher tone), Developers (peer/senior tone), Agentic Systems (structured, deterministic)
- Existing two-track nav (User Guide + Developer Guide) is preserved
- Full editorial + source verification: every CLI command verified against Click source, every hookspec verified against `hookspecs.py`, every config option verified against `models.py`
- Consistent heading hierarchy across all pages
- Eliminate hedging language — be decisive and opinionated
- Every page must have at least 2 concrete, real-world examples (not toy examples)
- Anti-pattern sections inline in relevant pages AND as standalone `docs/best-practices.md`
- `docs/agents.md` in Developer Guide nav — machine-readable system manual for LLM consumers
- `docs/agentic-workflows.md` stays human-focused in User Guide
- Fix INT-01: `docs/guide/index.md` missing Built-in Plugins row
- Document `ZTLCTL_DOCS_PATH` env var in user-facing docs
- Note GitHub Pages source setting manual step in troubleshooting or configuration docs (FLOW-01)
- Regenerate `llms-full.txt` and update `llms.txt` after content changes
- Update `NAV_ORDER` in `gen_llms_full_txt.py` for new pages (`best-practices.md`, `agents.md`)
- `mkdocs.yml` nav needs entries for both new pages

### Claude's Discretion

- Exact page structure and heading hierarchy within each enhanced page
- Whether Decisions & Tradeoffs and Evolution Path warrant standalone pages or inline sections
- Order of anti-patterns within best-practices.md
- Depth of agent schema documentation in agents.md
- Whether to add mkdocs admonitions (tips, warnings) for anti-pattern callouts
- Prioritization order of which pages to refine first

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 14 is a pure content phase — no new code, no new infrastructure. The work is to apply a comprehensive editorial and verification pass across all 18 existing documentation pages, create two new pages (`best-practices.md` and `agents.md`), fix three known audit gaps, and harden agent-facing artifacts.

The critical discipline for this phase is source verification before writing. Every CLI example must be traced to Click command definitions, every hookspec signature must be read from `hookspecs.py`, and every config option must be verified against `models.py`. The audit already found one discrepancy (configuration.md shows `[git]` section at top-level when git config is actually under `[plugins.git]` in the plugin system — but this is intentional per the two config models). More discrepancies likely exist in other pages.

The two new pages serve distinct purposes and audiences: `best-practices.md` is a human-readable aggregation of opinionated guidance across all workflows; `agents.md` is a machine-readable system manual with structured schemas and deterministic interaction flows for LLM consumers. These are not duplicates — they serve fundamentally different reading patterns.

**Primary recommendation:** Work page-by-page systematically. Read source first, verify examples, then enhance content. Do not edit docs from memory — every claim must be confirmed against source.

---

## Standard Stack

### Core (documentation tooling — already configured, no changes needed)

| Tool | Version | Purpose | Status |
|------|---------|---------|--------|
| MkDocs | 1.6.1 (pinned in CI) | Doc site build | Already configured |
| mkdocs-shadcn | 0.10.2 (pinned in CI) | Theme with admonitions, code blocks, tables | Already configured |
| mkdocstrings | configured | Auto-generated API reference | Already configured |
| MkDocs admonitions | built-in | `!!! note`, `!!! warning`, `!!! tip` callout blocks | Available, use for anti-patterns |

### MkDocs Admonition Syntax (verified against existing usage in plugins.md)

```markdown
!!! note
    Content here.

!!! warning
    Content here.

!!! tip
    Content here.
```

The shadcn theme renders admonitions correctly — `plugins.md` already uses `!!! note` and `!!! warning` successfully (confirmed by reading the file).

### No New Dependencies

This phase requires zero new packages. All tools are already installed and configured.

---

## Architecture Patterns

### Recommended Page Structure

Every page should follow this hierarchy:

```
---
title: Page Title
---

# Page Title

[1-2 sentence orientation — what this page covers and who it's for]

## [Primary Section]

[Content with concrete examples]

### [Subsection]

## [Secondary Section]

## [Anti-Patterns / Common Mistakes] (where applicable)

## Next Steps

[2-4 cross-links to related pages]
```

### Heading Hierarchy Rules

- H1: Page title (matches frontmatter `title:`)
- H2: Major sections (appear in ToC sidebar)
- H3: Subsections within a major section
- H4: Sub-subsections only when genuinely needed — avoid nesting depth > H3 in most pages

### Audience-Tone Matrix

| Audience | Pages | Tone |
|----------|-------|------|
| End Users | index.md, installation.md, quickstart.md, tutorial.md, concepts.md, paradigms.md, obsidian.md, plugins.md, agentic-workflows.md, commands.md, configuration.md, troubleshooting.md, guide/index.md, best-practices.md | Mentor/teacher — teach the "why" before the "what", concrete examples, decisive guidance |
| Developers | development.md, plugin-guide.md, api-reference.md, mcp.md, dev/index.md, agents.md | Peer/senior — assume competence, skip basics, explain architectural decisions |
| Agents | agents.md, llms.txt, llms-full.txt | Structured/deterministic — structured data over prose, schemas, constraint rules, no ambiguity |

### Content Depth Anchors

From reading existing pages:
- `plugins.md` (244 lines) sets the reference-page depth: concept + config table + common scenarios
- `agentic-workflows.md` (485 lines) sets the workflow-walkthrough depth: layered commands + contextual callouts
- `plugin-guide.md` (719 lines) sets the tutorial depth: step-by-step with full code examples

New pages should target appropriate depth for their type:
- `best-practices.md`: 200-350 lines (aggregation, not tutorials)
- `agents.md`: 300-500 lines (structured schemas + interaction flows)

### mkdocs.yml Nav Additions

Two new entries required. Based on CONTEXT.md decisions:

```yaml
nav:
  - User Guide:
    - ...
    - Best Practices: best-practices.md   # Add after Troubleshooting
  - Developer Guide:
    - ...
    - Agents: agents.md                   # Add after MCP Server
```

Exact position is Claude's discretion — recommended: Best Practices last in User Guide, Agents last in Developer Guide (current last is MCP Server).

### gen_llms_full_txt.py NAV_ORDER Addition

```python
NAV_ORDER = [
    ("Getting Started", ["index.md", "installation.md", "quickstart.md"]),
    (
        "User Guide",
        [
            "guide/index.md", "tutorial.md", "concepts.md", "paradigms.md",
            "obsidian.md", "plugins.md", "agentic-workflows.md",
            "commands.md", "configuration.md", "troubleshooting.md",
            "best-practices.md",   # ADD HERE
        ],
    ),
    (
        "Developer Guide",
        [
            "dev/index.md", "development.md", "plugin-guide.md",
            "api-reference.md", "mcp.md",
            "agents.md",           # ADD HERE
        ],
    ),
]
```

---

## Source Verification Findings

This section documents what was verified by reading source code and existing docs. Implementers MUST re-verify before editing each page.

### Config Discrepancy: configuration.md vs models.py

**Issue:** `configuration.md` shows a top-level `[git]` section in the TOML example:
```toml
[git]
enabled = true
auto_push = true
commit_style = "conventional"
```

**Source truth:** `models.py` has two separate models:
- `GitConfig` (lines 175-185) — fields: `enabled`, `branch`, `auto_push`, `commit_style`, `batch_commits`, `auto_ignore`
- `PluginsConfig` (lines 149-172) — `git: dict[str, Any]` as plugin config via `[plugins.git]`

**Resolution:** `configuration.md` shows the legacy `[git]` section. The correct user-facing TOML is `[plugins.git]` (as correctly shown in `plugins.md`). The `configuration.md` example is outdated and must be updated.

**Additional undocumented fields in `AgentContextConfig`:**
`configuration.md` documents `layer_2_max_notes` and `layer_3_max_hops` but omits `layer_0_min` (default: 500) and `layer_1_min` (default: 1000) from `AgentContextConfig`.

**Additional undocumented fields in `SearchConfig`:**
`configuration.md` documents `semantic_weight` and `half_life_days` but omits `semantic_enabled` (default: false), `embedding_model` (default: "local"), and `embedding_dim` (default: 384).

**Additional undocumented fields in `SessionConfig`:**
`configuration.md` documents 3 session fields but omits `orphan_reweave_threshold` (default: 0.2).

**Missing `[tags]` section entirely:**
`TagsConfig` exists in `models.py` with `auto_register: bool = True` but is not documented in `configuration.md`.

**Missing `[workflow]` section:**
`WorkflowConfig` exists with `template` and `skill_set` fields, not documented.

### Hookspec Verification (hookspecs.py confirmed)

The `plugin-guide.md` claims "16 hookspecs" in its introduction. The actual count from `hookspecs.py`:

**Active (non-deprecated) hookspecs:**
1. `pre_action` (firstresult=True)
2. `post_action`
3. `get_config_schema` (firstresult=True)
4. `initialize`
5. `register_content_models`
6. `register_cli_commands`
7. `register_mcp_tools`
8. `register_mcp_resources`
9. `register_mcp_prompts`
10. `register_workflow_modules`
11. `register_workspace_profiles`
12. `register_vault_init_steps`
13. `register_source_providers`
14. `register_note_types`
15. `register_render_contributions`
16. `declare_capabilities`

**Deprecated hookspecs (still callable but marked deprecated):**
17. `post_create`
18. `post_update`
19. `post_close`
20. `post_reweave`
21. `post_session_start`
22. `post_session_close`
23. `post_check`
24. `post_init`
25. `post_init_profile`

Total: 16 active + 9 deprecated = 25 hookspecs. The "16 hookspecs" claim in `plugin-guide.md` refers to the active non-deprecated set — this is accurate but should be stated explicitly. The deprecated hookspecs exist and work — the docs should acknowledge them with a deprecation callout rather than pretending they don't exist.

### ZTLCTL_DOCS_PATH Env Var (confirmed from source)

`src/ztlctl/services/docs.py` lines 42-59 confirm:
- `ZTLCTL_DOCS_PATH` environment variable overrides the package-relative docs path
- When not set, falls back to `<repo_root>/docs` (only works in editable/source installs)
- Without editable install and without `ZTLCTL_DOCS_PATH`, `ztlctl docs search` returns an error

This must be documented in:
1. `configuration.md` — under a new "Special Environment Variables" or inline in the Environment Variables section
2. `troubleshooting.md` — add "ztlctl docs search returns 'docs path not found'" entry

### Known Audit Gaps (from MILESTONE-AUDIT.md)

| Gap ID | Location | Fix Required |
|--------|----------|-------------|
| INT-01 | `docs/guide/index.md` | Add Built-in Plugins row to "In This Guide" table |
| FLOW-01 | `troubleshooting.md` or `configuration.md` | Add note about GitHub Pages source setting manual step |
| (unnamed) | `configuration.md` | Document `ZTLCTL_DOCS_PATH` env var |

### llms.txt vs Nav — Already Includes plugins.md

Verified: `docs/llms.txt` line 19 already includes the Built-in Plugins entry:
```
- [Built-in Plugins](https://thatdevstudio.github.io/ztlctl/plugins/): ...
```
The gap is only in `guide/index.md` — the llms.txt is correct.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Anti-pattern callouts | Custom HTML divs or raw markdown blockquotes | MkDocs admonitions (`!!! warning`, `!!! tip`) | Already configured, shadcn renders them correctly |
| Agent schemas | Prose descriptions | Markdown tables + code blocks | Machine-parseable, consistent, no custom format needed |
| TOML config examples | Generated output | Read `models.py` and write verified examples by hand | Only way to guarantee accuracy |
| Cross-linking | Global find-replace | Targeted additions at "Next Steps" sections | Surgical — avoids breaking existing anchor links |

**Key insight:** This phase succeeds or fails based on source-code discipline. Every piece of content that claims to document a feature must be traced to the code that implements it. Docs written from memory or prior docs will perpetuate existing errors.

---

## Common Pitfalls

### Pitfall 1: Copying Config Examples Without Verification

**What goes wrong:** Existing `configuration.md` has the `[git]` section at top-level — this is wrong. Editors who copy from existing docs propagate the error.

**Why it happens:** The git plugin config moved from `[git]` to `[plugins.git]` at some point. The docs were not updated in sync.

**How to avoid:** Always read `models.py` before writing any TOML example. The canonical config section names are the Pydantic class names lowercased (`[reweave]`, `[garden]`, `[session]`, etc.) except for plugin configs which live under `[plugins.<name>]`.

**Warning signs:** Any TOML block with a top-level `[git]` key is wrong. Any missing fields compared to the Pydantic model is a gap.

### Pitfall 2: Writing hookspec signatures from memory

**What goes wrong:** Hookspec signatures have precise type annotations and `firstresult` behavior — getting these wrong misleads plugin authors.

**Why it happens:** Signatures look simple but have important details (`firstresult=True`, `warn_on_impl=DeprecationWarning`, `Any` vs specific types).

**How to avoid:** Read `hookspecs.py` directly. Copy signatures verbatim. Note deprecated hookspecs with `!!! warning` admonitions.

### Pitfall 3: agents.md becoming another agentic-workflows.md

**What goes wrong:** agents.md drifts toward human-readable workflow narrative, duplicating agentic-workflows.md.

**Why it happens:** It's easier to write prose than to write structured schemas.

**How to avoid:** agents.md must prioritize machine-parseable content: tables, structured lists, explicit schemas with field names and types, deterministic flow steps. Prose is a last resort. If a concept can be expressed as a table or schema, use the table.

### Pitfall 4: Over-engineering best-practices.md

**What goes wrong:** best-practices.md becomes a 1000-line page that restates everything from other pages.

**Why it happens:** "Best practices" is a broad term.

**How to avoid:** best-practices.md is a reference destination for opinionated decisions. Each entry should be: anti-pattern (bad) → why it's bad → correct pattern (good). Keep entries concise. Cross-link to the authoritative page for full context. Target 200-350 lines.

### Pitfall 5: Breaking llms-full.txt sync

**What goes wrong:** New pages added but `gen_llms_full_txt.py` NAV_ORDER not updated — new pages excluded from agent corpus.

**Why it happens:** The script and mkdocs.yml are independent files that must stay in sync manually.

**How to avoid:** Any plan that adds a new page to mkdocs.yml nav MUST also update NAV_ORDER in `gen_llms_full_txt.py` and regenerate `llms-full.txt` in the same commit.

---

## New Pages: Content Specifications

### best-practices.md

**Nav location:** User Guide, last entry
**Audience:** End Users (and implicitly Developers reading about usage patterns)
**Purpose:** Opinionated aggregation of anti-patterns and correct patterns from across the system

**Recommended structure:**
```
# Best Practices

[1-2 sentence intro: this is the ThatDev opinion page]

## Vault Initialization

## Note Creation

## Tagging

## Linking and Reweave

## Session Management

## Plugin Configuration

## Agent Workflows

## What Not to Do (Anti-Patterns Summary)

## Next Steps
```

**Content sources to mine:**
- `plugins.md` — batch mode vs immediate mode pitfall
- `concepts.md` — tag format domain/scope
- `agentic-workflows.md` — session discipline
- `tutorial.md` — workflow patterns
- `configuration.md` — threshold tuning

### agents.md

**Nav location:** Developer Guide, last entry
**Audience:** LLM agents consuming ztlctl via MCP or CLI
**Purpose:** Machine-readable system manual — schemas, constraints, interaction flows

**Recommended structure:**
```
# Agent System Manual

[1 sentence: this page is for LLM systems, not human users]

## System Capabilities

[Table: capability name, access method (CLI/MCP), category]

## Entity Schemas

### Note
### Reference
### Task
### Session (Log)

## Lifecycle State Machines

[State diagrams as ASCII or structured tables]

## Constraint Rules

[What is allowed vs not allowed — explicit rules]

## Deterministic Interaction Flows

### Research Capture Flow
### Knowledge Retrieval Flow
### Session Management Flow

## Input/Output Schemas

### Creating Content
### Querying Content
### MCP Tool Call Format

## Error Handling

[Known error codes and recovery actions]
```

---

## Code Examples

### MkDocs Admonition Anti-Pattern Pattern

```markdown
!!! warning "Anti-Pattern: Tagging without domain/scope"
    Don't use bare tags like `--tags "python"`. Use `domain/scope` format:

    ```bash
    # Wrong — unscoped tag
    ztlctl create note "FastAPI guide" --tags "python"

    # Right — scoped tag enables filtering
    ztlctl create note "FastAPI guide" --tags "lang/python,framework/fastapi"
    ```

    Unscoped tags work but emit a warning and cannot be filtered with `--tag "domain/..."`.
```

### guide/index.md Fix (INT-01)

Add to the "In This Guide" table after the Obsidian Starter Kit row:

```markdown
| [Built-in Plugins](../plugins.md) | Git and Reweave plugin guides — config, triggers, and scenarios |
```

### troubleshooting.md Addition (FLOW-01 + ZTLCTL_DOCS_PATH)

```markdown
### GitHub Pages not updating after deploy

**Cause**: The GitHub Pages source must be manually set to "GitHub Actions" in repo settings.

**Fix**:
1. Go to your repository → Settings → Pages
2. Under "Build and deployment" → Source → select "GitHub Actions"
3. Trigger a new deploy (push any change) or re-run the last workflow

### "ztlctl docs search" returns "docs path not found"

**Cause**: `ztlctl docs search` requires access to the `docs/` directory. In a pip-installed (non-editable) environment, the package-relative path discovery fails.

**Fix**:
```bash
# Point ztlctl to your local docs checkout
export ZTLCTL_DOCS_PATH=/path/to/ztlctl/docs
ztlctl docs search "your query"
```

This is the designed behavior — `ZTLCTL_DOCS_PATH` is the user-facing override for non-editable installs.
```

### configuration.md Plugin Git Section Fix

Replace the incorrect `[git]` block with:

```toml
[plugins.git]
enabled = true
batch_commits = true
auto_push = false
auto_ignore = true
branch = "develop"
commit_style = "conventional"
```

---

## State of the Art

| Area | Current State | What This Phase Changes |
|------|---------------|------------------------|
| configuration.md | Shows incorrect `[git]` top-level section; missing `[tags]`, `[workflow]` sections; missing several fields | Correct to match models.py exactly |
| guide/index.md | Missing Built-in Plugins row (INT-01) | Add row |
| troubleshooting.md | Missing ZTLCTL_DOCS_PATH docs, missing Pages source setting step | Add both |
| plugin-guide.md | 16 active hookspecs documented, 9 deprecated not mentioned | Add deprecation callout section |
| agents.md | Does not exist | Create from scratch |
| best-practices.md | Does not exist | Create from scratch |
| llms.txt | Correct (already has plugins.md) | Add entries for new pages |
| llms-full.txt | Missing new pages (they don't exist yet) | Regenerate after new pages are written |

---

## Open Questions

1. **FLOW-01 placement: troubleshooting.md vs configuration.md?**
   - What we know: The manual step is a one-time repo setup (not a recurring config option), and it's GitHub-specific
   - What's unclear: Is it better in "Troubleshooting" (reactive) or somewhere in the deployment/infrastructure docs?
   - Recommendation: troubleshooting.md is the right home — users hit this after a failed deploy attempt

2. **How many pages need significant rewriting vs light touch?**
   - From reading: `installation.md` (69 lines) and `quickstart.md` (50 lines) are short and accurate but sparse — they need more real-world examples
   - `concepts.md` (91 lines) is accurate but thin — could benefit from a lifecycle state diagram or richer examples
   - `development.md` (154 lines) is accurate and complete — light touch
   - `agentic-workflows.md` (485 lines) is already deep — verify examples, add anti-patterns section
   - Recommendation: treat each page independently; verify first, then judge depth needed

3. **agents.md: Should it document MCP tool call signatures explicitly?**
   - What we know: MCP tools are documented in mcp.md at a category level; full tool signatures are auto-generated
   - What's unclear: Whether repeating tool call schemas in agents.md creates maintenance burden
   - Recommendation: Document interaction patterns and key schemas; link to mcp.md for full tool catalog; avoid duplicating the full tool list

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (uv run pytest) |
| Config file | pyproject.toml |
| Quick run command | `uv run pytest tests/unit/ -x -q` |
| Full suite command | `uv run pytest` |

### Phase Requirements Mapping

This phase has no mapped requirement IDs — it is a quality improvement phase addressing content gaps across previously-completed requirements. Validation is process-based:

| Check | Type | Method |
|-------|------|--------|
| `mkdocs build --strict` passes | build | `uv run --with mkdocs --with mkdocs-shadcn mkdocs build --strict` |
| All 18 pages render without errors | build | covered by build check |
| New pages appear in nav | visual | manual check after build |
| llms-full.txt includes new pages | content | `grep "best-practices\|agents" docs/llms-full.txt` |
| INT-01 fix present | content | `grep "Built-in Plugins" docs/guide/index.md` |
| ZTLCTL_DOCS_PATH documented | content | `grep "ZTLCTL_DOCS_PATH" docs/troubleshooting.md docs/configuration.md` |
| No `[git]` top-level in configuration.md | content | `grep "^\[git\]" docs/configuration.md` (should return nothing) |

### Sampling Rate

- **Per task commit:** `uv run --with mkdocs --with mkdocs-shadcn mkdocs build --strict` — catches broken links and render errors immediately
- **Per wave merge:** Full suite: `uv run pytest` — no new Python code changes so test suite should stay green throughout
- **Phase gate:** `mkdocs build --strict` green + all content checks pass before `/gsd:verify-work`

### Wave 0 Gaps

None — no new test files needed. Existing infrastructure (mkdocs build + pytest suite) covers all phase validation needs. No Python code changes in this phase.

---

## Sources

### Primary (HIGH confidence)

- Read directly: `src/ztlctl/plugins/hookspecs.py` — all hookspec signatures and deprecation markers
- Read directly: `src/ztlctl/config/models.py` — all config section models and defaults
- Read directly: `scripts/gen_llms_full_txt.py` — NAV_ORDER structure and update requirements
- Read directly: `mkdocs.yml` — nav structure, plugin config, markdown extensions
- Read directly: All 18 `docs/*.md` files (18 pages total)
- Read directly: `docs/guide/index.md`, `docs/dev/index.md`, `docs/llms.txt`
- Read directly: `.planning/v2.1-MILESTONE-AUDIT.md` — confirmed audit gaps
- Read directly: `src/ztlctl/services/docs.py` — confirmed ZTLCTL_DOCS_PATH behavior

### Secondary (MEDIUM confidence)

- CONTEXT.md decisions (user-confirmed) — scope, tone, new page specs
- STATE.md accumulated decisions — phase history and precedent decisions

### Tertiary (LOW confidence)

None — all findings from direct source code and file reads.

---

## Metadata

**Confidence breakdown:**
- Source verification findings: HIGH — read directly from source files
- New page content specifications: MEDIUM — based on CONTEXT.md decisions and patterns from existing pages
- Pitfalls: HIGH — confirmed by reading existing docs and source mismatches
- Validation approach: HIGH — confirmed mkdocs build pipeline from phases 8-13

**Research date:** 2026-03-20
**Valid until:** Stable — no moving dependencies. Content docs don't expire unless source code changes.
