---
phase: 08-mkdocs-infrastructure
plan: "03"
subsystem: infra
tags: [github-actions, mkdocs, github-pages, gh-deploy, ci-cd]

# Dependency graph
requires:
  - phase: 08-02
    provides: mkdocs.yml config with shadcn theme and full nav
provides:
  - GitHub Actions workflow that deploys MkDocs to gh-pages branch on push to develop
affects:
  - gh-pages branch deployment
  - live docs site at https://thatdevstudio.github.io/ztlctl/

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "pip install (not uv) for CI docs-only dependencies — avoids full ztlctl env setup"
    - "workflow-level permissions: contents: write for gh-pages push access"
    - "fetch-depth: 0 required for mkdocs gh-deploy to find gh-pages branch"

key-files:
  created:
    - .github/workflows/docs.yml
  modified: []

key-decisions:
  - "workflow-level permissions: contents: write (not job-level) — grants GITHUB_TOKEN write access to push gh-pages branch"
  - "pip install instead of uv in CI — docs workflow only needs mkdocs tools, not full ztlctl project environment"
  - "Pinned exact versions: mkdocs==1.6.1, mkdocs-shadcn==0.10.2, mkdocs-redirects==1.2.2 — matches pyproject.toml dev deps"

patterns-established:
  - "Docs workflow follows same trigger pattern as release-pipeline.yml: push to develop + workflow_dispatch"

requirements-completed: [INFR-04]

# Metrics
duration: 1min
completed: 2026-03-20
---

# Phase 08 Plan 03: GitHub Actions MkDocs Deploy Workflow Summary

**GitHub Actions docs.yml workflow created with contents: write permission, pinned mkdocs deps, and mkdocs gh-deploy --force targeting gh-pages branch**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-20T16:15:42Z
- **Completed:** 2026-03-20T16:16:32Z
- **Tasks:** 1 automated + 1 checkpoint (auto-approved)
- **Files modified:** 1

## Accomplishments
- Created `.github/workflows/docs.yml` that deploys MkDocs to gh-pages branch on every push to develop
- Workflow uses `workflow_dispatch` for manual triggering during migration testing
- Configured git identity (`github-actions[bot]`) required by mkdocs gh-deploy
- Pinned all three MkDocs dependencies to exact versions matching pyproject.toml

## Task Commits

Each task was committed atomically:

1. **Task 1: Create .github/workflows/docs.yml** - `dad0645` (ci)
2. **Checkpoint: Verify GitHub Pages source** - auto-approved (AUTO_CFG=true)

**Plan metadata:** (see final commit hash below)

## Files Created/Modified
- `.github/workflows/docs.yml` - GitHub Actions workflow: triggers on push to develop, installs pinned mkdocs deps, runs mkdocs gh-deploy --force to push built site to gh-pages branch

## Decisions Made
- `permissions: contents: write` placed at workflow level (not job level) — this grants `GITHUB_TOKEN` write access needed to push the gh-pages branch
- Used `pip install` not `uv` in CI — the docs workflow only needs mkdocs tools, not the full ztlctl project environment, keeping the workflow fast and simple
- Pinned exact versions (`mkdocs==1.6.1 mkdocs-shadcn==0.10.2 mkdocs-redirects==1.2.2`) matching pyproject.toml dev dependencies for consistency

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- `python3 -c "import yaml; ..."` YAML validation failed because PyYAML is not installed in the system Python. Verified YAML validity via structural string matching instead — all 16 required elements confirmed present. YAML was accepted by the pre-commit `check yaml` hook, confirming it is valid.

## User Setup Required

After the PR merges to develop and the "Deploy Docs" workflow runs successfully:

1. Go to https://github.com/ThatDevStudio/ztlctl/settings/pages
2. Under "Build and deployment" → "Source": change from "Deploy from a branch: develop / docs" to "Deploy from a branch: gh-pages / (root)"
3. Save the setting
4. Wait ~60 seconds, then verify https://thatdevstudio.github.io/ztlctl/ shows the new MkDocs/shadcn theme

## Next Phase Readiness
- All three MkDocs infrastructure plans (08-01, 08-02, 08-03) are complete
- Phase 08 is fully ready for PR creation and merge to develop
- After merge: deploy workflow will fire automatically, gh-pages branch will be created/updated
- Remaining manual step: GitHub Pages source switch (documented above)

---
*Phase: 08-mkdocs-infrastructure*
*Completed: 2026-03-20*
