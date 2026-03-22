---
phase: 28-plugin-foundation
plan: "02"
subsystem: ci
tags: [github-actions, plugin-validate, ci, yaml]

requires:
  - "28-01: plugin artifacts (plugin.json, hooks.json, .mcp.json, vault-gate.sh, tests/plugin/)"
provides:
  - "plugin_validate CI job in pr-ci.yml that blocks merges on plugin manifest errors, missing files, and permission issues"
  - "Parallel CI enforcement of all 8 plugin validation gates on every PR"
affects: [skills, agents, commands, hooks]

tech-stack:
  added: []
  patterns:
    - "plugin_validate: parallel GitHub Actions job with no needs: dependency — runs alongside validate_pr and doc_lint"
    - "Python inline scripts in run: steps for JSON validation and directory structure checks"
    - "if: ${{ always() }} summary step with markdown table matching existing CI job pattern"

key-files:
  created: []
  modified:
    - .github/workflows/pr-ci.yml

key-decisions:
  - "plugin_validate runs in parallel (no needs: field) — consistent with the existing validate_pr and doc_lint parallelism; plugin validation is independent of Python linting and docs"
  - "Directory structure step checks for component misplacement inside .claude-plugin/ — enforces the plugin root layout invariant established in Plan 01"

requirements-completed: [PLGN-04]

duration: 8min
completed: 2026-03-22
---

# Phase 28 Plan 02: Plugin CI Validation Job Summary

**plugin_validate CI job added to pr-ci.yml — 8 validation gates run in parallel on every PR, blocking merges on manifest errors, missing files, broken hooks, and permission issues**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-22T00:18:00Z
- **Completed:** 2026-03-22T00:26:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Added `plugin_validate` job to `.github/workflows/pr-ci.yml` as a parallel job (no `needs:` field) satisfying PLGN-04
- Job validates 8 gates: plugin.json valid JSON, plugin.json required fields (8 fields), hooks.json valid JSON, .mcp.json valid JSON, hook script execute permissions, plugin directory structure (components at plugin root, not in .claude-plugin/), path traversal safety (no `../` in plugin files), and the full `tests/plugin/` pytest suite
- Summary step uses `if: ${{ always() }}` with a markdown table matching the pattern from `validate_pr` and `doc_lint` jobs
- Job runs Python 3 inline scripts for JSON and filesystem checks — no additional dependencies beyond the repo checkout

## Task Commits

Each task was committed atomically:

1. **Task 1: Add plugin_validate CI job to pr-ci.yml** - `e16a6d1` (ci)

## Files Created/Modified

- `.github/workflows/pr-ci.yml` — Added `plugin_validate` job with 8 validation steps + summary (124 lines inserted)

## Decisions Made

- `plugin_validate` has no `needs:` field — it runs fully in parallel with `validate_pr` and `doc_lint`. Plugin validation is independent of Python linting, type checking, and doc linting, so there is no reason to serialize.
- The directory structure validation step explicitly checks that `skills/`, `agents/`, `hooks/`, and `commands/` exist at `plugin/` root AND do NOT exist inside `plugin/.claude-plugin/` — this enforces the layout invariant established in Plan 01 and tested in `test_plugin_directory_structure`.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## Self-Check: PASSED

- `.github/workflows/pr-ci.yml` — FOUND (modified, 1 file changed, 124 insertions)
- Commit `e16a6d1` — FOUND (`git log --oneline -1` confirms)
- `plugin_validate` job verified present in YAML: all 8 step IDs confirmed, no `needs:` field, `runs-on: ubuntu-latest`, summary step has `if: ${{ always() }}`

---
*Phase: 28-plugin-foundation*
*Completed: 2026-03-22*
