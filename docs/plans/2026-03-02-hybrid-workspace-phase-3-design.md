# Hybrid Workspace Phase 3 Design

**Date:** 2026-03-02
**Status:** Implemented

## Goal

Phase 3 turns the first-party `obsidian` profile into a real starter kit and adds a plugin-executed vault-init step surface that can both perform setup work and emit structured next-step guidance.

## Key Decisions

- `obsidian` remains a first-party profile plugin, not a core-owned branch
- plugins can now contribute ordered init steps through `register_vault_init_steps()`
- init steps can create files, emit warnings, and return structured setup instructions
- the Obsidian starter kit ships config files and install guidance only; it does not vendor or download community plugin binaries
- `.obsidian/` is profile-managed
- `garden/` is scaffolded by the Obsidian profile and then treated as human-managed
- current core indexing still covers only `notes/` and `ops/`

## Starter Kit Scope

The starter kit now scaffolds:

- `.obsidian/` workspace config
- Obsidian snippets for both ztlctl and garden layers
- plugin config for `folder-notes`, `omnisearch`, and `obsidian-book-search-plugin`
- `garden/README.md`
- `garden/notes/`, `garden/groves/`, `garden/library/`, `garden/canvases/`, `garden/attachments/`
- `garden/templates/note.md`, `grove.md`, and `book.md`

The curated community-plugin preset is:

- `dataview`
- `templater-obsidian`
- `folder-notes`
- `omnisearch`
- `obsidian-book-search-plugin`

## Init UX

`ztlctl init --profile obsidian` now prints a `Next steps` section and returns the same checklist in structured result data. The checklist covers:

- community plugin installation
- plugin enablement and reload guidance
- verification of note location, attachments, templates, snippets, and graph defaults
