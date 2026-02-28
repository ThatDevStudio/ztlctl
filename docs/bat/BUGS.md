# ztlctl BAT Bug Report

**Version**: 0.1.0
**Source**: Business Acceptance Test suite (130 tests, 2 runs)

## Bug Status Overview

| ID | Description | Run 1 | Run 2 | Status |
|----|-------------|-------|-------|--------|
| BUG-01 | Regenerate without config creates orphan files | FAIL | PASS | Fixed |
| BUG-02 | Batch all-or-nothing lacks rollback | FAIL | PASS | Fixed |
| BUG-03 | Note status auto-computation off-by-one | FAIL | PASS | Fixed |
| BUG-04 | Duplicate JSON on error (stdout+stderr) | Present | Not reproduced in preserved logs | Closed as stale |
| BUG-05 | Integrity check warns on clean vault | Present | Mitigated | Fixed |
| BUG-06 | GitPlugin.post_create() signature mismatch | Present | — | Fixed |
| BUG-07 | Session close integrity false positive | Present | — | Fixed |
| BUG-08 | Unlink leaves double spaces | Present | — | Fixed |
| BUG-09 | Maturity not in query get response | Present | PASS | Fixed |
| BUG-10 | op field inconsistency (batch errors) | Present | PASS | Fixed |
| BUG-11 | post_init hook not wired | Present | PASS | Fixed |
| BUG-12–16 | Various minor issues | Present | — | Fixed |

---

## Active Issues

No active BAT bugs remain on the current codebase.

### Historical Notes

**BUG-04**: The preserved BAT evidence does not support an active duplicate-JSON
bug. The dedicated cross-cutting run in `.bat/logs/bat-121.log` records
`STDOUT length: 0`, `Stdout empty (no duplication): True`, and
`Stdout has JSON (duplication bug): False`. Current CLI regression coverage now
locks stderr-only JSON emission for representative `agent session`, `agent context`,
and `check --rollback` failure paths.

**BUG-05**: Default `check` remains warning-inclusive for human operators, but
the JSON payload now includes explicit machine-readable health fields:
`healthy`, `error_count`, and `warning_count`. Automation should use those fields
or `--errors-only` rather than inferring health from `count` alone.

---

## Resolved Issues (Confirmed in Run 2)

### BUG-01: Regenerate Without Config (BAT-06) — FIXED
`agent regenerate` now returns `NO_CONFIG` error with exit code 1 when no
`ztlctl.toml` exists. Clean JSON error response, no crash.

### BUG-02: Batch Rollback (BAT-20) — FIXED
Batch create in all-or-nothing mode now performs true transaction rollback.
When item 1 fails, item 0 is removed from both filesystem and database.

### BUG-03: Status Auto-Computation (BAT-43) — FIXED
Note status (draft/linked/connected) now reflects current link count
immediately on the same update. PROPAGATE/INDEX ordering corrected.

### BUG-06: GitPlugin.post_create() Signature — FIXED
Plugin fires correctly on post_create. Marker file confirms correct payload
with content_type, content_id, title, path, tags (BAT-110).

### BUG-09: Maturity Not in Query Get — FIXED
`query get` JSON now includes `maturity` field (BAT-33).

### BUG-10: op Field Inconsistency — FIXED
Batch error paths now use consistent `batch_create` op (BAT-20).

### BUG-11: post_init Hook Not Wired — FIXED
Event WAL shows `post_init` events completing (BAT-115, BAT-116).

---

## What Is Left

No active BAT bugs remain.

Non-blocking BAT observations still exist in `docs/bat/SUMMARY.md`, but they are
design backlog items rather than confirmed bug regressions.
