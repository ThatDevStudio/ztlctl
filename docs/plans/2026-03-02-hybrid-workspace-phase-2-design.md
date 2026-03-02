# Hybrid Workspace Phase 2 Design

**Date:** 2026-03-02
**Status:** Approved

## Goal

Make workspace profiles plugin-discovered instead of built-in-only, while preserving the Phase 1 `profile` model and compatibility shims.

## Scope

- route `ztlctl init` and `ztlctl workflow init/update` through discovered profiles
- keep `core` as the always-available fallback profile
- extract `obsidian` into a first-party plugin module
- make missing profiles fail clearly
- surface installed profiles through prompts, help, and validation errors

## Non-Goals

- no new `profile list` command
- no profile validation/update/upgrade flow yet
- no garden scaffolding yet
- no dashboard/profile-aware export redesign

## Design Decisions

### 1. Discovery scope

- `init` uses entry-point plugins only
- vault-scoped workflow/profile operations use entry-point plugins plus `vault_root/.ztlctl/plugins`
- `core` is injected directly and remains available even with zero plugins installed

### 2. Canonical defaults

- default profile becomes `core`
- legacy compatibility client becomes `none` for every non-`obsidian` profile
- `obsidian` stays available through the shipped first-party plugin, not through core-owned branches

### 3. Registry model

- runtime resolution uses a `WorkspaceProfileRegistry`
- registry carries canonical profiles, alias mappings, and non-fatal discovery/conflict warnings
- deprecated aliases `none` and `vanilla` continue to resolve to `core`

### 4. Failure model

- unknown or currently uninstalled selected profiles return `PROFILE_NOT_FOUND`
- invalid client/profile syntax remains `INVALID_PROFILE`
- profile scaffold failures return `PROFILE_SCAFFOLD_FAILED`
- no silent fallback to `core` when an explicit profile is missing

### 5. Workflow model

- workflow answers remain canonical on `profile:`
- legacy `viewer:` answers still load and normalize on update
- unknown plugin profile ids are preserved on read, then validated at workflow execution time
- the core workflow template renders built-in profile notes for `core` and `obsidian`, and a generic note for plugin profiles

## Acceptance Criteria

- `core` is the default profile for fresh config, init, and workflow scaffolding
- the Obsidian scaffold is contributed by `ztlctl.plugins.builtins.obsidian`, not by core profile code
- init ignores target-vault local plugins
- workflow profile discovery includes local vault plugins
- installed profiles appear in `--help`, prompts, and error payloads
