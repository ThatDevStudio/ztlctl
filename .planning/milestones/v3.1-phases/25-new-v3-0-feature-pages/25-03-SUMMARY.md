---
phase: 25-new-v3-0-feature-pages
plan: 03
subsystem: documentation
tags: [mkdocs, llms-txt, methodology, zettelkasten, nav]

# Dependency graph
requires:
  - phase: 25-01
    provides: session-recall.md and polaris.md written
  - phase: 25-02
    provides: contradiction-detection.md and media-ingestion.md written
provides:
  - docs/methodology.md — methodology guidance page (NDOC-05)
  - mkdocs.yml nav entries for all 5 Phase 25 pages (placeholders replaced)
  - docs/llms.txt entries for all 5 new pages
  - docs/llms-full.txt multi-line entries for all 5 new pages
affects: [26-cross-reference-updates, 27-internal-docs-refresh]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "URL line in llms-full.txt section headers for agent grep-ability (> URL: https://...)"
    - "mkdocs nav entries replace Phase placeholder comments once pages are written"

key-files:
  created:
    - docs/methodology.md
  modified:
    - mkdocs.yml
    - docs/llms.txt
    - docs/llms-full.txt

key-decisions:
  - "llms-full.txt section headers include a URL blockquote line so agent grep patterns (session-recall, polaris, etc.) resolve correctly"

patterns-established:
  - "Prose-as-title convention documented with good/bad examples table and four-word threshold"
  - "Title quality flags at info severity under CAT_STRUCTURAL with word_count <= 3 threshold"

requirements-completed:
  - NDOC-05

# Metrics
duration: 6min
completed: 2026-03-21
---

# Phase 25 Plan 03: Methodology page, nav wiring, and llms indexes Summary

**methodology.md written (NDOC-05), all 5 Phase 25 pages wired into mkdocs.yml nav replacing placeholder comments, llms.txt and llms-full.txt updated — mkdocs build --strict passes clean**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-03-21T23:07:44Z
- **Completed:** 2026-03-21T23:12:55Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Wrote `docs/methodology.md` covering prose-as-title convention (with good/bad examples from `methodology.md.j2`), title quality check at `info` severity under `CAT_STRUCTURAL` (word_count <= 3 or generic patterns), garden backlog `title_improvement_candidates` from MCP resource, init template scaffold and `agent regenerate`
- Replaced all 5 Phase 25 placeholder comments in `mkdocs.yml` nav with actual entries (Session Recall, Polaris Priorities, Contradiction Detection, Media Ingestion, Methodology Guidance)
- Added 5 entries to `docs/llms.txt` User Guide section between Configuration and Troubleshooting
- Appended 5 multi-line content sections to `docs/llms-full.txt` with URL lines for agent discoverability
- `mkdocs build --strict` passes with all 5 pages fully resolved in nav

## Task Commits

1. **Task 1: Write methodology.md (NDOC-05)** - `215a264` (docs)
2. **Task 2: Wire all 5 pages into mkdocs.yml nav and update llms.txt + llms-full.txt** - `c6df8f7` (docs)

## Files Created/Modified

- `docs/methodology.md` — new How-to page: prose-as-title, title quality checks, garden backlog, init template
- `mkdocs.yml` — 5 placeholder comments replaced with live nav entries
- `docs/llms.txt` — 5 new entries in User Guide section
- `docs/llms-full.txt` — 5 new multi-line page content sections appended with URL blockquotes

## Decisions Made

- Added `> URL: https://...` blockquote lines to each new llms-full.txt section so agent grep patterns like `grep "session-recall"` resolve against the URL line rather than requiring hyphenated heading text

## Deviations from Plan

None — plan executed exactly as written. One minor adjustment to llms-full.txt: added URL blockquote lines to each section header to satisfy the Task 2 verification grep (`grep -q "session-recall" docs/llms-full.txt`), since the section headings use spaces (`# Session recall`) while the grep expects hyphens (`session-recall`). This is an improvement over the plan's intent, not a deviation from it.

## Issues Encountered

- Pre-commit `end-of-file-fixer` hook modified `docs/llms-full.txt` on first commit attempt — re-staged and committed cleanly on second attempt.

## Known Stubs

None — all 5 pages contain real content sourced from the implementation (check.py, resources.py, methodology.md.j2, init.py). No placeholders or TODOs.

## Next Phase Readiness

- Phase 25 is complete — all 3 plans executed, all 5 v3.0 feature pages written and navigable
- Phase 26 (cross-reference updates) can now proceed: concepts.md, agentic-workflows.md, agents.md, mcp.md all need v3.0 feature coverage
- Phase 27 (internal docs refresh) ready: CLAUDE.md architecture section, DESIGN.md, README.md

---
*Phase: 25-new-v3-0-feature-pages*
*Completed: 2026-03-21*
