---
phase: 07-plugin-agentic-wiring-fixes
verified: 2026-03-20T06:00:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 7: Plugin-Agentic Wiring Fixes Verification Report

**Phase Goal:** Close all integration gaps identified by the v2.0 milestone audit — wire pre/post-action hooks into controllers, connect plugin config injection, forward error detail to MCP, and resolve category activation semantics
**Verified:** 2026-03-20T06:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Plugins loaded from entry points receive validated TOML config during vault initialization | VERIFIED | `pm.inject_configs(self._settings)` at vault.py:378, immediately after `discover_and_load()` and before built-in plugin registration |
| 2 | MCP error responses include full structured error detail from ServiceError | VERIFIED | `detail=result.error.detail` in McpError constructor at response.py:161 |
| 3 | Category activation is documented as advisory metadata, not dynamic tool gating | VERIFIED | 5-line comment block at generator.py:92-96 co-located with `_active_categories` assignment |
| 4 | Every controller method in batch 1 calls `_dispatch_pre_action` before service delegation | VERIFIED | Exact counts: check=4, create=4, discovery=3, export=4, graph=8, ingest=4, init_ctrl=3 |
| 5 | Every controller method in batch 2 calls `_dispatch_pre_action` before service delegation | VERIFIED | Exact counts: query=10, reweave=3, session=9, update=3, upgrade=3, vector=2, workflow=4 |
| 6 | A plugin returning ActionRejection prevents service execution and returns a ServiceResult error | VERIFIED | All 30+33 methods include rejection guard returning `ServiceResult(ok=False, error=ServiceError(code="ACTION_REJECTED", ...))` |
| 7 | `_dispatch_post_action` fires after every successful service call | VERIFIED | Post-action counts match pre-action counts in all sampled controllers (check=4, query=10, vector=2) |
| 8 | Internal flag `dispatch_post_create` is excluded from the kwargs dict passed to plugins | VERIFIED | No `"dispatch_post_create":` key in any kwargs dict in create.py |
| 9 | Non-ServiceResult WorkflowController methods are NOT wired with hooks | VERIFIED | `read_answers`, `profile_choices`, `default_choices` contain no `_dispatch_pre_action` call |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/infrastructure/vault.py` | `inject_configs()` call in `init_event_bus()` | VERIFIED | Line 378: `pm.inject_configs(self._settings)` with PLUG-03 comment |
| `src/ztlctl/mcp/response.py` | Error detail forwarding + ACTION_REJECTED recovery entry | VERIFIED | Line 161: `detail=result.error.detail`; line 33: `ACTION_REJECTED` in COMMON_ERROR_RECOVERY |
| `src/ztlctl/mcp/generator.py` | Advisory-only design documentation | VERIFIED | Lines 92-96: multi-line advisory comment block |
| `src/ztlctl/controllers/check.py` | Hook-wired check, fix, rebuild, rollback | VERIFIED | 4 `_dispatch_pre_action` + 4 `_dispatch_post_action` calls |
| `src/ztlctl/controllers/create.py` | Hook-wired create_note, create_reference, create_task, create_batch | VERIFIED | 4 pre + 4 post, `dispatch_post_create` excluded from kwargs |
| `src/ztlctl/controllers/discovery.py` | Hook-wired discover_categories, activate_category, deactivate_category | VERIFIED | 3 pre + 3 post calls |
| `src/ztlctl/controllers/export.py` | Hook-wired export_markdown, export_indexes, export_graph, export_dashboard | VERIFIED | 4 pre + 4 post calls |
| `src/ztlctl/controllers/graph.py` | Hook-wired 8 methods | VERIFIED | 8 pre + 8 post calls |
| `src/ztlctl/controllers/ingest.py` | Hook-wired list_providers, ingest_text, ingest_file, ingest_url | VERIFIED | 4 pre + 4 post calls |
| `src/ztlctl/controllers/init_ctrl.py` | Hook-wired init_vault, regenerate_self, check_staleness | VERIFIED | 3 pre + 3 post calls |
| `src/ztlctl/controllers/query.py` | Hook-wired 10 methods | VERIFIED | 10 pre + 10 post calls |
| `src/ztlctl/controllers/reweave.py` | Hook-wired reweave, prune, undo | VERIFIED | 3 pre + 3 post calls |
| `src/ztlctl/controllers/session.py` | Hook-wired 9 methods | VERIFIED | 9 pre + 9 post calls |
| `src/ztlctl/controllers/update.py` | Hook-wired update, archive, supersede | VERIFIED | 3 pre + 3 post calls |
| `src/ztlctl/controllers/upgrade.py` | Hook-wired check_pending, apply, stamp_current | VERIFIED | 3 pre + 3 post calls |
| `src/ztlctl/controllers/vector.py` | Hook-wired status (as `vector_status`), reindex_all | VERIFIED | Action name `"vector_status"` confirmed at line 23, 27, 45, 47 |
| `src/ztlctl/controllers/workflow.py` | Hook-wired 4 ServiceResult methods; 3 helpers left unwired | VERIFIED | 4 pre + 4 post calls; read_answers/profile_choices/default_choices have no dispatch |
| `tests/controllers/test_hook_wiring.py` | 8 spot-check tests for batch 1 controllers | VERIFIED | 8 test functions; includes `test_rejection_prevents_service_call` and `test_create_controller_create_note_excludes_dispatch_flag` |
| `tests/controllers/test_hook_wiring_batch2.py` | 9 spot-check tests for batch 2 controllers | VERIFIED | 9 test functions; includes `test_vector_controller_status_uses_vector_status_action` and `test_workflow_controller_skip_non_service_result_methods` |
| `tests/mcp/test_response.py` | 3 tests for AGNT-01 detail forwarding | VERIFIED | `test_from_result_forwards_error_detail` (L117), `test_from_result_forwards_empty_detail` (L133), `test_action_rejected_in_common_error_recovery` (L145) |
| `tests/plugins/test_plugin_config.py` | 1 test for PLUG-03 vault wiring | VERIFIED | `test_init_event_bus_calls_inject_configs` at line 403 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ztlctl/infrastructure/vault.py` | `src/ztlctl/plugins/manager.py` | `pm.inject_configs(self._settings)` | WIRED | Line 378; called after `discover_and_load()`, before built-in plugin registration |
| `src/ztlctl/mcp/response.py` | `src/ztlctl/services/result.py` | `detail=result.error.detail` in McpError | WIRED | Line 161 in `from_result()` — field forwarded directly from `ServiceError.detail` |
| `src/ztlctl/controllers/*.py` (14 files) | `src/ztlctl/controllers/base.py` | `_dispatch_pre_action` / `_dispatch_post_action` | WIRED | All 63 ServiceResult methods across 14 controllers call both dispatch methods |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PLUG-02 | 07-02, 07-03 | Pre-action hooks with modification and cancellation via pluggy firstresult pattern | SATISFIED | 63 controller methods wired across 14 controllers; rejection path returns `ACTION_REJECTED` ServiceResult; REQUIREMENTS.md marked `[x]` Phase 7 Complete |
| PLUG-03 | 07-01 | Plugin configuration via `[plugins.<name>]` sections passed to plugins during initialization | SATISFIED | `pm.inject_configs(self._settings)` at vault.py:378; REQUIREMENTS.md marked `[x]` Phase 7 Complete |
| AGNT-01 | 07-01 | Structured error responses with machine-readable recovery guidance; every ServiceResult error includes actionable "what to do next" | SATISFIED | `detail=result.error.detail` forwarded in `from_result()`; `ACTION_REJECTED` added to COMMON_ERROR_RECOVERY; REQUIREMENTS.md marked `[x]` Phase 7 Complete |
| AGNT-04 | 07-01 | Progressive tool disclosure — category-based discovery metadata; activation state is advisory | SATISFIED | Advisory comment block in generator.py:92-96; REQUIREMENTS.md description updated to advisory framing, marked `[x]` Phase 7 Complete |

No orphaned requirements — all 4 requirement IDs claimed in plan frontmatter are accounted for and verified in REQUIREMENTS.md traceability table.

### Anti-Patterns Found

None detected across vault.py, response.py, generator.py, or any of the 14 modified controller files. No TODO/FIXME/PLACEHOLDER comments, no empty return stubs, no console.log-only implementations.

### Human Verification Required

None — all phase goals are programmatically verifiable. No UI behavior, real-time interaction, or external service integration involved.

### Gaps Summary

No gaps. All phase goals are achieved:

- PLUG-03: Plugin config injection is wired into the vault initialization path — third-party plugins receive validated TOML config on every vault open.
- AGNT-01: ServiceError.detail is forwarded to McpError.detail in all MCP error responses — agents receive structured error context.
- AGNT-04: Category activation documented as advisory metadata in both generator.py and REQUIREMENTS.md — the design intent is clear.
- PLUG-02: Pre/post-action hooks are wired into all 63 ServiceResult-returning controller methods across 14 controllers — plugins can intercept, modify, or reject any controller action.

All 6 task commits are verified in git history (243a9fb, 0526e4d, fb8a198, 90d30f6, 4bd50a3, 3f089d4). All requirements marked Complete in REQUIREMENTS.md traceability table.

---

_Verified: 2026-03-20T06:00:00Z_
_Verifier: Claude (gsd-verifier)_
