---
phase: 02-action-registry
plan: "02"
subsystem: controllers
tags: [controllers, orchestration, service-wrapper, tdd]
dependency_graph:
  requires:
    - src/ztlctl/services/base.py
    - src/ztlctl/services/check.py
    - src/ztlctl/services/upgrade.py
    - src/ztlctl/services/export.py
    - src/ztlctl/services/graph.py
    - src/ztlctl/services/vector.py
    - src/ztlctl/services/reweave.py
  provides:
    - src/ztlctl/controllers/ (full package)
  affects:
    - src/ztlctl/actions/ (registry layer will import controllers)
tech_stack:
  added: []
  patterns:
    - BaseController mirrors BaseService (vault + _dispatch_event)
    - Lazy local imports inside each method body (no module-level service imports)
    - Controllers construct services per-call (not instance variables)
key_files:
  created:
    - src/ztlctl/controllers/__init__.py
    - src/ztlctl/controllers/base.py
    - src/ztlctl/controllers/check.py
    - src/ztlctl/controllers/upgrade.py
    - src/ztlctl/controllers/export.py
    - src/ztlctl/controllers/graph.py
    - src/ztlctl/controllers/vector.py
    - src/ztlctl/controllers/reweave.py
    - tests/controllers/__init__.py
    - tests/controllers/test_base.py
    - tests/controllers/test_check.py
    - tests/controllers/test_upgrade.py
  modified: []
decisions:
  - ReweaveController uses actual service signature (content_id, dry_run, min_score_override) not the plan example (threshold, max_links)
  - export_graph passes fmt kwarg directly matching ExportService.export_graph(fmt=...) signature
  - GraphController.related uses (depth, top) matching service — plan listed (depth, max_results) which was incorrect
metrics:
  duration_seconds: 195
  tasks_completed: 2
  files_created: 12
  files_modified: 0
  completed_date: "2026-03-19"
requirements: [ACTN-02]
---

# Phase 02 Plan 02: Controller Layer Summary

**One-liner:** BaseController + 6 service wrappers (Check, Upgrade, Export, Graph, Vector, Reweave) using lazy local imports, mirroring BaseService pattern.

## What Was Built

Created `src/ztlctl/controllers/` package as the orchestration layer between the registry and services:

- **BaseController** (`base.py`): Mirrors BaseService exactly — accepts Vault, stores as `_vault`, copies `_dispatch_event()` verbatim. Invariants documented in docstring.

- **CheckController** (`check.py`): Wraps `check()`, `fix()`, `rebuild()`, `rollback()`.

- **UpgradeController** (`upgrade.py`): Wraps `check_pending()`, `apply()`, `stamp_current()`.

- **ExportController** (`export.py`): Wraps `export_markdown()`, `export_indexes()`, `export_graph()`, `export_dashboard()` — includes ExportFilters type hint via TYPE_CHECKING guard.

- **GraphController** (`graph.py`): Wraps all 8 GraphService methods: `related()`, `themes()`, `rank()`, `path()`, `gaps()`, `bridges()`, `unlink()`, `materialize_metrics()`.

- **VectorController** (`vector.py`): Wraps `reindex_all()` (only public ServiceResult-returning method).

- **ReweaveController** (`reweave.py`): Wraps `reweave()`, `prune()`, `undo()` with exact service signatures.

- **Integration tests** (16 tests): TestBaseController (4), TestCheckController (7), TestUpgradeController (5) — all pass against real vault fixtures.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] ReweaveController signature corrected to match actual service**
- **Found during:** Task 2 implementation
- **Issue:** Plan example showed `threshold: float = 0.3, max_links: int = 10` but actual `ReweaveService.reweave()` uses `dry_run: bool = False, min_score_override: float | None = None`
- **Fix:** Used actual service signature to maintain pass-through correctness
- **Files modified:** `src/ztlctl/controllers/reweave.py`

**2. [Rule 1 - Bug] GraphController.related() uses (depth, top) not (depth, max_results)**
- **Found during:** Task 1 — reading actual GraphService.related() signature
- **Issue:** Plan listed `max_results=20` but service uses `top: int = 20`
- **Fix:** Used actual service signature

None beyond the above signature corrections — plan executed cleanly.

## Verification

- `uv run pytest tests/controllers/ -x -q`: 16 passed
- `uv run mypy src/ztlctl/controllers/`: Success, no issues in 8 source files
- `uv run ruff check src/ztlctl/controllers/`: All checks passed
- `uv run pytest` (full suite): 1597 passed, 2 skipped — no regressions

## Self-Check: PASSED

All files verified present. Commits c0ae4a1 and e24b95b confirmed in git log.
