---
phase: 01-core-hardening
plan: "02"
subsystem: services
tags: [check, git, mcp, copier, security, tech-debt]

requires:
  - phase: 01-core-hardening-01
    provides: NoteTypeRegistry and TDD foundation for plan 02

provides:
  - backup_retention_days enforced in CheckService._prune_backups (age-based pruning)
  - VEC_CREATE_SQL dead code removed from schema.py
  - import json moved to module level in check.py
  - graph materialize_metrics called after check --rebuild
  - _sanitize_for_commit helper stripping newlines/null bytes in git.py
  - HTTP transport warning in serve.py for sse/streamable-http transports
  - Copier unsafe=False documented in workflow.py

affects: [check, git-plugin, mcp-serve, workflow]

tech-stack:
  added: []
  patterns:
    - "Sanitize user-supplied strings before passing to subprocess (git commit -m)"
    - "Emit warnings to stderr for insecure transport options before server start"
    - "Document security defaults inline where behavior is non-obvious (Copier trust)"

key-files:
  created: []
  modified:
    - src/ztlctl/services/check.py
    - src/ztlctl/infrastructure/database/schema.py
    - src/ztlctl/plugins/builtins/git.py
    - src/ztlctl/commands/serve.py
    - src/ztlctl/services/workflow.py
    - tests/plugins/test_git_plugin.py

key-decisions:
  - "Use datetime.fromtimestamp(backup.stat().st_mtime) for age-based backup pruning — consistent with existing backup filename pattern"
  - "Warn on both sse and streamable-http transports (not just streamable-http) — both are unauthenticated HTTP"
  - "Copier uses unsafe= (not trust=) parameter; current default unsafe=False is already safe — document rather than change"
  - "Sanitize content_id, title, and summary in git commit messages; content_type and fields_changed are internal values (no sanitization needed)"

patterns-established:
  - "Age-based pruning: after count-based pruning, re-glob backups list then prune by mtime"
  - "Security comments: SECURITY: prefix + reference to issue ID (HARD-07)"

requirements-completed: [HARD-01, HARD-07]

duration: 10min
completed: 2026-03-19
---

# Phase 01 Plan 02: Tech Debt and Security Hardening Summary

**5 tech-debt fixes (backup retention, dead code, import location, post-rebuild graph) and 3 security fixes (git injection, HTTP auth warning, Copier trust audit) across 5 source files**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-19T20:10:00Z
- **Completed:** 2026-03-19T20:22:44Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Enforced `backup_retention_days` config setting — backups older than configured days are now pruned (previously only count-based pruning existed)
- Removed `VEC_CREATE_SQL` dead code from schema.py — `VectorService.ensure_table()` creates the vec table at runtime using configured embedding dimension
- Moved `import json` to module level in check.py (was inside per-file loop body)
- Added `_sanitize_for_commit()` to strip newlines and null bytes from user-supplied git commit message fields (content_id, title, summary)
- Added stderr WARNING when HTTP transports (`sse`, `streamable-http`) are used in `ztlctl serve`
- Documented Copier's `unsafe=False` default (no template tasks without explicit opt-in) per HARD-07

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix tech debt — backup retention, dead code, import, post-rebuild materialize** - `b7ee0de` (fix)
2. **Task 2: Fix security issues — git sanitization, HTTP warning, Copier trust** - `6de39da` (fix, committed as part of prior perf commit by pre-commit hook behavior)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `src/ztlctl/services/check.py` - import json at module level, datetime/timedelta at module level, age-based backup pruning in _prune_backups, removed local datetime import from _check_garden_health
- `src/ztlctl/infrastructure/database/schema.py` - VEC_CREATE_SQL constant removed
- `src/ztlctl/plugins/builtins/git.py` - _sanitize_for_commit() helper, applied to post_create/post_update/post_close commit messages
- `src/ztlctl/commands/serve.py` - WARNING echo for sse/streamable-http transports
- `src/ztlctl/services/workflow.py` - SECURITY comments on all three Copier call sites
- `tests/plugins/test_git_plugin.py` - test_sanitize_for_commit_strips_newlines() test

## Decisions Made
- Warned on `sse` as well as `streamable-http` (plan only mentioned "http"/"streamable-http") — both are HTTP-based and unauthenticated, consistent treatment
- Copier parameter is `unsafe` (not `trust`) — audited actual API signature, added comment documenting safe default
- Age-based pruning re-globs after count-based pruning to get fresh list before mtime filtering

## Deviations from Plan

### Auto-fixed Issues

None - plan executed exactly as written (minor: added `sse` to HTTP transport warning check in serve.py — broader than plan's "http"/"streamable-http", but correct behavior).

## Issues Encountered
- Pre-commit hook stash/unstash cycle caused Task 2 changes to be absorbed into a prior commit (`6de39da`) with a different commit message. The changes are correctly on disk and committed; the commit message doesn't match the task name.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All HARD-01 (CONCERNS.md tech debt) and HARD-07 (security) items resolved
- Ready for Plan 03 (test coverage lift or next hardening task)

---
*Phase: 01-core-hardening*
*Completed: 2026-03-19*
