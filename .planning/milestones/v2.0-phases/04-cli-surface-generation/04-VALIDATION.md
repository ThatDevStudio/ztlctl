---
phase: 04
slug: cli-surface-generation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest && uv run ruff check . && uv run mypy src/` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest && uv run ruff check . && uv run mypy src/`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 40 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | ACTN-04 | unit | `uv run pytest tests/commands/test_cli_generator.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | ACTN-04 | integration | `uv run pytest tests/commands/test_generated_commands.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | ACTN-05 | unit | `uv run pytest tests/commands/test_custom_commands.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | ACTN-04 | integration | `uv run pytest tests/mcp/test_parity.py tests/commands/test_cli_parity.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/commands/test_cli_generator.py` — stubs for ACTN-04 generator tests
- [ ] `tests/commands/test_generated_commands.py` — stubs for generated command integration tests
- [ ] `tests/commands/test_cli_parity.py` — stubs for CLI/MCP parity verification

*Existing infrastructure covers test framework and fixtures.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `ztlctl --help` shows grouped commands | ACTN-04 | Visual layout verification | Run `ztlctl --help`, verify command grouping matches current |
| Interactive create prompts work | ACTN-05 | Requires TTY input | Run `ztlctl create note --interactive`, verify prompts appear |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 40s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
