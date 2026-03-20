---
phase: 07
slug: plugin-agentic-wiring-fixes
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/controllers/ tests/plugins/test_plugin_config.py tests/mcp/test_response.py -x -q` |
| **Full suite command** | `uv run pytest` |
| **Estimated runtime** | ~15 seconds (quick), ~60 seconds (full) |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/controllers/ tests/plugins/test_plugin_config.py tests/mcp/test_response.py -x -q`
- **After every plan wave:** Run `uv run pytest`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | PLUG-02 | integration | `uv run pytest tests/controllers/ -x -q` | ✅ | ⬜ pending |
| 07-01-02 | 01 | 1 | PLUG-02 | integration | `uv run pytest tests/controllers/ -x -q` | ✅ | ⬜ pending |
| 07-02-01 | 02 | 1 | PLUG-03 | integration | `uv run pytest tests/plugins/test_plugin_config.py -x -q` | ✅ | ⬜ pending |
| 07-02-02 | 02 | 1 | AGNT-01 | unit | `uv run pytest tests/mcp/test_response.py -x -q` | ✅ | ⬜ pending |
| 07-02-03 | 02 | 1 | AGNT-04 | unit | `uv run pytest tests/mcp/test_generator.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Test files already exist for controllers, plugins, and MCP layers.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Plugin pre_action rejection aborts CLI command | PLUG-02 | Requires live CLI invocation with a rejection-returning plugin | Install test plugin, run `ztlctl create note "test"`, verify rejection message |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
