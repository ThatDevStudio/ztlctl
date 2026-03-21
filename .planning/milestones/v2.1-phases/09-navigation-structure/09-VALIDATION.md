---
phase: 9
slug: navigation-structure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-20
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | mkdocs build verification + file existence checks |
| **Config file** | mkdocs.yml |
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
| 09-01-01 | 01 | 1 | UGDE-01 | build + nav check | `mkdocs build --strict && grep -c "User Guide" site/index.html` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | UGDE-01 | file check | `test -f docs/guide/index.md && test -f docs/dev/index.md` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 1 | AGNT-01 | file check | `test -f docs/llms.txt && head -1 docs/llms.txt` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | AGNT-02 | script + file | `python scripts/gen_llms_full_txt.py && test -f docs/llms-full.txt` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `docs/guide/index.md` — User Guide landing page stub
- [ ] `docs/dev/index.md` — Developer Guide landing page stub
- [ ] Verify `mkdocs build --strict` still passes after nav restructure

*Existing test infrastructure (pytest) covers Python source — this phase adds docs structure verification.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Two-track nav renders correctly | UGDE-01 | Visual check in browser | Run `mkdocs serve`, verify sidebar shows User Guide / Developer Guide sections |
| llms.txt accessible at site URL | AGNT-01 | Requires live deploy | After deploy, curl https://thatdevstudio.github.io/ztlctl/llms.txt |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
