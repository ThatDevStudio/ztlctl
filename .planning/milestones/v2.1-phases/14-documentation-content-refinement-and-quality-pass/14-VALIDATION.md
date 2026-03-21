---
phase: 14
slug: documentation-content-refinement-and-quality-pass
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 14 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | mkdocs build --strict + grep verification |
| **Config file** | mkdocs.yml |
| **Quick run command** | `mkdocs build --strict 2>&1 | tail -5` |
| **Full suite command** | `uv run pytest && mkdocs build --strict` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `mkdocs build --strict 2>&1 | tail -5`
- **After every plan wave:** Run `uv run pytest && mkdocs build --strict`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 14-01-01 | 01 | 1 | INT-01 | grep | `grep -c "Built-in Plugins" docs/guide/index.md` | ✅ | ⬜ pending |
| 14-01-02 | 01 | 1 | FLOW-01 | grep | `grep -c "GitHub Actions" docs/troubleshooting.md` | ✅ | ⬜ pending |
| 14-01-03 | 01 | 1 | docs-search | grep | `grep -c "ZTLCTL_DOCS_PATH" docs/commands.md` | ✅ | ⬜ pending |
| 14-02-xx | 02 | 1 | quality | build | `mkdocs build --strict` | ✅ | ⬜ pending |
| 14-03-01 | 03 | 2 | new-pages | build | `grep -c "best-practices.md\|agents.md" mkdocs.yml` | ❌ W0 | ⬜ pending |
| 14-04-xx | 04 | 3 | agent-harden | grep | `wc -l docs/llms.txt` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] None — existing mkdocs build infrastructure covers all phase requirements

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| GitHub Pages source setting | FLOW-01 | Requires GitHub repo admin access | Navigate to Settings > Pages, verify source is "GitHub Actions" |
| Visual rendering quality | quality-bar | Subjective visual check | Run `mkdocs serve`, review pages in browser |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
