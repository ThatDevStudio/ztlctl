# Phase 13: Switch GitHub Pages Deploy to Actions Artifact - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace `mkdocs gh-deploy --force` (which pushes to a `gh-pages` branch) with `actions/upload-pages-artifact` + `actions/deploy-pages` (direct artifact deployment). Delete the `gh-pages` branch after migration. This aligns the docs deploy with the project's trunk-based workflow by eliminating an intermediate branch.

</domain>

<decisions>
## Implementation Decisions

### Deploy workflow changes
- Replace `mkdocs gh-deploy --force` with:
  1. `mkdocs build` (produces `site/` directory)
  2. `actions/upload-pages-artifact` (uploads `site/` as GitHub Pages artifact)
  3. `actions/deploy-pages` (deploys the artifact to Pages)
- Remove `git config` identity step (no longer pushing to a branch)
- Change `permissions: contents: write` to `permissions: pages: write, id-token: write` (required for Pages deployment)
- Add `environment: github-pages` with `url: ${{ steps.deployment.outputs.page_url }}`
- Keep trigger: push to `develop` + `workflow_dispatch`

### GitHub Pages source setting
- Checkpoint task: user must change GitHub Pages source from `gh-pages` branch to "GitHub Actions" in repo settings
- This is a one-time manual step at https://github.com/ThatDevStudio/ztlctl/settings/pages

### gh-pages branch cleanup
- After artifact deploy is verified working, delete `gh-pages` branch:
  - `git push origin --delete gh-pages`
- This is the whole point of the phase — eliminate the non-trunk branch

### Claude's Discretion
- Whether to split into two jobs (build + deploy) or keep as one
- Exact `actions/upload-pages-artifact` and `actions/deploy-pages` version pins
- Whether to add a `concurrency` group for Pages deployments

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Current workflow to replace
- `.github/workflows/docs.yml` — Current workflow using `mkdocs gh-deploy --force` (35 lines)

### GitHub Actions Pages deployment
- GitHub docs: https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site#publishing-with-a-custom-github-actions-workflow

### Prior phase context
- `.planning/phases/08-mkdocs-infrastructure/08-CONTEXT.md` — Original deploy workflow decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.github/workflows/docs.yml` — base workflow to modify (keep trigger, Python setup, mkdocs install steps)
- `.github/workflows/release-pipeline.yml` — reference for GitHub Actions patterns in this repo

### Established Patterns
- Trigger on push to `develop` + `workflow_dispatch`
- Pinned dependency versions in pip install
- `actions/checkout@v4`, `actions/setup-python@v5` already in use

### Integration Points
- GitHub repository Pages settings (manual: Source → GitHub Actions)
- `gh-pages` remote branch (to delete after migration)

</code_context>

<specifics>
## Specific Ideas

- User explicitly said: "this feels like it breaks the trunk-based workflow" about the gh-pages branch
- This is a clean-up phase motivated by architectural consistency, not new functionality
- The workflow change is small (~10 lines modified) but the manual settings step is critical

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 13-switch-github-pages-deploy-to-actions-artifact-eliminate-gh-pages-branch*
*Context gathered: 2026-03-20*
