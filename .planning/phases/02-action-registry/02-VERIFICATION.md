---
phase: 02-action-registry
verified: 2026-03-19T22:00:00Z
status: passed
score: 11/11 must-haves verified
re_verification: false
gaps: []
---

# Phase 2: Action Registry Verification Report

**Phase Goal:** Every core operation is described as a declarative ActionDefinition in a central registry, ready for presentation layer generation
**Verified:** 2026-03-19T22:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | ActionParam frozen dataclass captures name, type, required, default, description, choices, and CLI/MCP-specific flags | VERIFIED | `src/ztlctl/actions/definitions.py` — `@dataclass(frozen=True)` with all 10 fields confirmed |
| 2 | ActionDefinition frozen dataclass captures name, description, category, params, handler, side_effect, plus optional CLI and MCP metadata | VERIFIED | `definitions.py` — 13 fields present including `mcp_when_to_use`, `cli_group`, `custom_presentation` |
| 3 | ActionRegistry supports register/get/list_actions with name-uniqueness enforcement | VERIFIED | `src/ztlctl/actions/registry.py` — `register()` raises `ValueError` on duplicate, `get()` raises `KeyError` if missing, `list_actions()` supports AND-combined filters |
| 4 | get_action_registry() returns a module-level singleton | VERIFIED | `registry.py` line 89: `_REGISTRY = ActionRegistry()`, line 92: `get_action_registry()` returns `_REGISTRY` |
| 5 | BaseController accepts a Vault and exposes _vault and _dispatch_event() | VERIFIED | `src/ztlctl/controllers/base.py` — `__init__(self, vault: Vault)` stores `self._vault`, `_dispatch_event()` mirrors BaseService exactly |
| 6 | Each controller wraps its corresponding service via lazy local imports | VERIFIED | All 13 controllers confirmed; service imports are inside method bodies (e.g. `from ztlctl.services.check import CheckService` at line 18 inside `def check()`) |
| 7 | Controller methods return ServiceResult (same contract as services) | VERIFIED | All controller methods pass through `ServiceResult` from their wrapped service; mypy strict passes on all 19 files |
| 8 | Controllers construct services per-call, not as instance variables | VERIFIED | Every method constructs `XService(self._vault)` inline; no `self._service` attributes found |
| 9 | All ~50 public controller methods are registered as ActionDefinitions in the singleton registry | VERIFIED | 59 ActionDefinitions registered across 13 categories; `python -c "from ztlctl.actions import get_action_registry; print(len(get_action_registry().list_actions()))"` outputs 59 |
| 10 | Filtering by category, side_effect, and custom_presentation returns correct subsets | VERIFIED | `list_actions()` AND-logic confirmed; Read:29, Write:30, Custom:5 — verified by runtime check |
| 11 | custom_presentation=True is set on batch, init_vault, init_workflow, update_workflow, export_assets | VERIFIED | `_register_core.py` confirms 5 custom_presentation actions matching the specified set |

**Score:** 11/11 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/actions/definitions.py` | ActionParam and ActionDefinition frozen dataclasses | VERIFIED | 142 lines; both `@dataclass(frozen=True)` classes present with all required fields |
| `src/ztlctl/actions/registry.py` | ActionRegistry class and singleton accessor | VERIFIED | 95 lines; `ActionRegistry`, `_REGISTRY`, `get_action_registry()` all present |
| `src/ztlctl/actions/__init__.py` | Re-exports all 4 symbols + calls `_register_core_actions()` | VERIFIED | 9 lines; both re-exports and module-load-time call confirmed |
| `src/ztlctl/actions/_register_core.py` | Registration of all ~50 built-in ActionDefinitions | VERIFIED | 1970 lines; 59 `registry.register()` calls confirmed, `_register_core_actions()` function present |
| `src/ztlctl/controllers/base.py` | BaseController abstract base class | VERIFIED | 47 lines; `class BaseController:` with `_vault` and `_dispatch_event()` |
| `src/ztlctl/controllers/check.py` | CheckController wrapping CheckService | VERIFIED | `CheckController(BaseController)` with 4 methods (check, fix, rebuild, rollback) |
| `src/ztlctl/controllers/graph.py` | GraphController wrapping GraphService | VERIFIED | `GraphController(BaseController)` present in controllers package |
| `src/ztlctl/controllers/create.py` | CreateController wrapping CreateService | VERIFIED | 4 methods (create_note, create_reference, create_task, create_batch) confirmed |
| `src/ztlctl/controllers/query.py` | QueryController wrapping QueryService | VERIFIED | 10 methods confirmed by lazy service import pattern |
| `src/ztlctl/controllers/session.py` | SessionController wrapping SessionService | VERIFIED | 9 methods including start, close, reopen, status, log_entry, cost, context, brief, extract_decision |
| `src/ztlctl/controllers/init_ctrl.py` | InitController wrapping InitService | VERIFIED | `class InitController(BaseController):` present |
| `src/ztlctl/controllers/__init__.py` | Re-exports all 14 classes | VERIFIED | All 14 names in `__all__` (BaseController + 13 controllers) |
| `tests/actions/test_definitions.py` | Unit tests for ActionParam and ActionDefinition | VERIFIED | 177 lines (min 80); `TestActionParam` and `TestActionDefinition` classes present, `test_frozen` and `test_hashable` confirmed |
| `tests/actions/test_registry.py` | Unit tests for ActionRegistry | VERIFIED | 155 lines (min 60); `TestActionRegistry` and `TestGetActionRegistry` classes present |
| `tests/actions/test_core_registrations.py` | Integration tests for core registrations | VERIFIED | 444 lines (min 80); 4 test classes, 33 tests including count, lookup, filtering, and handler parity |
| `tests/controllers/test_base.py` | BaseController tests | VERIFIED | 56 lines; `TestBaseController` with `test_dispatch_event_noop_when_no_bus` |
| `tests/controllers/test_check.py` | CheckController integration tests | VERIFIED | 61 lines (min 30); `TestCheckController` with `test_check_returns_service_result` |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ztlctl/actions/__init__.py` | `src/ztlctl/actions/definitions.py` | re-exports ActionParam, ActionDefinition | WIRED | Line 4: `from ztlctl.actions.definitions import ActionDefinition, ActionParam` |
| `src/ztlctl/actions/__init__.py` | `src/ztlctl/actions/registry.py` | re-exports ActionRegistry, get_action_registry | WIRED | Line 5: `from ztlctl.actions.registry import ActionRegistry, get_action_registry` |
| `src/ztlctl/controllers/check.py` | `src/ztlctl/services/check.py` | lazy local import inside methods | WIRED | `from ztlctl.services.check import CheckService` inside each method body (lines 18, 24, 30, 36) |
| `src/ztlctl/controllers/base.py` | mirrors BaseService structure | class BaseController | WIRED | `class BaseController:` with identical `_vault` + `_dispatch_event()` signature to BaseService |
| `src/ztlctl/controllers/create.py` | `src/ztlctl/services/create.py` | lazy local import | WIRED | `from ztlctl.services.create import CreateService` confirmed inside method bodies |
| `src/ztlctl/controllers/query.py` | `src/ztlctl/services/query.py` | lazy local import | WIRED | `from ztlctl.services.query import QueryService` confirmed (10 occurrences) |
| `src/ztlctl/controllers/session.py` | `src/ztlctl/services/session.py` | lazy local import | WIRED | `from ztlctl.services.session import SessionService` confirmed (9 occurrences) |
| `src/ztlctl/actions/_register_core.py` | `src/ztlctl/actions/registry.py` | get_action_registry().register() | WIRED | 59 `registry.register()` calls confirmed; `get_action_registry()` call on line 33 |
| `src/ztlctl/actions/_register_core.py` | `src/ztlctl/controllers/` | lambda factories referencing controller methods | WIRED | Factory pattern `lambda vault, **kw: Controller(vault).method(**kw)` confirmed (e.g. line 107) |
| `src/ztlctl/actions/__init__.py` | `src/ztlctl/actions/_register_core.py` | module-load-time call to `_register_core_actions()` | WIRED | Line 3: import; line 7: `_register_core_actions()` called at module level |

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| ACTN-01 | 02-01, 02-04 | ActionDefinition dataclass — name, typed params (ActionParam), service method binding, CLI metadata, MCP metadata | SATISFIED | `definitions.py` implements all required fields; `_register_core.py` populates mcp_when_to_use, mcp_avoid_when, mcp_common_errors, cli_group, cli_interactive_params for all 59 registered actions |
| ACTN-02 | 02-01, 02-02, 02-03, 02-04 | ActionRegistry — collects ActionDefinitions from core modules and plugins; validates uniqueness; provides lookup by name; single source of truth | SATISFIED | `registry.py` enforces name-uniqueness on `register()`, `get()` by name works, `list_actions()` is the single enumeration point; 112 tests green including singleton identity test |

No orphaned requirements found — both ACTN-01 and ACTN-02 are claimed by plan frontmatter and their implementations are confirmed in the codebase.

---

## Anti-Patterns Found

No anti-patterns detected.

- No TODO/FIXME/PLACEHOLDER comments in `src/ztlctl/actions/` or `src/ztlctl/controllers/`
- No stub implementations (all controller methods delegate to real service calls)
- No empty handlers (all 59 registered actions have factory lambda handlers that construct real controllers)
- `uv run ruff check src/ztlctl/actions/ src/ztlctl/controllers/` — clean
- `uv run mypy src/ztlctl/actions/ src/ztlctl/controllers/` — 0 errors across 19 files

---

## Human Verification Required

None. All observable truths in this phase are structural and can be verified programmatically. The phase goal produces infrastructure artifacts (dataclasses, registry, controllers, registrations) rather than user-facing UI or external service integrations.

---

## Test Results Summary

| Suite | Tests | Result |
|-------|-------|--------|
| `tests/actions/test_definitions.py` | 18 | passed |
| `tests/actions/test_registry.py` | 10 | passed |
| `tests/actions/test_core_registrations.py` | 33 | passed |
| `tests/controllers/test_base.py` | 4 | passed |
| `tests/controllers/test_check.py` | 7 | passed |
| `tests/controllers/test_create.py` | 10 | passed |
| `tests/controllers/test_query.py` | 15 | passed |
| `tests/controllers/test_session.py` | 10 | passed |
| `tests/controllers/test_upgrade.py` | 5 | passed |
| **Total** | **112** | **all passed** |

---

## Phase Goal Assessment

**Goal: Every core operation is described as a declarative ActionDefinition in a central registry, ready for presentation layer generation**

This goal is fully achieved:

1. **Declarative ActionDefinition** — `definitions.py` provides a frozen dataclass with 13 fields covering core identity, MCP guidance, CLI metadata, and a presentation escape hatch. Each field serves a specific downstream consumer.

2. **Central registry** — `registry.py` provides a singleton `ActionRegistry` accessible via `get_action_registry()`. Registration happens once at module-load time via `_register_core_actions()` in `__init__.py`.

3. **Every core operation** — 59 ActionDefinitions registered across 13 categories, covering all controller methods for CheckService, UpgradeService, ExportService, GraphService, VectorService, ReweaveService, CreateService, UpdateService, QueryService, SessionService, IngestService, WorkflowService, and InitService.

4. **Ready for presentation layer generation** — All 59 entries carry `cli_group`, `cli_interactive_params`, `cli_examples`, `mcp_when_to_use`, `mcp_avoid_when`, `mcp_common_errors`, and `custom_presentation` flags. The `ActionParam` descriptors include `cli_is_argument`, `cli_multiple`, `cli_flag`, `choices`, and `mcp_example` — exactly the metadata needed for auto-generating Click options and MCP tool schemas.

---

_Verified: 2026-03-19T22:00:00Z_
_Verifier: Claude (gsd-verifier)_
