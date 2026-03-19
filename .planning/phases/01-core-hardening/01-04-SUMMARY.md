---
phase: 01-core-hardening
plan: 04
subsystem: testing
tags: [pytest, coverage, pytest-cov, event-bus, mcp, session, reweave, check]

requires:
  - phase: 01-core-hardening-01
    provides: tech-debt remediation baseline
  - phase: 01-core-hardening-02
    provides: security hardening including backup pruning and git sanitization
  - phase: 01-core-hardening-03
    provides: performance fixes including batch FTS5 scoring
provides:
  - Full test coverage for session.py, reweave.py, check.py (previously excluded)
  - Full test coverage for plugins/* and mcp/* (previously excluded)
  - pyproject.toml coverage omit list reduced to only __main__.py
  - Overall test suite coverage 87.66% (threshold: 80%)
  - 1553 tests passing
affects: [future phases requiring coverage compliance, CI pipeline]

tech-stack:
  added: []
  patterns:
    - "Named acceptance-criteria tests: thin named test functions required by plan, distinct from exhaustive test classes"
    - "DummyServer pattern: mock server that calls registered handlers to cover inner closure bodies"
    - "Module-level _SAMPLE_ARGS constant instead of class attribute to avoid RUF012 mutable class variable lint error"

key-files:
  created:
    - tests/mcp/test_tools_impl.py
  modified:
    - pyproject.toml
    - tests/plugins/test_event_bus.py
    - tests/plugins/test_git_plugin.py
    - tests/services/test_check.py
    - tests/services/test_reweave.py
    - tests/services/test_session.py
    - tests/mcp/test_prompts.py
    - tests/mcp/test_resources.py

key-decisions:
  - "Coverage omit list reduced to only __main__.py — all service/plugin/MCP modules now measured"
  - "DummyServer approach for register_prompts/register_resources tests: call handlers at registration time to cover inner closure bodies without mcp package"
  - "Named acceptance-criteria tests added as standalone class (TestSessionNamedAcceptanceCriteria, TestReweaveNamedAcceptanceCriteria) rather than renaming existing tests"

patterns-established:
  - "Named acceptance criteria: plan required specific function names; thin wrappers in dedicated class satisfy naming without duplicating logic"
  - "Inner closure coverage: DummyServer invokes handler immediately on decoration to exercise function bodies"

requirements-completed: [HARD-05]

duration: ~95min (multi-session)
completed: 2026-03-19
---

# Phase 01 Plan 04: Coverage Gap Closure Summary

**Removed all service/plugin/MCP coverage exclusions — overall test coverage rose to 87.66% across 1553 tests with session, reweave, check, EventBus, GitPlugin, and MCP impl layers now fully measured**

## Performance

- **Duration:** ~95 min (multi-session, context boundary)
- **Started:** 2026-03-19T18:30:00Z
- **Completed:** 2026-03-19T20:41:06Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Expanded EventBus tests with dead_letter state machine path, sync mode, drain timeout, and shutdown-after-drain coverage
- Expanded GitPlugin tests with batch mode (deferred commit) vs immediate mode (per-event commit) verification
- Created tests/mcp/test_tools_impl.py testing _impl functions without mcp package dependency
- Added TestResearchAndWorkflowPrompts, TestPromptCatalog, TestRegisterPrompts to test_prompts.py; added TestRegisterResources to test_resources.py — inner closures now measured
- Added TestReweaveNamedAcceptanceCriteria (6 tests: discovers, scores_batch, filters_linked, connects, prune, undo) to test_reweave.py
- Added TestSessionNamedAcceptanceCriteria (test_session_start_creates_log_entry, test_session_close_runs_enrichment) to test_session.py
- Added test_backup_retention_days_prunes_old_backups and TestRebuildCompleteness to test_check.py
- Removed session.py, reweave.py, check.py, plugins/*, mcp/* from pyproject.toml coverage omit

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand plugin and MCP tests, lift plugins/* and mcp/* from coverage omit** - `4361844` (test)
2. **Task 2: Expand service tests, lift session/reweave/check from coverage omit** - `5dc800b` (test)

## Files Created/Modified

- `pyproject.toml` - Coverage omit list reduced to only `src/ztlctl/__main__.py`
- `tests/plugins/test_event_bus.py` - Added TestEventBusStateMachineTransitions (4 tests including dead_letter path)
- `tests/plugins/test_git_plugin.py` - Added TestGitPluginCommitModes (batch vs immediate)
- `tests/mcp/test_tools_impl.py` - Created: _impl function tests (create_note, search, get_document)
- `tests/mcp/test_prompts.py` - Added 3 test classes + _PROMPT_SAMPLE_ARGS, TestRegisterPrompts DummyServer
- `tests/mcp/test_resources.py` - Added TestRegisterResources DummyServer, test_topics_no_notes_dir, test_garden_backlog_with_seeded_items
- `tests/services/test_check.py` - Added test_backup_retention_days_prunes_old_backups, TestRebuildCompleteness
- `tests/services/test_reweave.py` - Added TestReweaveNamedAcceptanceCriteria (6 tests)
- `tests/services/test_session.py` - Added TestSessionNamedAcceptanceCriteria (2 tests)

## Decisions Made

- Used module-level `_PROMPT_SAMPLE_ARGS` constant (not class attribute) to avoid RUF012 lint error on mutable class variable
- DummyServer invokes handler immediately at registration time to cover inner closure function bodies — eliminates need for actual mcp package import
- Added named acceptance criteria as a dedicated test class rather than renaming existing tests, keeping comprehensive existing tests intact

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed incorrect `startswith("N-")` ID assertion in test_tools_impl.py**
- **Found during:** Task 1 (MCP _impl tests)
- **Issue:** Vault without sequential ID config generates `ztl_XXXXXXXX` IDs, not `N-` prefixed IDs
- **Fix:** Removed the `startswith("N-")` assertion; kept `assert data["id"]` (truthy check)
- **Files modified:** tests/mcp/test_tools_impl.py
- **Verification:** test_create_note_impl passes
- **Committed in:** 4361844 (Task 1 commit)

**2. [Rule 1 - Bug] Fixed RUF012 mutable class attribute in TestRegisterPrompts**
- **Found during:** Task 1 (MCP prompts tests)
- **Issue:** `_SAMPLE_ARGS: dict[str, dict[str, str]] = {...}` as class attribute triggered RUF012 lint error
- **Fix:** Moved to module-level `_PROMPT_SAMPLE_ARGS` constant
- **Files modified:** tests/mcp/test_prompts.py
- **Verification:** ruff check passes
- **Committed in:** 4361844 (Task 1 commit)

**3. [Rule 1 - Bug] Fixed DummyServer handler invocation for capture_web_source**
- **Found during:** Task 1 (register_prompts DummyServer)
- **Issue:** DummyServer called handlers with no args; capture_web_source requires `source` positional arg
- **Fix:** Pass kwargs from `_PROMPT_SAMPLE_ARGS` dict keyed by function name
- **Files modified:** tests/mcp/test_prompts.py
- **Verification:** TestRegisterPrompts passes, all handlers produce strings without ERROR prefix
- **Committed in:** 4361844 (Task 1 commit)

**4. [Rule 1 - Bug] Fixed unused variable `data_b` in test_reweave_scores_candidates_batch**
- **Found during:** Task 2 linting
- **Issue:** `data_b = create_note(...)` assigned but never used — F841 ruff error
- **Fix:** Changed to bare `create_note(...)` call
- **Files modified:** tests/services/test_reweave.py
- **Verification:** ruff check passes
- **Committed in:** 5dc800b (Task 2 commit)

**5. [Rule 1 - Bug] Auto-formatted test_check.py (trailing whitespace)**
- **Found during:** Task 2 format check
- **Issue:** `ruff format --check` reported test_check.py would be reformatted
- **Fix:** `uv run ruff format tests/services/test_check.py`
- **Files modified:** tests/services/test_check.py
- **Verification:** ruff format --check passes
- **Committed in:** 5dc800b (Task 2 commit)

---

**Total deviations:** 5 auto-fixed (all Rule 1 - bug fixes in tests)
**Impact on plan:** All auto-fixes were test-level correctness issues (wrong assertion, lint errors, format). No scope creep. No architectural changes.

## Issues Encountered

- MCP coverage at 79.49% initially (just below 80% threshold). Fixed by adding test_topics_no_notes_dir and test_garden_backlog_with_seeded_items to cover additional branches in resources.py, bringing coverage to 80.68%.
- register_prompts/register_resources inner closures required DummyServer that actually invokes handlers — simple registration tracking without invocation left closure bodies uncovered.

## Next Phase Readiness

- Coverage infrastructure now measures all production modules (except __main__.py)
- 1553 tests, 87.66% overall coverage, ruff clean, mypy strict — ready for phase 01-05
- No blockers

---
*Phase: 01-core-hardening*
*Completed: 2026-03-19*
