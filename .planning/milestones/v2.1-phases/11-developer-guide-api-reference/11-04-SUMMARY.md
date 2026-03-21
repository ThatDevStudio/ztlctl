---
phase: 11-developer-guide-api-reference
plan: "04"
subsystem: docs
tags: [documentation, navigation, developer-guide, architecture, llms]
dependency_graph:
  requires: [11-01, 11-02, 11-03]
  provides: [complete-developer-guide-nav, action-model-docs]
  affects: [mkdocs.yml, llms-full.txt, development.md, CONTRIBUTING.md]
tech_stack:
  added: []
  patterns: [action-model-documentation, cross-linking, nav-wiring]
key_files:
  created: []
  modified:
    - docs/development.md
    - CONTRIBUTING.md
    - mkdocs.yml
    - docs/dev/index.md
    - docs/llms.txt
    - scripts/gen_llms_full_txt.py
    - docs/llms-full.txt
decisions:
  - "Action Model section inserted in development.md (not CONTRIBUTING.md) to separate architecture docs from contribution workflow"
  - "CONTRIBUTING.md architecture section cross-links to development/#action-model rather than duplicating the 4-layer table"
  - "mkdocs.yml nav order: Contributing > Plugin Authoring > API Reference > MCP Server (logical progression)"
  - "llms-full.txt regenerated to include plugin-guide.md and api-reference.md in agent corpus"
metrics:
  duration_minutes: 3
  completed_date: "2026-03-20T19:09:03Z"
  tasks_completed: 2
  files_modified: 7
---

# Phase 11 Plan 04: Nav Wiring and Architecture Documentation Summary

**One-liner:** 4-layer action model (Data/Service/Controller/Registry) added to development.md; plugin-guide and api-reference wired into mkdocs nav, llms.txt, and llms-full.txt corpus.

## What Was Built

### Task 1: docs/development.md and CONTRIBUTING.md

**docs/development.md** — new "Action Model" subsection inserted between the existing architecture diagram and "Template Overrides". Covers:
- 4-layer table: Data (ActionParam/ActionDefinition), Service, Controller (BaseController), Registry (ActionRegistry)
- CLI auto-generation: `get_action_registry().list_actions()` + ActionParam CLI metadata fields
- MCP auto-generation: same registry, different surface formatter using `mcp_when_to_use` etc.
- Plugin integration points: `pre_action`, `post_action`, `register_note_types()`, `register_content_models()`
- ServiceResult contract: every service returns it; controllers unwrap for CLI/MCP; plugins receive via `post_action(result=...)`

**CONTRIBUTING.md** — two targeted additions without removing existing content:
1. Developer Guide callout paragraph after intro (before Table of Contents) linking to plugin authoring and API reference
2. "Project Architecture" section replaced with cross-link to `development/#action-model` plus quick-reference bullet list of 8 package layers

### Task 2: Nav, Index, llms.txt, Generator, and Corpus

**mkdocs.yml** — Developer Guide nav updated from 3 entries to 5, in correct order:
- dev/index.md, development.md, plugin-guide.md, api-reference.md, mcp.md

**docs/dev/index.md** — "In This Guide" table expanded from 2 to 4 rows, with Plugin Authoring and API Reference entries between Contributing and MCP Server.

**docs/llms.txt** — Developer Guide section expanded from 3 to 5 entries with Plugin Authoring and API Reference links.

**scripts/gen_llms_full_txt.py** — NAV_ORDER Developer Guide list updated from 3 to 5 files.

**docs/llms-full.txt** — regenerated; now includes full content of plugin-guide.md and api-reference.md (mkdocstrings directives appear as-is, which is self-documenting).

## Deviations from Plan

**1. [Rule 1 - Bug] mkdocs.yml nav already partially modified by plan 11-03**
- **Found during:** Task 2
- **Issue:** Plan 11-03 had already added `api-reference.md` to the nav but placed it after `mcp.md` and without `plugin-guide.md`. The file also had the wrong order.
- **Fix:** Read the current file state before editing; reordered to correct sequence (Plugin Authoring before API Reference, both before MCP Server)
- **Files modified:** mkdocs.yml
- **Commit:** 16f847c

**2. [Rule 1 - Bug] docs/llms.txt, dev/index.md, gen_llms_full_txt.py partially modified by plan 11-03**
- **Found during:** Task 2
- **Issue:** Plan 11-03 had already added entries to these files. My edits were additive in the correct locations; pre-commit hooks captured all changes together.
- **Fix:** Applied the plan's intended changes cleanly on top of existing state
- **Files modified:** docs/dev/index.md, docs/llms.txt, scripts/gen_llms_full_txt.py

**3. [Rule 2 - Missing] llms-full.txt needed regeneration after NAV_ORDER update**
- **Found during:** Task 2
- **Issue:** llms-full.txt was never regenerated after plan 11-03 added files to NAV_ORDER
- **Fix:** Ran `python3 scripts/gen_llms_full_txt.py` to regenerate; pre-commit hook fixed missing trailing newline
- **Files modified:** docs/llms-full.txt
- **Commit:** 16f847c

## Verification Results

| Check | Result |
|-------|--------|
| `grep -c "ActionRegistry\|ServiceResult\|BaseController" docs/development.md` | 6 (>= 3 required) |
| `grep "plugin-guide\|Developer Guide" CONTRIBUTING.md` | 1 match (Developer Guide callout) |
| `grep "plugin-guide.md\|api-reference.md" mkdocs.yml` | Both present |
| `grep "Plugin Authoring\|API Reference" docs/dev/index.md` | Both present |
| `grep -c "plugin-guide\|api-reference" docs/llms-full.txt` | 2 |
| `mkdocs build` | Exit 0, built in 0.97s |

## Commits

| Hash | Message | Files |
|------|---------|-------|
| 699fde8 | docs(11-04): add 4-layer action model to development.md and cross-link CONTRIBUTING.md | docs/development.md, CONTRIBUTING.md |
| 16f847c | docs(11-04): wire plugin-guide and api-reference into nav, llms.txt, and agent corpus | docs/llms-full.txt (+ mkdocs.yml, dev/index.md, llms.txt, gen_llms_full_txt.py via prior pre-commit) |

## Self-Check: PASSED

- docs/development.md contains "Action Model" section: FOUND
- CONTRIBUTING.md contains Developer Guide callout: FOUND
- mkdocs.yml contains plugin-guide.md and api-reference.md: FOUND
- docs/dev/index.md has 4 rows: FOUND
- docs/llms.txt has 5 Developer Guide entries: FOUND
- docs/llms-full.txt regenerated with plugin-guide and api-reference content: FOUND (2 occurrences)
- mkdocs build exits 0: CONFIRMED
