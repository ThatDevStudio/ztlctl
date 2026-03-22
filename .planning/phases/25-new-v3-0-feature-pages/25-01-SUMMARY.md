---
phase: 25-new-v3-0-feature-pages
plan: "01"
subsystem: docs
tags: [documentation, session-recall, polaris, v3.0-features, NDOC-01, NDOC-02]
dependency_graph:
  requires: [24-01]
  provides: [NDOC-01, NDOC-02]
  affects: [docs/session-recall.md, docs/polaris.md]
tech_stack:
  added: []
  patterns: [diataxis-how-to, google-cli-syntax, source-verified-examples]
key_files:
  created:
    - docs/session-recall.md
    - docs/polaris.md
  modified: []
decisions:
  - "All CLI flags verified against uv run ztlctl session recall-* --help and uv run ztlctl check alignment --help before writing — never from memory"
  - "Polaris documented as advisory-only (aligned is always true) to accurately reflect the source behavior"
  - "ztlctl://sessions/recent resource documented alongside MCP tools (not a tool, a resource) for clarity"
metrics:
  duration: "2 min"
  completed: "2026-03-21"
  tasks_completed: 2
  files_created: 2
  files_modified: 0
---

# Phase 25 Plan 01: New v3.0 Feature Pages (Session Recall + Polaris) Summary

**One-liner:** Two How-to docs pages for v3.0 session recall (temporal/topic/topology queries + MCP tools) and polaris priorities (init scaffold, context assembly Layer 1, check_alignment action).

## What Was Built

### Task 1: docs/session-recall.md (NDOC-01)

Complete How-to guide for the three session recall modes:

- **Temporal recall** — `ztlctl session recall-temporal [--from-date TEXT] [--to-date TEXT]`, flags verified from `--help`
- **Topic recall** — `ztlctl session recall-topic QUERY`, positional argument verified from `--help`
- **Topology recall** — `ztlctl session recall-topology [--limit INTEGER]`, flag verified from `--help`
- **MCP tools table** — `recall_temporal`, `recall_topic`, `recall_topology` with parameter details from `_session.py` ActionDefinitions
- **MCP resource** — `ztlctl://sessions/recent` with example JSON payload from `resources.py`
- **Agent workflow** — 4-step example using `ztlctl://sessions/recent` → `recall_temporal` → `recall_topic` → `start`
- **Result field tables** per recall mode
- Sentence-case headings, 3-type admonitions only, "What's next" with 3 links

### Task 2: docs/polaris.md (NDOC-02)

Complete How-to guide for the polaris priorities layer:

- **The polaris document** — location (`garden/groves/polaris.md`), structure (Mission/Current Priorities/Decision Principles)
- **Init scaffold** — `polaris.md.j2` template with exact rendered placeholder structure
- **MCP resource** — `ztlctl://polaris` documented with example response for missing-file case
- **Context assembly integration** — Layer 1 placement, 500-token budget cap, truncation behavior documented from `context.py`
- **Alignment checking** — `ztlctl check alignment --decision TEXT`, verified from `--help`; advisory-only semantics documented (`aligned` always `true`)
- **Agent decision workflow** — 4-step example: read polaris → `check_alignment` → proceed with context → `create_note --subtype decision`
- Sentence-case headings, 3-type admonitions only, "What's next" with 3 links

## Deviations from Plan

None — plan executed exactly as written.

## Commits

| Task | File | Commit |
|------|------|--------|
| 1 | docs/session-recall.md | c8a3d64 |
| 2 | docs/polaris.md | e08342b |

## Known Stubs

None. Both pages are fully populated from source-verified content.

## Self-Check: PASSED

- `docs/session-recall.md` exists — FOUND
- `docs/polaris.md` exists — FOUND
- Commit c8a3d64 exists — FOUND
- Commit e08342b exists — FOUND
