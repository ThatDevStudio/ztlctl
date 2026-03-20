---
phase: 01-core-hardening
plan: 05
subsystem: database
tags: [alembic, sqlite, schema-versioning, readme, cli-docs, check-service]

requires:
  - phase: 01-core-hardening
    plan: 02
    provides: Alembic migration infrastructure (UpgradeService, build_config, stamp_head)

provides:
  - Vault._check_schema_current() — Alembic head comparison with pre-Alembic vault exemption
  - Non-fatal stderr warning on AppContext.vault access when schema is stale
  - CheckService._check_schema_version() — schema_version error category in check output
  - README CLI Command Reference table listing all 18 commands and --log-json flag

affects:
  - check-service
  - app-context
  - vault
  - documentation

tech-stack:
  added: []
  patterns:
    - "Schema stale detection via MigrationContext.get_current_revision() vs ScriptDirectory head"
    - "Pre-Alembic vault detection: None current revision treated as current (not stale)"
    - "Non-fatal warning pattern: check + click.echo(err=True) without blocking operation"
    - "CheckService category extension: add trace_span + private method called before engine.connect()"

key-files:
  created:
    - tests/mcp/test_tools_impl.py (pre-existing untracked file from prior plan, committed here)
  modified:
    - src/ztlctl/infrastructure/vault.py
    - src/ztlctl/commands/_context.py
    - src/ztlctl/services/check.py
    - tests/services/test_upgrade.py
    - README.md

key-decisions:
  - "Pre-Alembic vaults (None revision, tables exist) treated as current to avoid false-positive stale warnings"
  - "Schema stale check runs outside engine.connect() block in CheckService to avoid nested connections"
  - "README CLI Command Reference added as a standalone section before Documentation, not modifying Quick Start"
  - "Copier recopy fallback warning already surfaced via app.emit() warnings loop — no additional CLI code needed"

patterns-established:
  - "_check_schema_current() uses lazy local imports (alembic) following 6-precedent pattern"
  - "Vault stale warning wired at AppContext.vault lazy init — single centralized location"

requirements-completed: [HARD-08, HARD-03, HARD-04]

duration: 8min
completed: 2026-03-19
---

# Phase 01 Plan 05: Schema Versioning and Documentation Audit Summary

**Alembic schema stale detection wired into vault init with non-fatal stderr warning, schema_version check category added to CheckService, and README CLI Command Reference table added covering all 18 commands and --log-json flag.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-19T20:30:00Z
- **Completed:** 2026-03-19T20:38:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Added `Vault._check_schema_current()` using Alembic `MigrationContext.get_current_revision()` vs `ScriptDirectory.get_current_head()`, with correct pre-Alembic vault handling (None revision = current)
- Wired non-fatal `WARNING: Vault schema is out of date. Run 'ztlctl upgrade'` stderr message into `AppContext.vault` lazy init
- Added `_check_schema_version()` as a new check category to `CheckService.check()` with severity=error
- Added 4 tests covering: at-head, pre-Alembic vault (fresh fixture), stale stamp, and warning-on-vault-access via mock
- Added README CLI Command Reference section listing all 18 commands with descriptions, documenting `--log-json`, `ztlctl check`, `ztlctl upgrade`, `ztlctl serve`, `ztlctl vector`, `ztlctl workflow`

## Task Commits

1. **Task 1: Schema stale detection and stale check integration** - `c2fecaf` (feat)
2. **Task 2: UX polish and documentation audit** - `5e77cfc` (docs)

## Files Created/Modified

- `src/ztlctl/infrastructure/vault.py` — Added `_check_schema_current()` method
- `src/ztlctl/commands/_context.py` — Added stale warning in `vault` lazy property
- `src/ztlctl/services/check.py` — Added `CAT_SCHEMA_VERSION` constant and `_check_schema_version()` category
- `tests/services/test_upgrade.py` — Added `TestCheckSchemaCurrent` class with 4 tests
- `README.md` — Added CLI Command Reference section
- `tests/mcp/test_tools_impl.py` — Pre-existing untracked file from prior plan (fixed import sort, committed)

## Decisions Made

- Pre-Alembic vaults (tables exist, no `alembic_version` row, current=None) are treated as current, not stale. UpgradeService.apply() handles the stamping — _check_schema_current() does not need to distinguish "needs stamp" from "truly stale".
- Schema version check runs as first check category in `check()`, before opening the engine connection, to avoid holding an open connection while calling `_check_schema_current()` (which opens its own connection internally).
- README Quick Start section left unchanged; a separate "CLI Command Reference" section was added before Documentation to avoid disrupting the tutorial flow.
- Copier recopy fallback warning is already surfaced via `app.emit()` warnings loop — no additional CLI-level code needed.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed pre-existing ruff import sort in tests/mcp/test_tools_impl.py**
- **Found during:** Task 2 verification (`uv run ruff check .`)
- **Issue:** Untracked file from a prior plan had `I001` import sort error, causing `ruff check .` to fail
- **Fix:** Ran `uv run ruff check --fix tests/mcp/test_tools_impl.py` and committed the file
- **Files modified:** `tests/mcp/test_tools_impl.py`
- **Verification:** `uv run ruff check .` exits 0
- **Committed in:** `5e77cfc` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - pre-existing bug in untracked file blocking verification)
**Impact on plan:** Auto-fix required to pass `ruff check .` verification. No scope change.

## Issues Encountered

- Fresh vault fixture does not have an `alembic_version` table (it is the pre-Alembic state). The initial stale test tried to query `alembic_version` which raised `OperationalError`. Fixed by restructuring the test: the fresh vault is itself the pre-Alembic test case, and the "stale" test stamps first then overwrites the revision.

## Next Phase Readiness

- Phase 01-core-hardening is now complete (5/5 plans done)
- Schema stale detection ready for production: surfaced at CLI init, in `ztlctl check`, and documented in README
- All 1525 tests pass, mypy strict, ruff clean

---
*Phase: 01-core-hardening*
*Completed: 2026-03-19*
