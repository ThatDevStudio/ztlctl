---
phase: 15
slug: event-model-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 15 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` ([tool.pytest.ini_options]) |
| **Quick run command** | `uv run pytest tests/ -x -q --timeout=30` |
| **Full suite command** | `uv run pytest tests/ --timeout=60` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q --timeout=30`
- **After every plan wave:** Run `uv run pytest tests/ --timeout=60`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 15-01-01 | 01 | 1 | ARCH-01 | integration | `uv run pytest tests/plugins/test_event_bus.py -k drain` | ❌ W0 | ⬜ pending |
| 15-01-02 | 01 | 1 | ARCH-02 | integration | `uv run pytest tests/plugins/test_event_bus.py -k startup` | ❌ W0 | ⬜ pending |
| 15-02-01 | 02 | 1 | ARCH-03 | unit | `uv run pytest tests/controllers/ -k post_action` | ✅ | ⬜ pending |
| 15-02-02 | 02 | 1 | ARCH-04 | unit | `uv run pytest tests/plugins/test_event_bus.py -k action_event` | ❌ W0 | ⬜ pending |
| 15-03-01 | 03 | 2 | DEBT-02 | unit | `uv run pytest tests/config/test_models.py -k eventbus` | ❌ W0 | ⬜ pending |
| 15-03-02 | 03 | 2 | DEBT-03 | integration | `uv run pytest tests/plugins/test_event_bus.py -k dead_letter` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/plugins/test_event_bus.py` — add drain, startup recovery, ActionEvent, and dead-letter test cases
- [ ] `tests/config/test_models.py` — add EventBusConfig test cases

*Existing test infrastructure covers framework and fixtures. Only new test cases needed for new behaviors.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Slow plugin teardown | ARCH-01 | Requires actual slow plugin execution | Create local plugin with `time.sleep(2)` in `post_action`, run `ztlctl create note`, verify no pending WAL rows after exit |
| Startup recovery after crash | ARCH-02 | Requires simulating interrupted process | Insert pending WAL row, start CLI command, verify row drained before command executes |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
