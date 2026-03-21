---
phase: 12
slug: doc-search-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing) |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/services/test_docs.py tests/controllers/test_docs.py -q` |
| **Full suite command** | `uv run pytest && uv run ruff check . && uv run mypy src/` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick test command
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | AGNT-03 | unit | `uv run pytest tests/services/test_docs.py -q` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 2 | AGNT-03 | integration | `uv run ztlctl docs search --help` | ❌ W0 | ⬜ pending |
| 12-02-02 | 02 | 2 | AGNT-04 | unit | `uv run pytest tests/mcp/test_docs_resources.py -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_docs.py` — test stubs for _docs_search_impl
- [ ] Verify `uv run pytest` still passes before any implementation

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Rich table renders cleanly | AGNT-03 | Visual output check | Run `uv run ztlctl docs "session"` and verify table format |
| MCP resource queryable by agent | AGNT-04 | Requires MCP client | Start `ztlctl serve`, query `ztlctl://docs/search` via MCP client |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
