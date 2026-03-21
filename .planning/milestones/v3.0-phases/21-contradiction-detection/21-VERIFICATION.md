---
phase: 21-contradiction-detection
verified: 2026-03-21T20:09:00Z
status: passed
score: 9/9 must-haves verified
re_verification: false
---

# Phase 21: Contradiction Detection Verification Report

**Phase Goal:** The vault can surface notes that likely contradict each other, record confirmed contradictions as graph edges, and expose them in an agent review resource
**Verified:** 2026-03-21T20:09:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | `ContradictionService.find_candidates` returns scored pairs of notes that may contradict | VERIFIED | `src/ztlctl/services/contradiction.py` lines 121-268; returns `{"candidates": [...], "count": N}` |
| 2  | Candidate pairs scoped by shared tags and high cosine similarity (>0.85) | VERIFIED | Lines 229-231: tag intersection check; lines 224-226: `cosine_sim < similarity_threshold` guard |
| 3  | Heuristic scoring: cosine 40%, negation 30%, key_points 30% | VERIFIED | `_COSINE_WEIGHT=0.4`, `_NEGATION_WEIGHT=0.3`, `_KEYPOINTS_WEIGHT=0.3` constants at lines 26-27; `_score_pair` computes each component |
| 4  | Results capped at 20 pairs, sorted by score descending | VERIFIED | Lines 261-262: `candidates.sort(key=lambda c: c["score"], reverse=True)` then `candidates[:max_pairs]` |
| 5  | Running check with `CAT_SEMANTIC` reports contradiction candidates as `CheckIssue`s | VERIFIED | `check.py` line 53: `CAT_SEMANTIC = "semantic_analysis"`; lines 112-113: `_check_semantic()` wired into `check()` with `trace_span`; returns `SEVERITY_INFO` dicts |
| 6  | `confirm_contradiction` records bidirectional `contradicts` edges in the graph | VERIFIED | `contradiction.py` lines 323-345: two `insert_edge` calls with `edge_type="contradicts"`, `source_layer="user"`, `check_duplicate=True` |
| 7  | MCP resource `ztlctl://review/contradictions` returns JSON array of scored candidate pairs | VERIFIED | `resources.py` line 78: catalog entry; line 702: `contradictions_review_impl`; lines 848-853: `@server.resource("ztlctl://review/contradictions")` registration |
| 8  | `check_contradictions` registered in ActionRegistry under analysis category | VERIFIED | `_check.py` lines 131-162: `ActionDefinition(name="check_contradictions", category="analysis")`; handler delegates to `ContradictionController.check_contradictions` |
| 9  | Contradiction check gracefully skips if no vector index exists | VERIFIED | `contradiction.py` lines 154-161: `if not vec.is_available()` returns `ok=True` with empty candidates; `check.py` line 965-966: `if not result.ok: return []` |

**Score:** 9/9 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/services/contradiction.py` | ContradictionService with `find_candidates` and `confirm_contradiction` | VERIFIED | 466 lines; exports `ContradictionService`; both methods fully implemented |
| `src/ztlctl/controllers/contradiction.py` | ContradictionController wrapping service via `_run_action` | VERIFIED | 51 lines; `check_contradictions` and `confirm_contradiction` both delegate through `_run_action` |
| `src/ztlctl/services/check.py` | `CAT_SEMANTIC` constant and `_check_semantic` method | VERIFIED | `CAT_SEMANTIC = "semantic_analysis"` at line 53; `_check_semantic()` at line 954; wired into `check()` at line 113 |
| `src/ztlctl/actions/_check.py` | `check_contradictions` and `confirm_contradiction` ActionDefinitions | VERIFIED | Both registered in `_register_check_actions()`; correct category, side_effects, CLI names, and MCP metadata |
| `src/ztlctl/mcp/resources.py` | `ztlctl://review/contradictions` resource | VERIFIED | Catalog entry at line 78; `contradictions_review_impl` at line 702; registered at line 848 |
| `tests/services/test_contradiction.py` | Unit tests for candidate discovery and scoring | VERIFIED | 392 lines, 13 test functions; all pass |
| `tests/controllers/test_contradiction.py` | Controller delegation tests | VERIFIED | 108 lines, 7 test functions; all pass |
| `tests/test_contradiction_integration.py` | Integration tests for CheckService `CAT_SEMANTIC` and `confirm_contradiction` | VERIFIED | 317 lines, 9 test functions; all pass |
| `tests/test_contradiction_resource.py` | MCP resource impl tests | VERIFIED | 185 lines, 6 test functions; all pass |
| `tests/test_contradiction_actions.py` | ActionRegistry registration tests | VERIFIED | 237 lines, 19 test functions; all pass |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `services/contradiction.py` | `services/vector.py` | Lazy `VectorService` import inside `find_candidates`; `vec.search_similar(query_text, limit=20)` | WIRED | Line 151: `from ztlctl.services.vector import VectorService`; line 209: `similar = vec.search_similar(...)` |
| `services/contradiction.py` | `schema.py` (node_tags, nodes) | `select(node_tags.c.node_id, node_tags.c.tag)` for tag overlap | WIRED | Lines 16-17: `from ztlctl.infrastructure.database.schema import node_tags, nodes`; lines 191-194: tag query |
| `controllers/contradiction.py` | `services/contradiction.py` | `ContradictionService(self._vault)` in controller methods | WIRED | Lines 23, 41: lazy imports; lines 31, 45: service instantiated and called |
| `services/check.py` | `services/contradiction.py` | `ContradictionService.find_candidates` called in `_check_semantic` | WIRED | `check.py` line 960: lazy import; line 962-963: `svc.find_candidates()` |
| `services/contradiction.py` | `VaultTransaction.insert_edge` | `confirm_contradiction` records bidirectional edges | WIRED | Lines 322-345: `with self._vault.transaction() as txn`; two `txn.insert_edge(..., "contradicts", ...)` calls |
| `mcp/resources.py` | `services/contradiction.py` | `contradictions_review_impl` calls `find_candidates` | WIRED | Line 704: lazy import; line 706: `ContradictionService(vault).find_candidates()` |
| `actions/_check.py` | `controllers/contradiction.py` | ActionDefinition handlers delegate to `ContradictionController` | WIRED | Lines 129, 152, 187: `ContradictionController(vault).check_contradictions(**kw)` and `.confirm_contradiction(**kw)` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CNTR-01 | 21-01 | Candidate pair discovery — topic-scoped, high-similarity, decision conflicts | SATISFIED | `find_candidates` filters by `cosine_sim >= 0.85` and shared tags; returns scored pairs |
| CNTR-02 | 21-01 | Heuristic scoring using negation patterns and key_points comparison | SATISFIED | `_score_pair`: cosine 40%, negation density 30% (8 keyword patterns, cap 5), key_points divergence 30% |
| CNTR-03 | 21-02 | `CAT_SEMANTIC` check category in CheckService reports contradiction candidates | SATISFIED | `CAT_SEMANTIC = "semantic_analysis"` constant; `_check_semantic()` wired into `check()`; returns `SEVERITY_INFO` issues |
| CNTR-04 | 21-02 | Confirmed contradictions recorded as `contradicts` edges in the graph | SATISFIED | `confirm_contradiction` inserts A→B and B→A edges with `edge_type="contradicts"`, `check_duplicate=True` |
| CNTR-05 | 21-02 | MCP resource `ztlctl://review/contradictions` surfaces contradiction pairs | SATISFIED | Resource in `_RESOURCE_CATALOG`, `contradictions_review_impl` function, registered in `register_resources()` |
| CNTR-06 | 21-02 | `check_contradictions` action registered in ActionRegistry (category: analysis) | SATISFIED | Both `check_contradictions` and `confirm_contradiction` registered under `"analysis"` category |

All 6 requirements satisfied. No orphaned requirements detected.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `controllers/contradiction.py` | 39 | Stale docstring: "stub — wired in Plan 02" — implementation is complete | Info | Cosmetic only; implementation correctly calls `ContradictionService.confirm_contradiction` |

No blocking stubs. The stale docstring is cosmetic and does not affect behavior.

---

### Human Verification Required

None. All phase functionality is verifiable programmatically via existing tests and grep-based code analysis.

---

### Test Suite Summary

54 contradiction-related tests pass across 5 test files:
- `tests/services/test_contradiction.py`: 13 tests (TDD service unit tests)
- `tests/controllers/test_contradiction.py`: 7 tests (controller delegation + plugin rejection)
- `tests/test_contradiction_integration.py`: 9 tests (CheckService CAT_SEMANTIC + confirm edge insertion)
- `tests/test_contradiction_resource.py`: 6 tests (MCP resource impl + catalog registration)
- `tests/test_contradiction_actions.py`: 19 tests (ActionRegistry registration for both actions)

Ruff: clean on all 5 implementation files.
Mypy: clean on `services/contradiction.py` and `controllers/contradiction.py`.

---

### Gaps Summary

No gaps. All 9 observable truths verified, all 10 artifacts substantive and wired, all 7 key links confirmed, all 6 requirements satisfied. Phase goal is fully achieved.

---

_Verified: 2026-03-21T20:09:00Z_
_Verifier: Claude (gsd-verifier)_
