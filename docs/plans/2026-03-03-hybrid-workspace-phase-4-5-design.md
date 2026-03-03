# Hybrid Workspace Phase 4/5 Design

**Date:** 2026-03-03
**Status:** Implemented

## Goal

Close the remaining hybrid-workspace backlog by clarifying export purpose, publishing a conceptual bridge from `research` to `ztlctl`, and recording a no-go decision for migration tooling.

## Key Decisions

- `export dashboard` remains an external artifact generator
- export wording should explain review purpose without redesigning the artifact model
- compatibility names such as `garden-backlog.json` and `ztlctl://garden/backlog` remain in place
- the `research` mapping guide is user-facing documentation, not only a plan artifact
- migration/import tooling is a no-go for now

## Export Position

The dashboard export is an external review workbench:

- it surfaces machine-layer work queues and review signals
- it provides topic dossiers for review and synthesis
- it complements `garden/`, but does not replace it
- it does not write back into the vault
- it does not mirror `.obsidian/` state

## Adoption Position

The old `research` workspace remains an important ancestor, but not a migration target. The right user guidance is conceptual mapping plus selective manual carry-forward of valuable human-authored material.
