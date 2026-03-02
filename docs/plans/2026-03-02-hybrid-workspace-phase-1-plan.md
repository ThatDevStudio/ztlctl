# Hybrid Workspace Phase 1 Implementation Plan

**Date:** 2026-03-02
**Status:** Approved

## Goal

Implement the Phase 1 workspace-profile architecture without yet enabling plugin-driven profile routing.

## Tasks

### 1. Add canonical profile helpers

- add `src/ztlctl/workspace_profiles.py`
- normalize profile aliases and legacy client inputs
- keep dashboard viewer normalization separate
- expose built-in profile metadata and scaffolding hooks

### 2. Migrate config

- add `WorkspaceConfig`
- add `[workspace].profile` to `ZtlSettings`
- map legacy `vault.client` to canonical `workspace.profile`
- derive compatibility `vault.client` from the resolved profile at runtime

### 3. Add plugin contracts and hooks

- add `WorkspaceProfileContribution`
- add `register_workspace_profiles()`
- add `post_init_profile(...)`
- add `PluginManager.workspace_profile_contributions()`

### 4. Migrate init

- make `--profile` canonical on `ztlctl init`
- keep deprecated `--client`
- write `[workspace].profile`
- dispatch both `post_init` and `post_init_profile`
- route profile-owned scaffolding through built-in profile contributions

### 5. Migrate workflow scaffolding

- make `profile` the canonical stored choice
- keep deprecated `--viewer` for `workflow init/update`
- rename generated guidance from `viewer.md` to `profile.md`
- rename Copier layer keys from `viewer` to `profile`
- rewrite legacy workflow answers on update

### 6. Codify ownership

- add `workspace_ownership.py`
- classify core-managed, profile-managed, and human-managed paths
- keep indexing behavior unchanged: `notes/` and `ops/` only

### 7. Reconcile docs and output

- update init rendering to prefer `profile`
- update self-doc templates to speak in terms of `profile`
- update `DESIGN.md`, `docs/configuration.md`, `docs/tutorial.md`, and `docs/development.md`

### 8. Add regression coverage

- config mapping from legacy `vault.client`
- canonical `[workspace].profile` writes
- deprecated `--client` and workflow `--viewer` compatibility
- new `post_init_profile` dispatch
- plugin profile contribution collection, reserved-name handling, and duplicate handling
- legacy workflow answer rewrite from `viewer:` to `profile:`

## Validation

- run targeted pytest slices for config, init, workflow, plugins, and command help/examples
- run `uv run python -m compileall src/ztlctl`
- run `uv run ruff check src tests`
- run `uv run mypy src`

## Out of Scope

- no third-party profile activation
- no profile validation/update/upgrade flows
- no garden scaffolding
- no old-workspace migration tooling
