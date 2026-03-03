---
title: Research to ztlctl Mapping
nav_order: 12
---

# Research to ztlctl Mapping

## Why This Guide Exists

The current `ztlctl` product keeps the spirit of the older `research` workspace, but it does not try to reproduce that repository literally.

This guide maps the concepts between the two systems so someone familiar with `research` can understand how the same goals show up in the current product architecture. It is a conceptual bridge, not an automated migration guide.

## High-Level Continuity

What carried forward:

- strong local, file-first durability
- fast indexed retrieval over markdown-backed knowledge
- agent-assisted capture and synthesis
- a distinct human garden layer for slower thinking
- Obsidian as a first-class companion workspace

## Structural Mapping

| `research` | `ztlctl` |
|---|---|
| `conversations/` | Operational session/log state via `ztlctl agent session ...`, not durable conversation markdown files |
| `decisions/` | Decision notes in `notes/` with `type=note` and `subtype=decision` |
| `knowledge/` | Knowledge notes in `notes/` |
| `resources/` | References in `notes/` plus durable `sources/<reference-id>/` bundles |
| `backlog/` | Tasks in `ops/tasks/` |
| `indexes/catalog.db` | `.ztlctl/ztlctl.db` |
| `_index.md`, `id-registry.md`, `changelog.md` | Replaced by query surfaces, DB-backed indexes, and generated/exported review views |
| `.claude/skills` and hook-heavy repo workflow | `workflow export`, MCP, plugin system, and generic CLI surfaces |
| old `.obsidian/` workspace | First-party Obsidian starter kit plugin |
| old `garden/` layer | Restored `garden/` layer in the current Obsidian profile |

## What Changed Intentionally

- There is no durable conversation markdown type in the core product.
- Notes and references use hash-based IDs instead of sequential IDs.
- Decisions are note subtypes rather than a separate top-level directory.
- The first-party Obsidian starter kit is curated and intentionally smaller than the old workspace.
- The current starter kit does not ship `.obsidian/workspace.json`.
- Older plugin extras such as `quickadd`, `periodic-notes`, `auto-note-mover`, `obsidian-linter`, and `various-complements` are intentionally not in the first-party preset.
- Garden maturity language changed from `seedling` to `seed`.

## What Was Restored in Later Phases

- dynamic workspace profiles
- first-party Obsidian starter kit scaffolding
- explicit `garden/` scaffold
- one-shot `.obsidian/` scaffold ownership model

## What Remains Intentionally Different

- export is external, not a live workspace layer
- `garden/` remains human-owned
- `.obsidian/` is scaffolded once, then customized by the user
- migration parity does not drive the product architecture

## If You Are Coming from `research`

- Start a fresh `ztlctl` vault.
- Choose `--profile obsidian`.
- Treat the new vault as a new operating model rather than a drop-in in-place upgrade.
- Manually bring over only human-authored garden material you still value.
- Selectively recreate durable notes, references, and tasks if needed instead of trying to import everything wholesale.

## Migration Tooling Decision

**No-go for now.**

Reasons:

- the old machine-layer directories do not map 1:1 onto the current durable model
- old note, reference, and task identity/storage conventions differ materially from current `ztlctl`
- the old automation layer was heavily Claude- and repo-specific
- the current Obsidian starter kit is intentionally not a literal reconstruction
- garden content is human-authored and better handled manually than by importer heuristics
- importer value is low relative to the risk of carrying forward stale structure and semantics

If migration tooling is revisited later, it should be a narrowly scoped importer for durable machine-layer artifacts only. Sessions, `.obsidian/`, hooks, and workspace automation should remain explicitly out of scope.
