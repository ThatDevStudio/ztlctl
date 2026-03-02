# Hybrid Workspace Phase 2 Implementation Plan

**Date:** 2026-03-02
**Status:** Implemented

## Deliverables

- plugin-discovered workspace profile registry
- first-party Obsidian profile plugin entry point
- dynamic profile routing for init and workflow scaffolding
- dynamic help/prompt surfaces for installed profiles
- Phase 2 regression coverage for discovery scope, defaults, and missing-profile failures

## Work Completed

### 1. Registry and resolution

- replaced static profile literals with a discovery-backed registry in `src/ztlctl/workspace_profiles.py`
- kept `core` as the always-available fallback profile
- normalized deprecated aliases `none` and `vanilla` to `core`
- kept dashboard `viewer` independent from workspace profile discovery

### 2. Obsidian extraction

- moved the minimal `.obsidian/snippets/ztlctl.css` scaffold into `src/ztlctl/plugins/builtins/obsidian.py`
- registered the first-party Obsidian profile under the `ztlctl.plugins` entry-point group
- removed core-owned Obsidian profile registration

### 3. Config and runtime defaults

- changed `[workspace].profile` default to `core`
- changed legacy compatibility `[vault].client` default to `none`
- kept legacy `vault.client` mapping behavior during settings load

### 4. Init and workflow routing

- `ztlctl init` now resolves installed profiles from entry-point plugins plus `core`
- `ztlctl workflow init/update` now resolve installed profiles from entry-point plugins, local vault plugins, and `core`
- explicit missing profiles now return `PROFILE_NOT_FOUND`
- workflow answers continue to rewrite legacy `viewer:` keys to canonical `profile:`

### 5. UX and drift guards

- `--profile` help text now shows currently installed profiles
- interactive prompts use discovered profile ids instead of hardcoded static lists
- docs and templates now describe dynamic profiles and the `core` default
- tests cover local profile discovery, alias normalization, missing-profile failures, and help output

## Follow-On Work

- Phase 3 should build the first-party Obsidian starter kit on top of the now-real plugin profile system
- Phase 4 should add profile-managed validation and upgrade behavior
