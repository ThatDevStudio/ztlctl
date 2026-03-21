---
phase: 16
slug: plugin-bridge-and-action-executor
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 16 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 16-01-01 | 01 | 1 | ARCH-05 | unit | `uv run pytest tests/plugins/test_event_bus.py -k bridge` | ✅ | ⬜ pending |
| 16-01-02 | 01 | 1 | ARCH-06 | unit | `uv run pytest tests/controllers/ -k run_action` | ❌ W0 | ⬜ pending |
| 16-02-01 | 02 | 2 | ARCH-09 | unit | `uv run pytest tests/ -k garden_seed` | ❌ W0 | ⬜ pending |
| 16-02-02 | 02 | 2 | DEBT-04 | integration | `uv run pytest tests/mcp/ -k shutdown` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/controllers/test_action_executor.py` — tests for generic `_run_action` executor
- [ ] `tests/mcp/test_shutdown.py` — MCP graceful shutdown test

*Existing bridge tests in test_event_bus.py cover bridge reversal; update assertions rather than add new files.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MCP client disconnect | DEBT-04 | Requires actual MCP client connection/disconnect | Start `ztlctl serve`, connect MCP client, disconnect, verify no dangling asyncio tasks |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
