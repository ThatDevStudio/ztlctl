---
phase: 1
slug: core-hardening
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy src/` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check . && uv run ruff format --check . && uv run mypy src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | HARD-01 | unit | `uv run pytest tests/ -x -q` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-02 | unit | `uv run pytest tests/ -x -q` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-05 | unit | `uv run pytest tests/ -x -q` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-06 | unit+perf | `uv run pytest tests/ -x -q` | ✅ | ⬜ pending |
| TBD | TBD | TBD | HARD-08 | integration | `uv run pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| TBD | TBD | TBD | HARD-09 | unit | `uv run pytest tests/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/domain/test_note_type_definition.py` — stubs for HARD-09 (NoteTypeDefinition)
- [ ] `tests/services/test_upgrade_schema.py` — stubs for HARD-08 (schema versioning detection)

*Existing infrastructure covers all other phase requirements — session, reweave, check, plugins tests already exist but are excluded from coverage.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI help text accuracy | HARD-04 | Requires human judgment on doc quality | Read `ztlctl --help`, `ztlctl create --help`, compare with README sections |
| MCP HTTP transport warning | HARD-07 | Requires visual verification of warning output | Run `ztlctl serve --transport http`, verify warning appears in stderr |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
