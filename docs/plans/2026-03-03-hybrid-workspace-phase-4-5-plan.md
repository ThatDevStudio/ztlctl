# Hybrid Workspace Phase 4/5 Implementation Plan

**Date:** 2026-03-03
**Status:** Implemented

## Deliverables

- export/dashboard wording aligned with the hybrid model
- MCP resource descriptions aligned with export purpose
- new `research` to `ztlctl` mapping guide
- explicit migration tooling no-go decision
- backlog/docs closure for `GDN-003`, `ADP-001`, and `ADP-002`

## Work Completed

### 1. Export purpose alignment

- reframed dashboard export as an external review workbench
- renamed the dashboard markdown section from `Garden Backlog` to `Enrichment Backlog`
- preserved compatibility filenames and viewer behavior

### 2. MCP wording cleanup

- kept resource URIs stable
- clarified `ztlctl://review/dashboard` and `ztlctl://garden/backlog` descriptions

### 3. Research mapping guide

- published a dedicated user-facing mapping page
- documented structural continuity and intentional differences
- added practical guidance for users coming from the old workspace

### 4. Migration decision

- recorded a no-go for migration/import tooling for now
- limited any future reconsideration to narrowly scoped machine-layer imports only
