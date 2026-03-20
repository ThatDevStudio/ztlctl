---
phase: 05
slug: plugin-formalization
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 05 — Validation Strategy

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
| 05-01-01 | 01 | 1 | PLUG-01 | unit | `uv run pytest tests/plugins/test_api_version.py -x -q` | ❌ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | PLUG-02 | unit | `uv run pytest tests/plugins/test_pre_action_hooks.py -x -q` | ❌ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | PLUG-03 | unit | `uv run pytest tests/plugins/test_plugin_config.py -x -q` | ❌ W0 | ⬜ pending |
| 05-02-01 | 02 | 2 | PLUG-05, PLUG-06 | integration | `uv run pytest tests/plugins/test_custom_note_types.py -x -q` | ❌ W0 | ⬜ pending |
| 05-02-02 | 02 | 2 | PLUG-07 | unit | `uv run pytest tests/plugins/test_marketplace_metadata.py -x -q` | ❌ W0 | ⬜ pending |
| 05-03-01 | 03 | 3 | PLUG-01 | integration | `uv run pytest tests/plugins/test_git_plugin.py tests/plugins/test_reweave_plugin.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/plugins/test_api_version.py` — stubs for PLUG-01 API versioning tests
- [ ] `tests/plugins/test_pre_action_hooks.py` — stubs for PLUG-02 pre-action hook tests
- [ ] `tests/plugins/test_plugin_config.py` — stubs for PLUG-03 config validation tests
- [ ] `tests/plugins/test_custom_note_types.py` — stubs for PLUG-05/PLUG-06 custom note type tests
- [ ] `tests/plugins/test_marketplace_metadata.py` — stubs for PLUG-07 metadata tests

*Existing test infrastructure covers framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Plugin deprecation warnings display correctly | PLUG-01 | Visual formatting check | Load a plugin with old API version, verify warning text |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
