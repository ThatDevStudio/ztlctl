# Hybrid Workspace Phase 0 Design

**Date:** 2026-03-02
**Status:** Approved

## Goal

Establish a single current-truth surface for workspace/client/viewer behavior before Phase 1 introduces workspace profiles.

Phase 0 is intentionally conservative:

- keep `client` and `viewer` as the current abstractions
- normalize the no-special-integration mode from `vanilla` to `none`
- preserve backward compatibility for one release
- remove stale config and documentation claims that imply a built-in Obsidian plugin exists today
- fix generated self-docs so they describe the actual domain model

## Non-Goals

- no `profile` abstraction
- no workspace-profile plugin contract
- no Obsidian starter-kit plugin
- no garden scaffolding or indexing changes
- no change to the default `obsidian` client/viewer

## Current Truth

- `vault.client` is still the vault-facing workspace selector.
- workflow and dashboard export still use `viewer`.
- `obsidian` still triggers direct `.obsidian/snippets/ztlctl.css` scaffolding in init.
- core content discovery still only walks `notes/` and `ops/`.
- `[plugins].obsidian` is documented but not backed by a real built-in plugin implementation.
- generated `self/` docs still contain stale ID, lifecycle, and maturity language.

## Design Decisions

### 1. Canonical naming

- Canonical `client` values: `obsidian | none`
- Canonical `viewer` values: `obsidian | none`
- Deprecated alias: `vanilla`

`vanilla` remains accepted at input boundaries for one release, but all persisted outputs produced by Phase 0 write `none`.

### 2. Compatibility behavior

- CLI flags accept `vanilla` but normalize it to `none`
- `vault.client = "vanilla"` in existing TOML normalizes to `none` during settings load
- workflow answers containing `viewer: vanilla` normalize to `none` when read and are rewritten as `none` on update/init
- deprecation warnings are emitted through `ServiceResult.warnings`

### 3. Config boundary

- keep `[vault].client`
- remove canonical `[plugins].obsidian` from the config model and docs
- rely on current Pydantic behavior that ignores unknown nested plugin keys so older configs still load

### 4. Self-doc truth source

Generated `self/identity.md` and `self/methodology.md` must follow:

- note IDs: `ztl_<8hex>`
- reference IDs: `ref_<8hex>`
- task IDs: `TASK-NNNN`
- log IDs: `LOG-NNNN`
- note machine status: `draft -> linked -> connected`
- reference status: `captured -> annotated`
- task status: `inbox -> active -> blocked/done/dropped`
- decision status: `proposed -> accepted -> superseded`
- garden maturity: `seed -> budding -> evergreen`

### 5. Obsidian scope in Phase 0

Phase 0 does not remove the existing direct `.obsidian` init behavior. It documents it honestly as current behavior and removes broader product claims that suggest a full built-in Obsidian integration exists already.

## Acceptance Criteria

- no canonical public surface uses `vanilla`
- `none` is the only no-special-integration value newly persisted by Phase 0 code
- `vanilla` remains backward compatible via normalization plus warnings
- self-doc templates match actual IDs and lifecycle semantics
- canonical config/docs no longer include `[plugins].obsidian`
- docs describe current Obsidian behavior accurately without overstating plugin support
