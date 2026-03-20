---
phase: 8
slug: mkdocs-infrastructure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x (existing) + mkdocs build verification |
| **Config file** | pyproject.toml (pytest), mkdocs.yml (new) |
| **Quick run command** | `mkdocs build --strict 2>&1` |
| **Full suite command** | `uv run pytest && mkdocs build --strict` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `mkdocs build --strict`
- **After every plan wave:** Run `uv run pytest && mkdocs build --strict`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | INFR-01 | build | `mkdocs build --strict` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | INFR-02 | file check | `test ! -f site/backlog/index.html` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | INFR-03 | file check | `test ! -d site/plans` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 1 | INFR-04 | CI | GitHub Actions workflow exists | ❌ W0 | ⬜ pending |
| 08-01-05 | 01 | 1 | INFR-05 | build | `mkdocs build --strict` (redirects resolve) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `mkdocs.yml` — MkDocs config with mkdocs-shadcn theme
- [ ] `uv add --group dev mkdocs mkdocs-shadcn mkdocs-redirects` — install docs tooling
- [ ] Verify `mkdocs build` runs without errors

*Existing test infrastructure (pytest, ruff, mypy) covers Python source — this phase adds docs build verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dark mode toggle works | INFR-01 | Visual check in browser | Run `mkdocs serve`, toggle dark/light mode |
| GitHub Pages shows new site | INFR-04 | Requires push to develop + Pages deployment | Push, wait for GH Actions, check live URL |
| GitHub Pages source setting | INFR-04 | Repo settings UI change | Settings → Pages → Source → gh-pages branch |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
