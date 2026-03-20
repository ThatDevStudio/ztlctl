---
phase: 11
slug: developer-guide-api-reference
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | mkdocs build verification + content checks |
| **Config file** | mkdocs.yml |
| **Quick run command** | `mkdocs build --strict 2>&1` |
| **Full suite command** | `uv run pytest && mkdocs build --strict` |
| **Estimated runtime** | ~45 seconds (mkdocstrings adds griffe parsing time) |

---

## Sampling Rate

- **After every task commit:** Run `mkdocs build --strict`
- **After every plan wave:** Run full suite
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | DVGD-01 | content + build | `test -f docs/plugin-guide.md && mkdocs build --strict` | ❌ W0 | ⬜ pending |
| 11-02-01 | 02 | 1 | DVGD-02 | build + content | `mkdocs build --strict && test -f docs/api-reference.md` | ❌ W0 | ⬜ pending |
| 11-03-01 | 03 | 2 | DVGD-03 | content check | `grep -c "ActionRegistry\|ServiceResult\|BaseController" docs/development.md` (>3) | ✅ | ⬜ pending |
| 11-03-02 | 03 | 2 | DVGD-04 | content check | `grep -c "plugin-guide\|api-reference" CONTRIBUTING.md` (>0) | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `uv add --group dev "mkdocstrings[python]>=1.0.3"` — install API doc generator
- [ ] Verify `mkdocs build --strict` still passes after adding mkdocstrings plugin

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| mkdocstrings renders correctly with shadcn | DVGD-02 | Visual rendering check | Run `mkdocs serve`, navigate to API Reference, verify signatures render |
| Plugin tutorial is followable | DVGD-01 | UX judgment | Follow the "Build Your First Plugin" steps end-to-end |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
