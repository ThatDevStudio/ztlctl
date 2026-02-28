# Trunk-Based Development Migration

**Date:** 2026-02-28
**Status:** Approved

## Goal

Migrate from two-branch model (main + develop) to trunk-based development with `develop` as the single trunk branch. All release automation moves from `main` to `develop`. The `main` branch and stale feature branches are deleted.

## Current State

- `develop`: version 1.0.0, all feature work (76 commits ahead of main)
- `main`: version 1.1.1, 6 release/version-bump commits not on develop
- Stale branches: `docs/documentation-upgrade`, `fix/sync-version-from-release`, `hotfix/fix-wheel-duplicates`, `release/v1.1.0`
- Release pipeline: merge to main triggers `cz bump` → changelog → tag → GitHub Release → PyPI publish (manual approval gate)

## Design

### 1. Git State Reconciliation

Merge `main` into `develop` to bring develop to version 1.1.1 with full release history. Resolve conflicts favoring main's version numbers (the published state). Delete `main` and 4 stale branches (local + remote).

### 2. Release Workflow (auto-release on develop)

`release.yml` trigger changes from `branches: [main]` to `branches: [develop]`.

The existing `cz bump` logic handles non-version-bumping commits (exit code 21 = skip), so `docs:`, `ci:`, `chore:` merges won't trigger a release — only `feat:`, `fix:`, and breaking changes will.

Push target changes from `main` to `develop`. Release target changes from `--target main` to `--target develop`.

### 3. CI Workflow

Remove `main` from branch triggers in `ci.yml`. CI runs on pushes/PRs to `develop` only.

### 4. Publish Workflow

No changes. Triggers on GitHub Release publication (branch-agnostic). Manual approval gate on `pypi` environment is preserved.

### 5. Source Code

`GitConfig.branch` default in `src/ztlctl/config/models.py` changes from `"main"` to `"develop"`.

### 6. Documentation Updates

| File | Changes |
|------|---------|
| `CLAUDE.md` | Remove main from branching table, remove hotfix workflow, simplify release description, remove post-release sync section, update CI table |
| `CONTRIBUTING.md` | Simplify branching model (remove main/hotfix rows), update commit rules |
| `README.md` | Update release description |
| Memory files | Update workflow.md and MEMORY.md |

### 7. GitHub Settings (Manual, Post-Merge)

- Change GitHub default branch to `develop` (if not already)
- Delete `main` branch on GitHub
- Update branch protection rules to apply to `develop` only

## New Branching Model

| Branch | Purpose | Merges to |
|--------|---------|-----------|
| `develop` | Trunk — all development and releases | — |
| `feature/<name>` | New features | `develop` |
| `fix/<name>` | Bug fixes | `develop` |

## New Release Flow

```
Feature PR merged to develop
  → release.yml runs
  → cz bump --changelog --yes
  → If version-bumping commits exist:
    → Version bump + changelog committed
    → Tag pushed
    → GitHub Release created
    → publish.yml triggers (manual approval)
    → Published to PyPI
  → If no version-bumping commits:
    → Skip (exit code 21)
```
