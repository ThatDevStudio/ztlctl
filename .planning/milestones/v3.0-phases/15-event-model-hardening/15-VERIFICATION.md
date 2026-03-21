---
phase: 15-event-model-hardening
verified: 2026-03-21T18:30:00Z
status: passed
score: 11/11 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 9/11
  gaps_closed:
    - "Every mutating action has exactly one post_action producer — the service layer (Gap 1)"
    - "All post_action events carry ActionEvent payload shape through the WAL (Gap 2)"
    - "REQUIREMENTS.md status table reflects completion of ARCH-04 and DEBT-02 (Gap 3)"
  gaps_remaining: []
  regressions: []
---

# Phase 15: Event Model Hardening — Verification Report

**Phase Goal:** Event delivery is reliable — one canonical post-commit payload shape, service-only emission, and graceful shutdown/startup drain
**Verified:** 2026-03-21T18:30:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (Plan 04)

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | EventBusConfig has correct fields and defaults | VERIFIED | `src/ztlctl/config/models.py`: `class EventBusConfig(BaseModel)` with all 4 fields, correct defaults |
| 2 | ZtlSettings exposes eventbus: EventBusConfig field | VERIFIED | `src/ztlctl/config/settings.py`: import + `eventbus: EventBusConfig` field |
| 3 | ActionEvent model validates required fields with Literal constraint | VERIFIED | `src/ztlctl/domain/events.py`: frozen, action_name/side_effect/payload/warnings/result all present |
| 4 | EventBus constructor accepts EventBusConfig and uses configurable timeouts | VERIFIED | `event_bus.py`: config param, `self._per_future_timeout`, `self._shutdown_timeout`, `self._dead_letter_retention_days` all stored |
| 5 | Shutdown drain waits with bounded timeout on CLI exit | VERIFIED | `commands/_context.py`: `wait_for_events=True`, uses `eventbus.shutdown_timeout_seconds` |
| 6 | Startup drain retries pending WAL events before new work begins | VERIFIED | `vault.py`: `self._event_bus.drain()` in `init_event_bus()` |
| 7 | Every mutating action has exactly one post_action producer — the service layer | VERIFIED | `_dispatch_post_action_event` called at 14 call sites across 6 service files (commit d21fa08). Structural regression test `tests/services/test_post_action_dispatch.py` passes (1 passed). |
| 8 | All post_action events carry ActionEvent payload shape through the WAL | VERIFIED | Each call site passes `result.data` as payload; `base.py:_dispatch_post_action_event` constructs `ActionEvent(action_name=..., side_effect="write", payload=..., warnings=..., result=...)` and dispatches via `bus.dispatch("post_action", event.model_dump(), ...)` |
| 9 | Dead-letter events reported in ztlctl check at info severity | VERIFIED | `services/check.py`: dead_letter count query, SEVERITY_INFO issue appended |
| 10 | Startup drain auto-purges dead-letter events older than retention window | VERIFIED | `vault.py`: `purge_dead_letters()` called before `drain()` in `init_event_bus()` |
| 11 | event_purge action registered under maintenance category | VERIFIED | `actions/_register_core.py`: `name="event_purge"`, `category="maintenance"` |

**Score:** 11/11 truths verified

---

## Required Artifacts

### Plan 01 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/config/models.py` | EventBusConfig frozen Pydantic model | VERIFIED | `class EventBusConfig(BaseModel)` with all 4 fields |
| `src/ztlctl/domain/events.py` | ActionEvent frozen Pydantic model | VERIFIED | Frozen, all required fields, `Literal["write","read"]` constraint |
| `src/ztlctl/config/settings.py` | eventbus field on ZtlSettings | VERIFIED | `eventbus: EventBusConfig` field present |
| `src/ztlctl/plugins/event_bus.py` | Configurable EventBus constructor | VERIFIED | `self._per_future_timeout`, `self._shutdown_timeout`, `self._dead_letter_retention_days` all stored |

### Plan 02 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/services/base.py` | _dispatch_post_action_event for service-side emission | VERIFIED | Method defined and now called by all 6 write service files (14 call sites total) |
| `src/ztlctl/commands/_context.py` | Bounded shutdown drain in close() | VERIFIED | `wait_for_events=True` + timeout from config |
| `src/ztlctl/infrastructure/vault.py` | Startup drain in init_event_bus() | VERIFIED | `drain()` called; `purge_dead_letters()` called before it |
| `src/ztlctl/controllers/base.py` | _dispatch_post_action removed | VERIFIED | Method not defined; controller-side dispatch absent |
| `tests/controllers/test_post_action_removal.py` | AST-based regression test | VERIFIED | Exists; uses ast.parse, checks all controller files |

### Plan 03 Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/services/check.py` | Dead-letter count in structural validation | VERIFIED | `event_wal.c.status == "dead_letter"` query in `_check_structural_validation` |
| `src/ztlctl/plugins/event_bus.py` | purge_dead_letters method | VERIFIED | `def purge_dead_letters` present; respects `dead_letter_retention_days` |
| `src/ztlctl/actions/_register_core.py` | event_purge ActionDefinition | VERIFIED | `name="event_purge"`, `category="maintenance"` |
| `src/ztlctl/controllers/check.py` | event_purge controller method | VERIFIED | `def event_purge` delegates to `bus.purge_dead_letters` |

### Plan 04 Artifacts (Gap Closure)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/services/create.py` | post_action dispatch for _create_content, create_batch | VERIFIED | 2 call sites confirmed (lines 301, 368) |
| `src/ztlctl/services/update.py` | post_action dispatch for update, archive | VERIFIED | 2 call sites confirmed (lines 249, 311) |
| `src/ztlctl/services/session.py` | post_action dispatch for start, close, reopen, extract_decision | VERIFIED | 4 call sites confirmed (lines 123, 242, 323, 642) |
| `src/ztlctl/services/reweave.py` | post_action dispatch for reweave, prune, undo | VERIFIED | 3 call sites confirmed (lines 174, 262, 330) |
| `src/ztlctl/services/check.py` | post_action dispatch for fix, rebuild | VERIFIED | 2 call sites confirmed (lines 155, 284) |
| `src/ztlctl/services/graph.py` | post_action dispatch for unlink | VERIFIED | 1 call site confirmed (line 508) |
| `tests/services/test_post_action_dispatch.py` | Structural regression test | VERIFIED | Exists; 1 passed — AST scan of all 6 service files |
| `.planning/REQUIREMENTS.md` | ARCH-04 and DEBT-02 marked Complete | VERIFIED | `[x] **ARCH-04**` and `[x] **DEBT-02**` confirmed; traceability table shows both as Complete |

---

## Key Link Verification

### Plan 01 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `config/settings.py` | `config/models.py` | import EventBusConfig | WIRED | `from ztlctl.config.models import ... EventBusConfig` |
| `plugins/event_bus.py` | `config/models.py` | EventBusConfig parameter | WIRED | `config: EventBusConfig \| None = None` in constructor |

### Plan 02 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/base.py` | `plugins/event_bus.py` | _dispatch_post_action_event calls bus.dispatch | WIRED | `bus.dispatch("post_action", event.model_dump(), session_id=session_id)` at base.py:88 |
| `commands/_context.py` | `infrastructure/vault.py` | close() passes wait_for_events=True | WIRED | `self._vault.close(wait_for_events=True, timeout=timeout)` |
| `infrastructure/vault.py` | `plugins/event_bus.py` | init_event_bus calls drain() | WIRED | `self._event_bus.drain()` in init_event_bus |

### Plan 03 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/check.py` | `infrastructure/database/schema.py` | query event_wal for dead_letter rows | WIRED | `event_wal.c.status == "dead_letter"` in _check_structural_validation |
| `infrastructure/vault.py` | `plugins/event_bus.py` | startup drain calls purge_dead_letters | WIRED | `self._event_bus.purge_dead_letters()` before drain() |

### Plan 04 Key Links

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/create.py` | `services/base.py` | self._dispatch_post_action_event() inherited call | WIRED | 2 call sites confirmed |
| `services/update.py` | `services/base.py` | self._dispatch_post_action_event() inherited call | WIRED | 2 call sites confirmed |
| `services/session.py` | `services/base.py` | self._dispatch_post_action_event() inherited call | WIRED | 4 call sites confirmed |
| `services/reweave.py` | `services/base.py` | self._dispatch_post_action_event() inherited call | WIRED | 3 call sites confirmed |
| `services/check.py` | `services/base.py` | self._dispatch_post_action_event() inherited call | WIRED | 2 call sites confirmed |
| `services/graph.py` | `services/base.py` | self._dispatch_post_action_event() inherited call | WIRED | 1 call site confirmed |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| ARCH-01 | 15-02 | WAL rows drain on CLI shutdown with bounded timeout | SATISFIED | `AppContext.close()` uses `wait_for_events=True` + `shutdown_timeout_seconds`; REQUIREMENTS.md `[x]`, traceability: Complete |
| ARCH-02 | 15-02 | Pending WAL events from prior runs drain on startup | SATISFIED | `Vault.init_event_bus()` calls `self._event_bus.drain()`; REQUIREMENTS.md `[x]`, traceability: Complete |
| ARCH-03 | 15-02, 15-04 | Write-side post_action emitted by services only | SATISFIED | Controllers: 0 call sites (64 removed). Services: 14 call sites across 6 files. Structural tests for both sides pass. REQUIREMENTS.md `[x]`, traceability: Complete |
| ARCH-04 | 15-01 | Canonical ActionEvent payload model with stable shape | SATISFIED | `domain/events.py`: frozen model with action_name, side_effect, payload, warnings, result. REQUIREMENTS.md `[x]`, traceability: Complete |
| DEBT-02 | 15-01 | EventBus timeout configurable via settings | SATISFIED | `EventBusConfig` in `config/models.py`; `ZtlSettings.eventbus` field; EventBus constructor accepts config; `_wait_futures` uses `self._per_future_timeout`. REQUIREMENTS.md `[x]`, traceability: Complete |
| DEBT-03 | 15-03 | Dead-letter accumulation resolved | SATISFIED | `purge_dead_letters()` method; startup auto-purge; `check` reporting; `event_purge` action registered. REQUIREMENTS.md `[x]`, traceability: Complete |

**All 6 requirements satisfied. No orphaned requirements.**

---

## Anti-Patterns Found

None. The previously-identified blocker (orphan `_dispatch_post_action_event` method) is resolved by Plan 04 (commit d21fa08). The documentation gap (ARCH-04 and DEBT-02 Pending in REQUIREMENTS.md) is resolved by commit 25cf223. No new anti-patterns detected in the gap-closure changes.

---

## Human Verification Required

The human verification item from the initial report (end-to-end post_action WAL dispatch from a write command) can now be attempted, but the automated structural tests provide sufficient confidence that the pipeline is correctly wired. The `test_post_action_dispatch.py` structural test passes, confirming all 14 write-method call sites are present. The `test_post_action_removal.py` test confirms controllers have no call sites.

No blocking human verification remains.

---

## Re-Verification Summary

Three gaps from the initial verification are closed:

**Gap 1 (Blocker — Closed):** `_dispatch_post_action_event` was an orphan method defined on `BaseService` but never called by any service. Plan 04 added 14 call sites across `create.py` (2), `update.py` (2), `session.py` (4), `reweave.py` (3), `check.py` (2), and `graph.py` (1). Commit d21fa08.

**Gap 2 (Blocker — Closed, consequence of Gap 1):** No ActionEvent payloads reached the WAL from real service operations. Now that all write services call `_dispatch_post_action_event`, the `ActionEvent` model is constructed and dispatched via `bus.dispatch("post_action", event.model_dump(), ...)` for every mutating operation.

**Gap 3 (Documentation — Closed):** REQUIREMENTS.md checklist and traceability table entries for ARCH-04 and DEBT-02 were still showing as incomplete. Both are now marked `[x]` (checked) in the requirements list and `Complete` in the traceability table. Commit 25cf223.

No regressions introduced. Full structural regression coverage added via `tests/services/test_post_action_dispatch.py`.

---

_Verified: 2026-03-21T18:30:00Z_
_Verifier: Claude (gsd-verifier)_
