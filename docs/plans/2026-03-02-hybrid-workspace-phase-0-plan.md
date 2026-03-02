# Hybrid Workspace Phase 0 Implementation Plan

**Date:** 2026-03-02
**Status:** Approved

## Goal

Implement Phase 0 truth reconciliation and `none` normalization without introducing the Phase 1 profile architecture.

## Tasks

### 1. Add canonical mode normalization

- add a shared module for canonical client/viewer values
- normalize `vanilla -> none`
- raise structured errors for unsupported values
- emit deprecation warnings through `ServiceResult.warnings`

### 2. Wire normalization into runtime paths

- `InitService.init_vault`
- `WorkflowService.read_answers`
- `WorkflowService.init_workflow`
- `WorkflowService.update_workflow`
- `ExportService.export_dashboard`
- `VaultConfig` validation for legacy TOML values

### 3. Update command surfaces

- show `obsidian|none` in prompts, examples, and help text
- continue accepting `--client vanilla` and `--viewer vanilla`
- keep `obsidian` as the default

### 4. Update workflow scaffolding

- switch Copier viewer choices from `obsidian|vanilla` to `obsidian|none`
- rename the portable viewer layer from `vanilla` to `none`
- ensure rewritten workflow answers persist `viewer: none`

### 5. Fix generated self-doc drift

- replace stale `ZTL-NNNN` and `ref_NNNN` examples
- replace `sapling` with `budding`
- separate machine status from garden maturity
- update task and decision lifecycle references
- rename the generated Obsidian CSS class from `.ztlctl-sapling` to `.ztlctl-budding`

### 6. Reconcile docs/spec

- update `DESIGN.md`
- update `docs/configuration.md`
- update `docs/tutorial.md`
- update `docs/development.md`
- remove canonical `[plugins].obsidian` examples
- document that `.obsidian/snippets/ztlctl.css` is the current extent of built-in init scaffolding

### 7. Add regression coverage

- canonical `none` path for init/workflow/export
- alias compatibility for `vanilla`
- workflow-answer normalization from legacy `viewer: vanilla`
- TOML normalization from legacy `client = "vanilla"`
- ignored legacy `[plugins].obsidian`
- self-doc truth assertions

## Validation

- compile the package
- run targeted config/init/workflow/export tests
- run command tests covering the renamed surfaces

## Out of Scope

- no workspace-profile contract
- no plugin discovery changes
- no migration tooling
- no changes to indexing boundaries
