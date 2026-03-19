---
phase: 03
slug: mcp-surface-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 03 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest && uv run ruff check . && uv run mypy src/` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check . && uv run mypy src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | ACTN-03 | unit | `uv run pytest tests/test_mcp_generator.py -x -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | ACTN-03 | unit | `uv run pytest tests/test_mcp_responses.py -x -q` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | PLUG-04 | integration | `uv run pytest tests/test_mcp_parity.py -x -q` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | AGNT-02 | unit | `uv run pytest tests/test_token_budget.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_mcp_generator.py` — stubs for ACTN-03 generator tests
- [ ] `tests/test_mcp_responses.py` — stubs for Pydantic MCP response model tests
- [ ] `tests/test_mcp_parity.py` — stubs for PLUG-04 CLI/MCP parity verification
- [ ] `tests/test_token_budget.py` — stubs for AGNT-02 token budget tests

*Existing infrastructure covers test framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `ztlctl serve` starts and exposes tools | ACTN-03 | Requires MCP package + running server | Start server, connect client, list tools |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
