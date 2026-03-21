---
phase: 10
slug: user-guide-content
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 10 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | mkdocs build verification + content checks |
| **Config file** | mkdocs.yml |
| **Quick run command** | `mkdocs build --strict 2>&1` |
| **Full suite command** | `uv run pytest && mkdocs build --strict` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `mkdocs build --strict`
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | UGDE-02 | content check | `wc -l docs/paradigms.md` (must be >150) | ✅ | ⬜ pending |
| 10-02-01 | 02 | 1 | UGDE-03 | content + build | `test -f docs/plugins.md && mkdocs build --strict` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 2 | UGDE-04 | content check | `grep -c "research-capture\|review-triage\|knowledge-synthesis" docs/agentic-workflows.md` (must be >3) | ✅ | ⬜ pending |
| 10-03-02 | 03 | 2 | UGDE-05 | content check | `grep -c "session" docs/agentic-workflows.md` (must be >10) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] Verify `mkdocs build --strict` passes before any content edits

*This phase is documentation-only — no new test fixtures needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Paradigm guide reads clearly | UGDE-02 | Quality judgment | Read docs/paradigms.md end-to-end, verify comparison table and scenarios make sense |
| Plugin guides are accurate | UGDE-03 | Behavioral verification | Compare plugin docs against actual CLI behavior |
| Recipe walkthroughs are followable | UGDE-04 | UX judgment | Follow each recipe walkthrough step-by-step in a test vault |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
