---
gsd_state_version: 1.0
milestone: v3.1
milestone_name: Documentation & Hardening
status: unknown
stopped_at: Completed 25-02-PLAN.md
last_updated: "2026-03-21T23:07:44.067Z"
progress:
  total_phases: 10
  completed_phases: 2
  total_plans: 3
  completed_plans: 3
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-21)

**Core value:** Agents should only ever have to orchestrate the tool — not build custom functionality that is lacking from the tool.
**Current focus:** Phase 25 — new-v3-0-feature-pages

## Current Position

Phase: 25 (new-v3-0-feature-pages) — EXECUTING
Plan: 3 of 3

## Performance Metrics

**Velocity:**

- Total plans completed: 65 (v2.0: 22, v2.1: 21, v3.0: 22 — all prior milestones)
- Average duration: ~53 min (v2.0), varies widely (v2.1, v3.0)
- Total execution time: estimated ~30+ hours across all milestones

**By Phase (v3.0 — most recent):**

| Phase | Plans | Avg/Plan |
|-------|-------|----------|
| 15 Event Model Hardening | 4 | ~117 min |
| 16 Plugin Bridge and Action Executor | 3 | ~98 min |
| 17 Registry Decomposition | 2 | ~11 min |
| 18 Architecture Cleanup | 2 | ~8 min |
| 19 Methodology + Polaris | 3 | ~93 min |
| 20 Session Recall | 2 | ~4 min |
| 21 Contradiction Detection | 2 | ~7 min |
| 22 Ingestion Pipeline | 2 | ~4 min |

**Recent Trend:**

- v3.1 Documentation & Hardening: Not started
- Expected: docs phases lighter than architecture phases (v3.0 avg); infrastructure phase (23) heavier than content phases

*Updated after each plan completion*
| Phase 23 P02 | 8 | 2 tasks | 5 files |
| Phase 23 P01 | 284 | 2 tasks | 8 files |
| Phase 24 P01 | 2 | 2 tasks | 3 files |
| Phase 25 P01 | 2 | 2 tasks | 2 files |
| Phase 25 P02 | 117 | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting v3.1:

- Vale + Google style for prose linting — active voice, second person, present tense, sentence-case headings; Go binary installed via CI action (errata-ai/vale-action@v2)
- pymarkdownlnt (not markdownlint-cli2) for Markdown structure linting — Python-native, uv-compatible, no Node.js
- mkdocs-git-revision-date-localized for git-sourced page dates — always accurate, zero author discipline required
- NEVER use `mkdocs build -v --strict` — confirmed MkDocs bug suppresses strict-mode failures with -v flag; always `mkdocs build --strict` without -v
- lychee for external link checking runs on a schedule only (not per-PR) — avoids network flakiness
- Five new v3.0 feature pages go in `docs/` root (consistent with all v2.1 pages) and require explicit `nav:` registration
- llms.txt and llms-full.txt remain hand-maintained — page count (~25) does not yet justify generator script
- Phase 23 bundles DEBT-09 (IngestService post_action dispatch) and DEBT-10 (stale docstrings) with infra work — both are small code changes that unblock clean CI
- Phase 24 (nav/IA audit) must precede Phase 25 (new pages) — placement in nav must be confirmed before writing begins
- Phases 25, 26, 27 ordered: new pages first (25), then cross-reference updates and index refresh (26), then internal docs (27)
- [Phase 23]: IngestService dispatch fires in _ingest_normalized (note path) and _create_reference_with_bundle (reference path), matching where writes occur
- [Phase 23]: pymarkdown excludes docs/plans/ directory (excluded from MkDocs build); avoids false positives on archived plan files
- [Phase 23]: MD003/MD013/MD022/MD024/MD031/MD032/MD033/MD036/MD040/MD041/MD046 disabled in pymarkdown to match existing docs patterns; gate starts clean and rules tightened as docs are rewritten
- [Phase 24]: Nav order follows Diataxis progression: Tutorial → Explanation → Reference → How-to
- [Phase 24]: 5 placeholder comment slots inserted in mkdocs.yml nav between Configuration and Built-in Plugins for Phase 25 v3.0 feature pages
- [Phase 24]: Documentation Conventions documented in CLAUDE.md: CLI syntax, admonitions (3 types only), cross-referencing, headings (sentence case), Diataxis type definitions
- [Phase 25]: All CLI flags verified against uv run ztlctl --help before writing — never from memory (per STATE.md blocker note)
- [Phase 25]: Polaris check_alignment documented as advisory-only (aligned is always true) reflecting source behavior in check.py
- [Phase 25]: Contradiction CLI routes through check group (check contradictions, check confirm-contradiction), not standalone subcommand
- [Phase 25]: Media ingestion supports 11 formats: ogg/flac/mkv/webm included alongside mp3/m4a/wav/mp4 from TranscriptionService.SUPPORTED_EXTENSIONS

### Pending Todos

- Confirm whether `scripts/gen_llms_txt.py` exists in the codebase before Phase 23 begins (research gap noted in SUMMARY.md)
- Decide Vale local development installation path during Phase 23 (brew install vs. pre-commit auto-download) and document in CONTRIBUTING.md or CLAUDE.md
- Expect one pymarkdownlnt rule-override tuning iteration (especially MD033 for MkDocs admonition HTML) during Phase 23

### Blockers/Concerns

- mkdocs-git-revision-date-localized requires git history on CI checkout — ensure `fetch-depth: 0` in the doc_lint job (shallow clone strips dates)
- Vale `.vale/styles/` directory must be gitignored with `vale sync` run at CI start — do not commit downloaded style packages
- pymarkdownlnt rule overrides for ztlctl docs may need tuning on first scan — MD033 (inline HTML in admonitions) is the most likely conflict
- Every Phase 25 feature page must be verified against the ActionRegistry source and `uv run ztlctl <command> --help` before the page is considered complete — flag names from source, never from memory

## Session Continuity

Last session: 2026-03-21T23:07:44.064Z
Stopped at: Completed 25-02-PLAN.md
Resume file: None
Next action: `/gsd:plan-phase 23`
