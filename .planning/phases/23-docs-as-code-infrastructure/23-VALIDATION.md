---
phase: 23
slug: docs-as-code-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-21
---

# Phase 23 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest --cov --cov-report=term-missing` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest --cov --cov-report=term-missing`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 23-01-01 | 01 | 1 | DINF-01 | integration | `mkdocs build --strict` | ✅ | ⬜ pending |
| 23-01-02 | 01 | 1 | DINF-01 | config | `uv run pymarkdownlnt scan docs/` | ❌ W0 | ⬜ pending |
| 23-01-03 | 01 | 1 | DINF-04 | integration | `mkdocs build --strict` (date plugin) | ❌ W0 | ⬜ pending |
| 23-02-01 | 02 | 1 | DEBT-09 | unit | `uv run pytest tests/services/test_post_action_dispatch.py -x` | ✅ | ⬜ pending |
| 23-02-02 | 02 | 1 | DEBT-10 | grep | `grep -c "stub" src/ztlctl/commands/contradiction.py` returns 0 | ✅ | ⬜ pending |
| 23-02-03 | 02 | 1 | DINF-02 | grep | `grep "Documentation Rules" CLAUDE.md` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pymarkdownlnt` added to dev dependencies — `uv add --group dev pymarkdownlnt`
- [ ] `mkdocs-git-revision-date-localized-plugin` added to dev dependencies
- [ ] `.pymarkdown.yml` config file created with rule overrides (MD033 for admonition HTML)
- [ ] `.vale.ini` config file created with Google style reference

*Existing pytest infrastructure covers DEBT-09/DEBT-10 requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CI `doc_lint` job runs in parallel with `validate_pr` | DINF-01 | GitHub Actions workflow must be tested by pushing a PR | Push a test PR and verify both jobs appear in checks |
| Vale prose lint catches style violations | DINF-01 | Vale binary not installed locally by default | Run `vale docs/` locally if installed, or verify in CI |
| GSD template includes Documentation Tasks | DINF-03 | External to repo (GSD templates) | Verify CLAUDE.md documents the expectation |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
