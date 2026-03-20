---
phase: 06
slug: agentic-integration-security
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest && uv run ruff check . && uv run mypy src/` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check . && uv run mypy src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | AGNT-01 | unit | `uv run pytest tests/services/test_error_recovery.py -x -q` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | AGNT-03 | unit | `uv run pytest tests/mcp/test_recipes.py -x -q` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | AGNT-04 | unit | `uv run pytest tests/mcp/test_progressive_disclosure.py -x -q` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | SECU-01, SECU-02 | unit | `uv run pytest tests/plugins/test_security.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/services/test_error_recovery.py` — stubs for AGNT-01 recovery field tests
- [ ] `tests/mcp/test_recipes.py` — stubs for AGNT-03 orchestration recipe tests
- [ ] `tests/mcp/test_progressive_disclosure.py` — stubs for AGNT-04 category activation tests
- [ ] `tests/plugins/test_security.py` — stubs for SECU-01/SECU-02 security tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Agent follows recipe end-to-end | AGNT-03 | Requires MCP client + LLM | Connect Claude, invoke recipe resource, verify it follows steps |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
