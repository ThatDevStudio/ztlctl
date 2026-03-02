# Hybrid Workspace Phase 1 Design

**Date:** 2026-03-02
**Status:** Approved

## Goal

Replace workspace-selection semantics built around `client` and workflow `viewer` with a canonical `profile` model, while keeping one-release compatibility shims.

## Scope

- add canonical `[workspace].profile`
- move `ztlctl init` and `ztlctl workflow init/update` to `--profile`
- keep `export dashboard --viewer` as a render-target concern
- add workspace-profile plugin contracts and hook skeletons
- codify `core-managed`, `profile-managed`, and `human-managed` paths

## Non-Goals

- no plugin-discovered profile routing yet
- no first-party Obsidian starter kit beyond the current built-in scaffold
- no garden scaffolding
- no migration/import tooling

## Design Decisions

### 1. Canonical workspace identity

- Canonical built-in profiles: `obsidian | core`
- `core` is the durable replacement for the old no-special-integration state
- Deprecated aliases:
  - `profile=none -> core`
  - `profile=vanilla -> core`
  - `client=none -> core`
  - `client=vanilla -> core`

### 2. Config boundary

- `[workspace].profile` is the canonical runtime source
- `[vault].client` remains as deprecated compatibility input only
- if both are present, `workspace.profile` wins
- new vaults write `[workspace].profile`; they do not write `vault.client`

### 3. Workflow boundary

- workflow scaffolding stores `profile`, not `viewer`
- legacy answers containing `viewer:` remain readable
- `workflow update` rewrites legacy answers to canonical `profile:`
- `export dashboard --viewer` stays unchanged because it controls render style, not workspace identity

### 4. Ownership boundary

Core-managed:

- `ztlctl.toml`
- `.ztlctl/`
- `self/`
- `notes/`
- `ops/`

Profile-managed:

- profile-declared managed paths
- in Phase 1: `.obsidian/` for the built-in `obsidian` profile

Human-managed:

- `garden/`
- other non-core workspace paths not declared by a profile

### 5. Plugin compatibility

- keep legacy `post_init(vault_name, client, tone)`
- add `post_init_profile(vault_name, profile, tone, managed_paths)`
- add `register_workspace_profiles()`
- built-in profiles use the same contribution type as future plugin profiles
- init/workflow routing still uses built-in profiles only in Phase 1

## Acceptance Criteria

- runtime config and workflow generation use `profile` canonically
- legacy `client` and workflow `viewer` inputs still work with warnings
- built-in profile scaffolding is routed through a profile abstraction
- docs and generated self-docs describe `profile` as the canonical model
- ownership boundaries are explicit in code and tests
