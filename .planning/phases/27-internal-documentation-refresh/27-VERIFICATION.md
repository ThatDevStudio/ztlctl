---
phase: 27-internal-documentation-refresh
verified: 2026-03-21T00:00:00Z
status: gaps_found
score: 5/6 must-haves verified
re_verification: false
gaps:
  - truth: "CLAUDE.md architecture section lists all current services, controllers, and action counts"
    status: partial
    reason: "CLAUDE.md correctly says 16 services (matching source), but DESIGN.md Section 1 architecture diagram says '15 services' on line 47 — minor internal inconsistency between the two internal docs"
    artifacts:
      - path: "DESIGN.md"
        issue: "Line 47 of architecture diagram reads '15 services' — actual source has 16 and CLAUDE.md correctly says 16"
    missing:
      - "Update DESIGN.md Section 1 architecture diagram line 47 from '15 services' to '16 services'"
      - "Optionally add the missing services (UpdateService, ExportService, InitService, WorkflowService, UpgradeService) to the diagram's service enumeration box"
---

# Phase 27: Internal Documentation Refresh Verification Report

**Phase Goal:** CLAUDE.md, DESIGN.md, and README.md accurately describe the v3.0 system — developers and contributors work from current information
**Verified:** 2026-03-21T00:00:00Z
**Status:** gaps_found (1 minor inconsistency)
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | CLAUDE.md architecture section lists all current services, controllers, and action counts | ⚠️ PARTIAL | CLAUDE.md correctly says 16 services; DESIGN.md diagram says 15 (stale) |
| 2 | CLAUDE.md describes feature-local action registration pattern and centralized PluginManager | ✓ VERIFIED | Lines 250–256 of CLAUDE.md — full prose description with `get_plugin_manager()` in `plugins/runtime.py` |
| 3 | README.md features list includes session recall, polaris, contradiction detection, and media ingestion | ✓ VERIFIED | Lines 85–89, 142–145 of README.md — all four features present with doc links |
| 4 | README.md command table is complete and accurate for v3.0 | ✓ VERIFIED | Lines 73–76 show `recall-topic` and `check contradictions` examples; architecture tree updated |
| 5 | DESIGN.md captures the v3.0 reliable event model with WAL drain and service-only post_action | ✓ VERIFIED | Section 15 lines 1122–1146, decision D-13 at line 1677 |
| 6 | DESIGN.md describes the generic action executor, feature-local registration, recall/contradiction/ingestion design choices | ✓ VERIFIED | D-14/D-15 in Decision Log; Sections 19–22 added for recall, contradiction, ingestion, polaris |

**Score:** 5/6 truths verified (1 partial — minor count inconsistency in DESIGN.md diagram)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `CLAUDE.md` | Updated architecture section with v3.0 service/controller/action inventory | ✓ VERIFIED | Lines 219–256: 16 services listed, 17 controllers listed, 73 actions tabulated across 9 modules |
| `DESIGN.md` | v3.0 architectural decisions appended/updated | ✓ VERIFIED | Sections 1, 10, 15, 16 updated; Sections 19–22 added; Decision Log extended D-13 through D-21 |
| `README.md` | Updated features list and command examples for v3.0 | ✓ VERIFIED | All v3.0 features present; doc table updated; architecture tree updated; Quick Start examples added |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `CLAUDE.md` | `src/ztlctl/services/` | service class inventory | ✓ VERIFIED | 16 services match `grep "^class " services/*.py` — CheckService, ContradictionService, CreateService, ExportService, GraphService, IngestService, InitService, QueryService, RecallService, ReweaveService, SessionService, TranscriptionService, UpdateService, UpgradeService, VectorService, WorkflowService |
| `CLAUDE.md` | `src/ztlctl/controllers/` | controller class inventory | ✓ VERIFIED | 17 concrete controllers match source (excluding BaseController) |
| `CLAUDE.md` | `src/ztlctl/actions/` | 73 ActionDefinitions across 9 modules | ✓ VERIFIED | `grep -c "ActionDefinition(" actions/` returns 73 |
| `CLAUDE.md` | `src/ztlctl/plugins/runtime.py` | `get_plugin_manager()` factory | ✓ VERIFIED | `runtime.py` exports `get_plugin_manager()` as single construction point |
| `DESIGN.md` | `src/ztlctl/controllers/base.py` | `_run_action` executor pattern | ✓ VERIFIED | DESIGN.md lines 44, 77, 985, 1678 reference `_run_action`; source `controllers/base.py` exists |
| `DESIGN.md` | `src/ztlctl/actions/` | feature-local registration | ✓ VERIFIED | DESIGN.md line 1679 (D-15) documents decomposition; `actions/` directory exists with 9 `_*.py` modules |
| `DESIGN.md` | `src/ztlctl/services/recall.py` | recall service design | ✓ VERIFIED | Section 19 documents `RecallService` with three query modes; `services/recall.py` exists |
| `README.md` | `docs/` | documentation links | ✓ VERIFIED | Lines 142–146 link to session-recall.md, polaris.md, contradiction-detection.md, media-ingestion.md |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| IDOC-01 | 27-01 | CLAUDE.md architecture section updated with v3.0 services (15 services per REQUIREMENTS.md, actual 16), 17 controllers, 73+ actions, feature-local registration, centralized PM | ✓ SATISFIED | CLAUDE.md lines 219–256 — all required content present; CLAUDE.md correctly states 16 (more accurate than REQUIREMENTS.md's "15") |
| IDOC-02 | 27-02 | DESIGN.md refreshed with v3.0 architectural decisions (event model, action executor, plugin runtime, recall, contradiction, ingestion) | ✓ SATISFIED | All 6 decision categories documented: event model (Section 15, D-13), action executor (line 985, D-14), feature-local registration (D-15), bridge reversal (D-16), recall (Section 19, D-21), contradiction (Section 20, D-18), ingestion (Section 21, D-19) |
| IDOC-03 | 27-01 | README.md feature list and command examples updated for v3.0 (session recall, polaris, contradiction, ingestion commands) | ✓ SATISFIED | README.md lines 73–89, 142–145, 165–173 — all four features present with commands, links, and architecture reference |

All 3 requirements SATISFIED.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `DESIGN.md` | 47 | Architecture diagram says "15 services" | ⚠️ Warning | Count inconsistency: CLAUDE.md says 16, actual source has 16; diagram is stale |
| `DESIGN.md` | 47–52 | Service Layer box lists only 11 services (missing UpdateService, ExportService, InitService, WorkflowService, UpgradeService) | ℹ️ Info | Diagram is illustrative (truncated), but combined with wrong count claim, could mislead developers |

No blocker anti-patterns. The DESIGN.md count inconsistency is a minor documentation stale value — the narrative sections (19–22), decision log, and CLAUDE.md all correctly reflect v3.0.

### Human Verification Required

No items require human testing. All verifications are programmatic:
- All key terms are present in the correct files
- All commit hashes (356bf99, 1d2427c, 643807c, fe2d9c6) verified in git log
- Service/controller/action counts verified against source code

### Gaps Summary

One minor gap: DESIGN.md Section 1 architecture diagram on line 47 still reads "Service Layer (15 services, Section 10)" but actual source has 16 concrete service classes, and CLAUDE.md (the primary developer reference) correctly says 16. The DESIGN.md diagram also only enumerates 11 of the 16 services in its listing box (omitting UpdateService, ExportService, InitService, WorkflowService, UpgradeService).

This is a cosmetic inconsistency within DESIGN.md only — it does not affect CLAUDE.md or README.md accuracy. The DESIGN.md narrative sections (19–22) and decision log all accurately reflect v3.0 architecture. The diagram count mismatch is low-severity but technically represents a false claim in the document.

**Root cause**: The execution agent updated CLAUDE.md and then correctly discovered the true count is 16 (not 15 as in PROJECT.md context snapshot), but the DESIGN.md architecture diagram was not updated to match.

**Fix required**: Single line change in DESIGN.md line 47: `(15 services` → `(16 services`.

---

## Source Count Verification

For full transparency, the counts were independently verified:

**Services (16):** CheckService, ContradictionService, CreateService, ExportService, GraphService, IngestService, InitService, QueryService, RecallService, ReweaveService, SessionService, TranscriptionService, UpdateService, UpgradeService, VectorService, WorkflowService

**Controllers (17, excluding BaseController):** CheckController, ContradictionController, CreateController, DiscoveryController, DocsController, ExportController, GraphController, IngestController, InitController, QueryController, RecallController, ReweaveController, SessionController, UpdateController, UpgradeController, VectorController, WorkflowController

**Actions (73):** Verified by `grep -c "ActionDefinition(" src/ztlctl/actions/` across all 9 `_*.py` modules

---

_Verified: 2026-03-21T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
