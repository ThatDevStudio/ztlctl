---
phase: 19-methodology-guidance-and-polaris
verified: 2026-03-21T20:00:00Z
status: passed
score: 7/7 must-haves verified
re_verification: false
---

# Phase 19: Methodology Guidance and Polaris — Verification Report

**Phase Goal:** Prose-as-title conventions are documented and checked by the integrity scanner, and a persistent polaris priorities layer is accessible to agents and users
**Verified:** 2026-03-21T20:00:00Z
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A new vault created with `ztlctl init` contains `garden/groves/polaris.md` with starter priorities template | VERIFIED | `init.py` step 5b renders `polaris.md.j2` and writes `garden/groves/polaris.md`; `files_created.append("garden/groves/polaris.md")` confirmed at line 415 |
| 2 | An MCP agent reading `ztlctl://polaris` receives the polaris document content | VERIFIED | `polaris_impl` function at `resources.py:110`, `ztlctl://polaris` registered at line 705, catalog entry at line 33 |
| 3 | ContextAssembler includes polaris content in Layer 1 (operational state) with 500-token budget | VERIFIED | `context.py:126-141`: reads `garden/groves/polaris.md`, truncates at 500 tokens, sets `layers["polaris"]`; `AgentContextLayers.polaris: str | None` in `contracts.py:243` |
| 4 | Prose-as-title convention is documented in `methodology.md.j2` with examples and research-partner tone | VERIFIED | `### Prose-as-Title Convention` section at line 59 with 4-row table; "Your titles ARE your search index" guidance present |
| 5 | CheckService flags notes with short or generic titles at info severity under CAT_STRUCTURAL | VERIFIED | `_GENERIC_TITLE_PATTERNS` frozenset at `check.py:55`; `_check_structural_validation` appends `SEVERITY_INFO` issues for `word_count <= 3` or generic matches at line 817 |
| 6 | Garden backlog MCP resource includes title improvement candidates alongside stale seeds and orphans | VERIFIED | `garden_backlog_impl` imports `CheckService, CAT_STRUCTURAL, SEVERITY_INFO` at `resources.py:186`, filters for "Title quality" messages, returns `title_improvement_candidates` at line 207 |
| 7 | `check_alignment` action accepts a decision description and returns structured polaris context | VERIFIED | `CheckService.check_alignment` at `check.py:348`; `CheckController.check_alignment` at `controllers/check.py:60`; ActionDefinition registered in `_check.py:96` with `cli_name="alignment"` |

**Score:** 7/7 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/ztlctl/templates/self/polaris.md.j2` | Jinja2 template with Mission, Current Priorities, Decision Principles | VERIFIED | All 3 sections present at lines 11, 15, 21 |
| `src/ztlctl/mcp/resources.py` | `polaris_impl` function and `ztlctl://polaris` resource registration | VERIFIED | `polaris_impl` at line 110; resource at line 705; catalog entry at line 33 |
| `src/ztlctl/services/context.py` | Polaris content in Layer 1 assembly | VERIFIED | `layers["polaris"]` with 500-token budget at lines 126-141 |
| `src/ztlctl/templates/self/methodology.md.j2` | Prose-as-title guidance section | VERIFIED | `### Prose-as-Title Convention` with table at line 59 |
| `src/ztlctl/services/check.py` | Title quality check in `_check_structural_validation` | VERIFIED | `_GENERIC_TITLE_PATTERNS` at line 55; check logic at line 817 |
| `src/ztlctl/services/check.py` | `check_alignment` service method | VERIFIED | `def check_alignment` at line 348; returns `{aligned, relevant_priorities, reasoning, polaris_exists}` |
| `src/ztlctl/controllers/check.py` | `check_alignment` controller method | VERIFIED | Delegates via `_run_action` at line 60 |
| `src/ztlctl/actions/_check.py` | `check_alignment` ActionDefinition registration | VERIFIED | Registered at line 96 under `check` category with `cli_name="alignment"` |
| `src/ztlctl/services/contracts.py` | `polaris: str \| None` in `AgentContextLayers` | VERIFIED | Field at line 243 |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/ztlctl/services/init.py` | `src/ztlctl/templates/self/polaris.md.j2` | Jinja2 render in step 5b | WIRED | `polaris_env.get_template("polaris.md.j2").render(...)` at `init.py:409` |
| `src/ztlctl/mcp/resources.py` | `garden/groves/polaris.md` | file read from vault root | WIRED | `vault.root / "garden" / "groves" / "polaris.md"` at `resources.py:112` |
| `src/ztlctl/services/context.py` | `garden/groves/polaris.md` | file read with 500-token budget in Layer 1 | WIRED | `self._vault.root / "garden" / "groves" / "polaris.md"` at `context.py:126` |
| `src/ztlctl/services/check.py` | `CAT_STRUCTURAL` | title quality issues appended to structural validation | WIRED | `"category": CAT_STRUCTURAL` at `check.py:828`; `SEVERITY_INFO` at same block |
| `src/ztlctl/mcp/resources.py` | `src/ztlctl/services/check.py` | `garden_backlog_impl` reads check results for title candidates | WIRED | `CheckService(vault).check(min_severity="info")` at `resources.py:186`; filters `"Title quality"` at line 195 |
| `src/ztlctl/actions/_check.py` | `src/ztlctl/controllers/check.py` | ActionDefinition handler lambda | WIRED | `lambda vault, **kw: CheckController(vault).check_alignment(**kw)` at `_check.py:109` |
| `src/ztlctl/controllers/check.py` | `src/ztlctl/services/check.py` | controller delegates via `_run_action` | WIRED | `CheckService(self._vault).check_alignment(**kw)` at `controllers/check.py:67` |
| `src/ztlctl/services/check.py` | `garden/groves/polaris.md` | reads polaris file to extract priorities | WIRED | `self._vault.root / "garden" / "groves" / "polaris.md"` at `check.py:355` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| POLR-01 | 19-01 | `garden/groves/polaris.md` scaffolded during `ztlctl init` with starter template | SATISFIED | `init.py` step 5b renders template and writes file; `files_created` includes `"garden/groves/polaris.md"` |
| POLR-02 | 19-01 | MCP resource `ztlctl://polaris` exposes polaris document content | SATISFIED | `polaris_impl` registered as `ztlctl://polaris` in `resources.py` |
| POLR-03 | 19-01 | ContextAssembler integrates polaris into Layer 1 with token budgeting | SATISFIED | `context.py` Layer 1 block with 500-token budget; `AgentContextLayers.polaris` in contracts |
| POLR-04 | 19-03 | `check_alignment` action returns structured polaris context for agent evaluation | SATISFIED | Service + controller + ActionDefinition all present; result shape `{aligned, relevant_priorities, reasoning}` confirmed |
| METH-01 | 19-02 | Prose-as-title convention documented in `methodology.md.j2` | SATISFIED | `### Prose-as-Title Convention` with table and "Your titles ARE your search index" guidance |
| METH-02 | 19-02 | Title quality check in CheckService at `CAT_STRUCTURAL`, info severity | SATISFIED | `_GENERIC_TITLE_PATTERNS` frozenset; `_check_structural_validation` appends `SEVERITY_INFO` issues for short/generic titles |
| METH-03 | 19-02 | Garden backlog resource includes title improvement candidates | SATISFIED | `garden_backlog_impl` returns `title_improvement_candidates` sourced from CheckService at info severity |

No orphaned requirements — all 7 IDs (POLR-01 through POLR-04, METH-01 through METH-03) appear in plan frontmatter and are satisfied. REQUIREMENTS.md marks all 7 complete.

---

### Anti-Patterns Found

No anti-patterns detected. Scan of all 6 modified source files found zero TODO/FIXME/placeholder comments, no stub return values, and no unconnected state.

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| — | — | None found | — | — |

---

### Human Verification Required

None — all behaviors are verifiable programmatically through grep and test execution.

---

### Test Results

210 tests across 5 test files passed (0 failures, 0 errors):

- `tests/services/test_check.py` — includes `TestTitleQualityCheck` (8 tests) and `TestCheckAlignment` (8 tests)
- `tests/services/test_context.py` — 4 polaris-specific tests (present, absent, truncation, token counting)
- `tests/services/test_init.py` — polaris scaffolding tests; `files_created` includes `garden/groves/polaris.md`
- `tests/mcp/test_resources.py` — `polaris_impl` (exists/not-exists), `resource_catalog` includes `ztlctl://polaris`, `TestGardenBacklogTitleCandidates` (7 tests)
- `tests/actions/test_core_registrations.py` — `check_alignment` in check category exact-names set

---

### Commit Verification

All 6 phase commits verified present in git history:

| Commit | Plan | Description |
|--------|------|-------------|
| `cd72d4c` | 19-01 | feat(19-01): polaris template, init scaffolding, and MCP resource |
| `2a7d4b1` | 19-01 | feat(19-01): add polaris to ContextAssembler Layer 1 with 500-token budget |
| `f091703` | 19-02 | feat(19-02): add prose-as-title methodology section and title quality check |
| `373a40f` | 19-02 | feat(19-02): surface title improvement candidates in garden backlog resource |
| `d9fca5f` | 19-03 | test(19-03): add failing tests for check_alignment service and action |
| `4ff3d4a` | 19-03 | feat(19-03): implement check_alignment action for polaris decision checking |

---

### Summary

Phase 19 achieved its goal completely. All 7 requirements are satisfied with substantive, wired implementations:

- **Polaris layer** (POLR-01 through POLR-04): The polaris document is scaffolded on vault init, exposed as an MCP resource (`ztlctl://polaris`), integrated into the ContextAssembler Layer 1 with a 500-token budget, and queryable by agents via the `check_alignment` action that returns structured `{aligned, relevant_priorities, reasoning}` data.

- **Methodology guidance** (METH-01 through METH-03): The `### Prose-as-Title Convention` section with a 4-row example table is in the methodology template (research-partner tone). CheckService's `_check_structural_validation` flags notes with word count <= 3 or generic names at `SEVERITY_INFO` under `CAT_STRUCTURAL`, never blocking creation. The garden backlog MCP resource surfaces these candidates via `title_improvement_candidates` alongside existing stale seeds and orphans.

No stubs, no unconnected code paths, no regressions.

---

_Verified: 2026-03-21T20:00:00Z_
_Verifier: Claude (gsd-verifier)_
