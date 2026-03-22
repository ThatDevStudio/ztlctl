---
phase: 24
plan: 01
subsystem: docs
tags: [documentation, navigation, information-architecture, diataxis]
dependency_graph:
  requires: []
  provides: [diataxis-audit, nav-ordering, documentation-conventions]
  affects: [mkdocs.yml, CLAUDE.md, docs/*]
tech_stack:
  added: []
  patterns: [diataxis-framework, beginner-to-advanced-nav-progression]
key_files:
  created:
    - .planning/phases/24-navigation-and-information-architecture/24-DIATAXIS-AUDIT.md
  modified:
    - mkdocs.yml
    - CLAUDE.md
decisions:
  - "Nav order follows Diataxis progression: Tutorial → Explanation → Reference → How-to"
  - "5 placeholder comment slots inserted between Configuration and Built-in Plugins for Phase 25 feature pages"
  - "plugin-guide.md flagged as high-priority remediation in Phase 26 (Tutorial + Reference mixed)"
  - "Documentation Conventions documented in CLAUDE.md with 5 convention areas: CLI syntax, admonitions (3 types), cross-referencing, headings, Diataxis types"
metrics:
  duration_minutes: 2
  completed_date: "2026-03-21"
  tasks_completed: 2
  files_changed: 3
---

# Phase 24 Plan 01: Diataxis Audit and Navigation Reorder Summary

**One-liner:** Diataxis classification of all 20 docs pages with mkdocs.yml nav reordered to Tutorial→Explanation→Reference→How-to progression and 5 v3.0 feature page placeholder slots inserted.

## What Was Built

### Task 1: Diataxis Audit and Nav Reorder (QUAL-01)

Created `24-DIATAXIS-AUDIT.md` classifying all 20 docs pages:

- **2 Tutorials**: quickstart.md, tutorial.md
- **6 How-tos**: installation.md, obsidian.md, agentic-workflows.md, best-practices.md (mixed), troubleshooting.md, development.md
- **6 References**: commands.md, configuration.md, plugins.md, api-reference.md, mcp.md, agents.md
- **2 Explanations**: concepts.md, paradigms.md
- **4 Landings**: index.md, guide/index.md, dev/index.md, and plugin-guide.md (mixed)

Identified 3 mixed-purpose pages requiring Phase 26 remediation:
- `plugin-guide.md` (High priority — Tutorial + Reference halves both substantial; split recommended)
- `agentic-workflows.md` (Medium — How-to recipes mixed with Reference-style MCP tool coverage)
- `best-practices.md` (Medium — How-to patterns mixed with Explanation conceptual context)

Reordered mkdocs.yml User Guide nav to beginner-to-advanced Diataxis progression:
1. Tutorial → tutorial.md (learning-oriented)
2. Explanation → concepts.md, paradigms.md
3. Reference → commands.md, configuration.md (moved up — reference needed before feature deep-dives)
4. [5 placeholder slots for Phase 25 v3.0 feature pages]
5. Reference → plugins.md
6. How-to → obsidian.md (moved after plugins — extensibility section)
7. How-to → agentic-workflows.md
8. How-to → best-practices.md (moved after agentic-workflows — advanced topic)
9. How-to → troubleshooting.md

### Task 2: Documentation Conventions in CLAUDE.md (QUAL-04)

Added `### Documentation Conventions` subsection to `## Documentation Rules` section in CLAUDE.md, positioned after `### GSD Phase Documentation Convention (DINF-03)` and before `## Architecture`.

Conventions documented:
- **CLI syntax** (Google developer style): `[--flag VALUE]` optional, `REQUIRED` required, bare `ztlctl` inline vs `$ ztlctl` in code blocks, flags from `--help` only
- **Admonition taxonomy** (3 types): `!!! warning`, `!!! note`, `!!! tip` — no other types
- **Cross-referencing**: "What's next" section on every page, relative Markdown links, descriptive link text
- **Headings**: Sentence case, single H1 per page
- **Diataxis content types**: definitions for all four types with "do not mix" rule

## Verification

- `uv run mkdocs build --strict` — exits 0
- 24-DIATAXIS-AUDIT.md exists with 20-row table covering all docs pages
- mkdocs.yml contains all 5 placeholder comment markers
- mkdocs.yml has Command Reference before placeholders, Built-in Plugins after
- CLAUDE.md has `### Documentation Conventions` after GSD convention and before `## Architecture`
- All 7 acceptance criteria strings present in CLAUDE.md

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — this plan produces audit/navigation artifacts only; no content pages with data stubs.

## Self-Check: PASSED

- `.planning/phases/24-navigation-and-information-architecture/24-DIATAXIS-AUDIT.md` — FOUND
- `mkdocs.yml` nav updated with 5 placeholder comments — FOUND
- `CLAUDE.md` Documentation Conventions section — FOUND
- Commits: 6215a9e (Task 1), 4e0f32a (Task 2) — both present in git log
