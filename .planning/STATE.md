---
gsd_state_version: 1.0
milestone: v2.1
milestone_name: Documentation
status: unknown
stopped_at: Completed 11-02-PLAN.md
last_updated: "2026-03-20T19:04:50.986Z"
progress:
  total_phases: 6
  completed_phases: 3
  total_plans: 12
  completed_plans: 10
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-20)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 11 — developer-guide-api-reference

## Current Position

Phase: 11 (developer-guide-api-reference) — EXECUTING
Plan: 3 of 4

## Performance Metrics

**Velocity:**

- Total plans completed: 22 (across v2.0)
- Average duration: ~53 min
- Total execution time: ~19.6 hours

**By Phase (v2.1):**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| — | — | — | — |

**Recent Trend:**

- v2.0 final phases: 4 min, 5 min, ~90 min, ~442 min
- Trend: Varies by phase complexity

*Updated after each plan completion*
| Phase 08-mkdocs-infrastructure P01 | 5 | 1 tasks | 4 files |
| Phase 08-mkdocs-infrastructure P02 | 136 | 2 tasks | 19 files |
| Phase 08-mkdocs-infrastructure P03 | 1 | 1 tasks | 1 files |
| Phase 09-navigation-structure P01 | 1 | 1 tasks | 3 files |
| Phase 09-navigation-structure P02 | 2 | 2 tasks | 3 files |
| Phase 10-user-guide-content P01 | 3 | 1 tasks | 3 files |
| Phase 10-user-guide-content P02 | 4 | 2 tasks | 5 files |
| Phase 10 P03 | 3 | 2 tasks | 2 files |
| Phase 11 P01 | 1 | 2 tasks | 4 files |
| Phase 11 P02 | 2 | 1 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Two-track documentation (user + developer guide): knowledge workers and plugin authors have fundamentally different needs
- llms.txt + MCP doc search for agent accessibility: agents are a primary audience
- mkdocs-shadcn theme (not Material): install via `pip install mkdocs-shadcn`, configure with `theme: name: shadcn`
- Phase 10 and Phase 11 can be parallelized (both depend on Phase 9, not each other)
- [Phase 08-01]: Deleted backlog.md, research-mapping.md, roadmap.md from docs/ — internal planning artifacts must not appear on published MkDocs site
- [Phase 08-01]: docs/index.md For Developers and Agents section reduced to 3 links: agentic-workflows.md, development.md, troubleshooting.md
- [Phase 08-02]: mkdocs.yml at project root with shadcn theme, exclude_docs for plans/, full nav listing all 13 pages
- [Phase 08-02]: site/ added to .gitignore as MkDocs build artifact (auto-fix)
- [Phase 08-03]: workflow-level permissions: contents: write (not job-level) for gh-pages push access
- [Phase 08-03]: pip install (not uv) in CI — docs workflow only needs mkdocs tools, not full ztlctl env
- [Phase 08-03]: Pinned exact versions in CI: mkdocs==1.6.1, mkdocs-shadcn==0.10.2, mkdocs-redirects==1.2.2
- [Phase 09-01]: Pages stay in docs/ root — MkDocs nav nesting is config-driven, no file moves needed (avoids URL breakage)
- [Phase 09-01]: Section index files in docs/guide/ and docs/dev/ subdirs with ../ relative links to docs/*.md targets
- [Phase 09-02]: llms.txt hand-authored (not generated) — spec is stable and file is small enough to maintain manually
- [Phase 09-02]: gen_llms_full_txt.py uses NAV_ORDER (not mkdocs.yml parsing) to stay stdlib-only (no PyYAML dep)
- [Phase 09-02]: strip_frontmatter() silently strips --- blocks before concatenation so YAML never pollutes agent corpus
- [Phase 10-01]: Expanded paradigms.md from 72 to 192 lines preserving original sections verbatim; comparison table + 3 command-sequence scenarios + choose-your-path guidance added
- [Phase 10-01]: Committed untracked docs/plugins.md and mkdocs.yml nav entry (from plan 02) to fix pre-existing broken link blocking mkdocs build --strict
- [Phase 10]: [Phase 10-03]: Recipe walkthroughs inserted after MCP Server Integration section — preserves logical flow from concepts to concrete usage
- [Phase 10]: [Phase 10-03]: Session Lifecycle section placed between Recipe Walkthroughs and Batch Operations — sessions tie recipes together
- [Phase 11]: allow_inspection: false + paths: [src] mandated for mkdocstrings to prevent dynamic import failures in CI docs env (no ztlctl runtime deps installed)
- [Phase 11]: No show_inheritance_diagram in mkdocstrings config — mkdocs-shadcn has alpha-status mkdocstrings support
- [Phase 11-developer-guide-api-reference]: docs/plugin-guide.md: hookspec signatures from source only — read hookspecs.py before writing any signature documentation

### Roadmap Evolution

- Phase 13 added: Switch GitHub Pages deploy to Actions artifact (eliminate gh-pages branch)

### Pending Todos

None yet.

### Blockers/Concerns

- Research noted: `docs/llms.txt` with no YAML front matter may need verification that Jekyll serves it correctly
- Research noted: docs/plans/ is currently publicly served — must be excluded in Phase 8
- Research noted: GitHub Pages has no server-side redirects — redirect stubs (meta-refresh) must be planned before moving files

## Session Continuity

Last session: 2026-03-20T19:04:50.931Z
Stopped at: Completed 11-02-PLAN.md
Resume file: None
