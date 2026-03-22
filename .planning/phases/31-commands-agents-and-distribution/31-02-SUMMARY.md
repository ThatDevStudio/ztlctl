---
phase: 31-commands-agents-and-distribution
plan: "02"
subsystem: distribution
tags: [marketplace, plugin, ci, release-pipeline, documentation]

requires:
  - phase: 28-plugin-foundation
    provides: plugin.json manifest, plugin/ directory structure, CI plugin_validate job
  - phase: 31-01
    provides: slash commands and agents completing the plugin component set

provides:
  - marketplace.json at repo root enabling claude plugin install ztlctl from GitHub
  - Release pipeline version sync step keeping plugin.json version in lockstep with pyproject.toml
  - Comprehensive plugin README covering prerequisites, install, verify, update, troubleshoot

affects:
  - future plugin updates (version sync is now automatic)
  - user onboarding (README is primary install surface)

tech-stack:
  added: []
  patterns:
    - "Git-subdir marketplace: marketplace.json directory field points to plugin/ subdirectory"
    - "Atomic version sync: plugin.json amended into cz bump commit before push — one commit, one tag"

key-files:
  created:
    - marketplace.json
    - .planning/phases/31-commands-agents-and-distribution/31-02-SUMMARY.md
  modified:
    - .github/workflows/release-pipeline.yml
    - plugin/README.md

key-decisions:
  - "marketplace.json uses git-subdir format with directory field — not the older plugins array schema"
  - "Version sync uses git commit --amend --no-edit to fold plugin.json into the cz bump commit atomically"
  - "README is the primary onboarding surface and DINF-03 documentation deliverable for this phase"

patterns-established:
  - "Plugin version always matches pyproject.toml version — enforced automatically by release pipeline"
  - "Troubleshooting section documents claude mcp list verification as first post-install step"

requirements-completed: [DIST-01, DIST-02, DIST-03]

duration: 2min
completed: 2026-03-22
---

# Phase 31 Plan 02: Commands, Agents, and Distribution — Distribution Summary

**marketplace.json (git-subdir format) + atomic plugin.json version sync in CI + comprehensive install/troubleshoot README**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-22T04:54:35Z
- **Completed:** 2026-03-22T04:56:49Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `marketplace.json` at repo root using git-subdir format (`"directory": "plugin"`) — enables `claude plugin install ztlctl` from GitHub
- Added "Sync plugin version" step to release pipeline that amends the cz bump commit with plugin.json version update — single commit, single tag, zero drift
- Rewrote `plugin/README.md` with complete installation lifecycle: Python 3.13 + uv/pipx prerequisites, install command, post-install `claude mcp list` verification, 5 commands + 2 agents summary, update instructions, and Windows troubleshooting

## Task Commits

Each task was committed atomically:

1. **Task 1: Create marketplace.json and update plugin.json manifest** - `763b278` (chore)
2. **Task 2: Add version sync step to release pipeline and rewrite plugin README** - `cc0c9db` (chore)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `marketplace.json` - Git-subdir marketplace manifest pointing to plugin/ directory
- `.github/workflows/release-pipeline.yml` - Sync plugin version step added after cz bump
- `plugin/README.md` - Full rewrite with prerequisites, install, verify, update, troubleshoot
- `plugin/.claude-plugin/plugin.json` - Already had correct paths; no content change needed

## Decisions Made

- **marketplace.json schema**: Used git-subdir format (`"directory": "plugin"`) rather than the existing `"plugins"` array schema. The existing file had an outdated schema with `$schema`, `owner`, and `plugins` array fields. The plan specifies the simpler git-subdir format that Claude Code uses for `claude plugin install`.
- **Version sync atomicity**: `git commit --amend --no-edit` folds plugin.json into the cz bump commit before push. This is safe because the bump commit has not been pushed at that point in the pipeline. Result: one release commit includes both pyproject.toml and plugin.json version bumps.
- **README scope**: The README is both user documentation and the DINF-03 documentation deliverable for this phase — it covers the full installation lifecycle in one place.

## Deviations from Plan

None — plan executed exactly as written. The marketplace.json file existed but used an older schema; replacing it with the git-subdir format is what the plan specified.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Distribution layer complete: marketplace.json + version sync + README covers the full plugin distribution lifecycle
- Plugin is ready for `claude plugin install ztlctl` once pushed to GitHub
- Version sync will automatically keep plugin.json current on every release going forward

---
*Phase: 31-commands-agents-and-distribution*
*Completed: 2026-03-22*
