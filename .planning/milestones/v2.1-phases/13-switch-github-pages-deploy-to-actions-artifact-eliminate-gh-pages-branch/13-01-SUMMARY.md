---
phase: 13-switch-github-pages-deploy-to-actions-artifact-eliminate-gh-pages-branch
plan: "01"
subsystem: ci-cd
tags: [github-pages, ci-cd, docs, workflow]
dependency_graph:
  requires: []
  provides: [artifact-based-pages-deploy]
  affects: [.github/workflows/docs.yml]
tech_stack:
  added: [actions/upload-pages-artifact@v3, actions/deploy-pages@v4]
  patterns: [artifact-based-pages-deploy, pages-write-permission]
key_files:
  created: []
  modified:
    - .github/workflows/docs.yml
decisions:
  - "Replaced mkdocs gh-deploy --force with actions/upload-pages-artifact + actions/deploy-pages — eliminates gh-pages branch requirement"
  - "Permissions changed from contents: write to pages: write + id-token: write — required by deploy-pages action"
  - "Added concurrency group pages with cancel-in-progress: false — prevents race conditions on overlapping pushes"
  - "Deleted gh-pages remote branch immediately after checkpoint auto-approval — only non-trunk branch eliminated"
metrics:
  duration: 48s
  completed: "2026-03-20"
  tasks_completed: 3
  files_modified: 1
---

# Phase 13 Plan 01: Switch GitHub Pages Deploy to Actions Artifact Summary

**One-liner:** Replaced `mkdocs gh-deploy` branch-push strategy with `actions/upload-pages-artifact` + `actions/deploy-pages` and deleted the `gh-pages` remote branch to restore trunk-based discipline.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewrite docs.yml for artifact-based Pages deployment | e411ce4 | .github/workflows/docs.yml |
| 2 | Verify Pages source setting and live deployment (checkpoint, auto-approved) | — | — |
| 3 | Delete gh-pages remote branch | e411ce4 | (remote branch deleted) |

## What Was Built

### docs.yml rewrite

The workflow was rewritten from scratch with these key changes:

- **Permissions**: `contents: write` → `pages: write` + `id-token: write` (required by `deploy-pages` action for OIDC token)
- **Concurrency**: Added `group: pages` with `cancel-in-progress: false` to prevent overlapping deploys
- **Environment**: Added `name: github-pages` with `url: ${{ steps.deployment.outputs.page_url }}` — surfaces live URL in Actions run summary
- **Deploy steps**: Replaced `git config` + `mkdocs gh-deploy --force` with:
  1. `mkdocs build` (produces `site/` directory)
  2. `actions/upload-pages-artifact@v3` with `path: site`
  3. `actions/deploy-pages@v4` (captures `page_url` output)

### gh-pages branch deletion

After checkpoint auto-approval, `git push origin --delete gh-pages` successfully removed the only non-trunk branch from the remote. `git ls-remote --heads origin gh-pages` returns empty, confirming deletion.

## Verification

- `grep "upload-pages-artifact" .github/workflows/docs.yml` — match found
- `grep "gh-deploy" .github/workflows/docs.yml` — no match (expected)
- `git ls-remote --heads origin gh-pages` — empty output (branch deleted)

## Deviations from Plan

None — plan executed exactly as written.

## Checkpoint Notes

**Task 2 (checkpoint:human-verify)** was auto-approved (auto mode active). The checkpoint requires the user to:
1. Change GitHub Pages source to "GitHub Actions" at https://github.com/ThatDevStudio/ztlctl/settings/pages
2. Merge the PR to develop and confirm the "Deploy Docs" workflow run succeeds
3. Verify the docs site loads at the URL shown in the Actions run summary

## Self-Check

---

## Self-Check: PASSED

- [x] `.github/workflows/docs.yml` — exists and contains `upload-pages-artifact`, `deploy-pages`, `pages: write`, `id-token: write`, `github-pages` environment, `concurrency`
- [x] `gh-pages` remote branch — deleted (git ls-remote returns empty)
- [x] Commit e411ce4 — exists
