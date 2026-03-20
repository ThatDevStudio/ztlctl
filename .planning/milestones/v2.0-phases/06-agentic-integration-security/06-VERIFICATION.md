---
phase: 06-agentic-integration-security
verified: 2026-03-20T04:51:38Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 6: Agentic Integration & Security Verification Report

**Phase Goal:** Agents can orchestrate ztlctl end-to-end without workarounds, with structured error recovery and progressive tool disclosure, and plugin-contributed workflows are security-constrained
**Verified:** 2026-03-20T04:51:38Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth                                                                                                           | Status     | Evidence                                                                                                                   |
|----|-----------------------------------------------------------------------------------------------------------------|------------|----------------------------------------------------------------------------------------------------------------------------|
| 1  | Every ServiceResult error includes a machine-readable recovery field with actionable next steps                 | VERIFIED   | `ServiceError.recovery: str \| None = None` in `result.py:23`                                                              |
| 2  | McpResponse.from_result() propagates recovery from ServiceError or COMMON_ERROR_RECOVERY fallback              | VERIFIED   | `recovery = result.error.recovery or COMMON_ERROR_RECOVERY.get(result.error.code)` in `response.py:152`                   |
| 3  | All ~35 error codes across all services have recovery entries in COMMON_ERROR_RECOVERY                         | VERIFIED   | 36 entries in COMMON_ERROR_RECOVERY (lines 20-99 of `response.py`); test `test_all_codes_have_recovery` validates coverage |
| 4  | MCP resources expose multi-step orchestration recipes that agents can follow step-by-step                      | VERIFIED   | `recipe_research_capture_impl`, `recipe_review_triage_impl`, `recipe_knowledge_synthesis_impl`, `recipe_index_impl` all in `resources.py:463-608` |
| 5  | MCP tool surface supports category-based discovery — agents can discover categories and their active/core status | VERIFIED   | `discover_categories` action in `_register_core.py:2130`, wired to `DiscoveryController.discover_categories`              |
| 6  | Agents can activate/deactivate non-core categories to manage tool surface                                      | VERIFIED   | `activate_category` and `deactivate_category` actions registered; `_DEFAULT_ACTIVE_CATEGORIES` frozenset in `generator.py:86-88` |
| 7  | Plugin-contributed Copier workflow templates execute with unsafe=False by default, requiring explicit --force-trust to run template hooks | VERIFIED   | `_run_plugin_copy(unsafe=force_trust)` in `workflow.py:368-377`; `_run_copy` always uses unsafe=False (no parameter) |
| 8  | Plugins declare required capabilities and the host validates access at load time with audit logging            | VERIFIED   | `declare_capabilities` hookspec in `hookspecs.py:281`; `_validate_capabilities()` called in `discover_and_load()` at `manager.py:67` |
| 9  | Missing capability declarations trigger a non-fatal log entry, not a hard error                                | VERIFIED   | Missing declarations log at `DEBUG` level; invalid capability names log at `WARNING` level; no exception raised (`manager.py:320-326`) |

**Score:** 9/9 truths verified

### Required Artifacts

| Artifact                                       | Expected                                                          | Status     | Details                                                                                   |
|------------------------------------------------|-------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------|
| `src/ztlctl/services/result.py`                | ServiceError with `recovery: str \| None = None` field            | VERIFIED   | Field present at line 23; frozen Pydantic model; all 30+ existing call sites unaffected   |
| `src/ztlctl/mcp/response.py`                   | McpError with recovery + extended COMMON_ERROR_RECOVERY (36 entries) | VERIFIED   | 36 entries; `ALREADY_OPEN` present; `SEMANTIC_UNAVAILABLE` present                       |
| `src/ztlctl/mcp/resources.py`                  | Three recipe _impl functions + ztlctl://recipes index             | VERIFIED   | All four functions present; registered in `register_resources()` at lines 692-718         |
| `src/ztlctl/mcp/generator.py`                  | Category activation state + get/activate/deactivate/reset         | VERIFIED   | `_DEFAULT_ACTIVE_CATEGORIES` frozenset at line 86; all four functions present             |
| `src/ztlctl/controllers/discovery.py`          | discover_categories handler                                       | VERIFIED   | `DiscoveryController` with `discover_categories`, `activate_category`, `deactivate_category` |
| `src/ztlctl/plugins/hookspecs.py`              | `declare_capabilities` hookspec (not firstresult)                 | VERIFIED   | `@hookspec def declare_capabilities` at line 281; no `firstresult=True`                   |
| `src/ztlctl/plugins/manager.py`                | VALID_CAPABILITIES + `_validate_capabilities` + audit logging     | VERIFIED   | `VALID_CAPABILITIES` at line 34; `_validate_capabilities()` at line 307                  |
| `src/ztlctl/services/workflow.py`              | `force_trust` parameter + `_run_plugin_copy` method               | VERIFIED   | `init_workflow(force_trust=False)` at line 430; `update_workflow(force_trust=False)` at line 503; `_run_plugin_copy(unsafe=force_trust)` at line 354 |

### Key Link Verification

| From                                    | To                                     | Via                                                         | Status  | Details                                                                        |
|-----------------------------------------|----------------------------------------|-------------------------------------------------------------|---------|--------------------------------------------------------------------------------|
| `src/ztlctl/mcp/response.py`            | `src/ztlctl/services/result.py`        | `McpResponse.from_result()` reads `result.error.recovery`  | WIRED   | `result.error.recovery or COMMON_ERROR_RECOVERY.get(result.error.code)` line 152 |
| `src/ztlctl/mcp/resources.py`           | `src/ztlctl/mcp/server.py`             | `register_resources()` called in `create_server()`         | WIRED   | `register_resources(server, vault)` at `server.py:61`                          |
| `src/ztlctl/mcp/generator.py`           | `src/ztlctl/actions/registry.py`       | `get_action_registry().list_actions()`                     | WIRED   | `_get_all_categories()` at line 96; `generate_tools()` at line 374             |
| `src/ztlctl/plugins/manager.py`         | `src/ztlctl/plugins/hookspecs.py`      | `hook.declare_capabilities()` call in `_validate_capabilities` | WIRED   | `declare_fn = getattr(plugin, "declare_capabilities", None)` at line 320       |
| `src/ztlctl/services/workflow.py`       | `src/ztlctl/controllers/workflow.py`   | `force_trust` forwarded from controller to service         | WIRED   | `WorkflowService.init_workflow(vault_root, choices, force_trust=force_trust)` at `workflow.py (controller):33` |
| `src/ztlctl/actions/_register_core.py` | `src/ztlctl/controllers/discovery.py` | ActionDefinitions call `DiscoveryController` methods       | WIRED   | `lambda vault, **kw: DiscoveryController(vault).discover_categories(**kw)` at line 2134 |

### Requirements Coverage

| Requirement | Source Plan | Description                                                                           | Status    | Evidence                                                                            |
|-------------|-------------|---------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------------------|
| AGNT-01     | 06-01       | Structured error responses with machine-readable recovery guidance                    | SATISFIED | `ServiceError.recovery` + 36-entry `COMMON_ERROR_RECOVERY` + `from_result()` wiring |
| AGNT-03     | 06-02       | Agent orchestration recipe resources                                                  | SATISFIED | 3 recipe _impl functions + index registered as MCP resources at `ztlctl://recipes/*` |
| AGNT-04     | 06-02       | Progressive tool disclosure — category-based tool activation                          | SATISFIED | `discover_categories`, `activate_category`, `deactivate_category` ActionDefinitions wired to `DiscoveryController` |
| SECU-01     | 06-03       | Copier --trust=false enforcement for plugin-contributed workflow templates             | SATISFIED | `_run_plugin_copy(unsafe=force_trust)` in `WorkflowService`; built-in `_run_copy()` always uses `unsafe=False` |
| SECU-02     | 06-03       | Plugin capability declarations with audit logging                                     | SATISFIED | `declare_capabilities` hookspec + `_validate_capabilities()` called in `discover_and_load()`; WARNING for invalid capabilities, DEBUG for missing |

No orphaned requirements — AGNT-02 maps to Phase 3 (not Phase 6) per REQUIREMENTS.md.

### Anti-Patterns Found

| File                                          | Line | Pattern    | Severity | Impact                                                    |
|-----------------------------------------------|------|------------|----------|-----------------------------------------------------------|
| `src/ztlctl/plugins/manager.py`               | 323  | stdlib `logging.debug` used instead of structlog for "no capabilities declared" | Info     | Plan 03 specified structlog; implementation uses stdlib logging at DEBUG (not WARNING). Functionally equivalent — tests pass, audit trail exists. Intentional design choice documented in test docstring. |

### Human Verification Required

None. All goal-level behaviors are verifiable programmatically through code inspection.

### Implementation Notes

**SECU-02 logging divergence:** The Plan 03 must_have truth stated "structlog warning" for missing capability declarations. The actual implementation uses stdlib `logging.debug()` (not structlog, not WARNING level). This is an intentional divergence — the test at `tests/plugins/test_manager.py:468` documents "logs no_capabilities_declared **at debug level**" and the code comment says "Advisory in plugin API v2 — missing declaration is not an error." Invalid capability names (unknown values) do produce a `logging.warning()`. The goal — non-blocking audit for missing declarations, warning for invalid declarations — is fully achieved regardless of logger backend.

**COMMON_ERROR_RECOVERY count:** 36 entries verified, exceeding the "at least 30" specification.

**Built-in vs plugin template trust boundary:** `WorkflowService._run_copy()` and `_run_update()` hardcode `unsafe=False` with no parameter. Only `_run_plugin_copy()` accepts `force_trust`. This is the correct security boundary — built-in templates can never be made unsafe by the flag.

### Gaps Summary

No gaps. All 9 observable truths pass full three-level verification (exists, substantive, wired). All 5 requirements are satisfied. All key links are connected. No blocker anti-patterns found.

---

_Verified: 2026-03-20T04:51:38Z_
_Verifier: Claude (gsd-verifier)_
