# Hybrid Workspace Phase 3 Implementation Plan

**Date:** 2026-03-02
**Status:** Implemented

## Deliverables

- plugin-contributed ordered vault init steps
- structured init instructions surfaced in CLI and JSON output
- first-party Obsidian starter kit scaffold
- human-owned `garden/` scaffold and templates
- Obsidian product documentation and regression coverage

## Work Completed

### 1. Vault init step surface

- added `VaultInitContext`, `VaultInitInstruction`, `VaultInitStepResult`, and `VaultInitStepContribution`
- added `register_vault_init_steps()` to the public plugin hooks
- added `PluginManager.vault_init_step_contributions()`

### 2. Init pipeline refactor

- moved `InitService.init_vault()` to an ordered step model
- wrapped legacy `WorkspaceProfileContribution.init_scaffold` into compatibility init steps
- added `setup_steps` and `step_ids_executed` to init success payloads
- rendered setup instructions under `Next steps` in CLI output

### 3. Obsidian starter kit

- expanded the first-party Obsidian profile plugin to scaffold `.obsidian/` config, snippets, and plugin config files
- scaffolded `garden/README.md`, garden directories, and garden templates
- added detailed plugin install, enable, and verify guidance during init

### 4. Drift guards

- added coverage for init-step registration, ordering, filtering, and failure handling
- added scaffold-content tests for the starter-kit files and wording
- updated docs to describe the starter kit as config plus guidance, not automatic plugin installation

## Follow-On Work

- The current default direction is to treat the Obsidian starter kit as a one-shot scaffold rather than a ztlctl-managed lifecycle surface.
- Any future validation or upgrade behavior for `.obsidian/` would require a new product decision instead of being assumed backlog follow-through.
- review/export surfaces can still become more profile-aware later, but they no longer depend on profile-managed update controls.
