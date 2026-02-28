# ztlctl BAT Bug Report

**Date**: 2026-02-28
**Version**: 0.1.0
**Source**: Business Acceptance Test suite (130 tests)

This file now tracks only active BAT issues.

Previously reported items `BUG-01`, `BUG-02`, `BUG-03`, `BUG-04`, `BUG-06`,
`BUG-07`, `BUG-08`, `BUG-09`, `BUG-11`, `BUG-12`, `BUG-13`, `BUG-14`,
`BUG-15`, and `BUG-16` have been fixed on `develop`. `BUG-10` is not
reproducible on current `develop` and is no longer tracked as an active bug.

## Active Issues

### BUG-05: Integrity Check Warns on Clean Vault [MITIGATED]

**Status Update (2026-02-28)**: Partially addressed on `develop`. `check` now
supports `--errors-only` and `--min-severity error`, which allows automation to
ignore advisory warnings. Default `check` behavior still includes warning-level
issues on otherwise healthy vaults.

**Category**: Integrity & Maintenance
**Severity**: Low

**Impact**: A freshly created vault can still report non-zero warning counts on
`check`, which means callers using the default output cannot treat
`data.count == 0` as "vault is healthy" without also deciding how to handle
advisory warnings.

**Recreation**:
```bash
mkdir bat-89 && cd bat-89
ztlctl init --name "test" --client vanilla --tone minimal --topics "test" --no-workflow
ztlctl --json create note "Alpha" --tags "test"
ztlctl --json create note "Beta" --tags "test"
ztlctl --json create note "Gamma" --tags "test"
ztlctl --json create task "Test Task"
ztlctl --json check
```

**Current Result**:
- Exit code `0`
- `data.count` may be non-zero because warning-level issues are included
- `ztlctl --json check --errors-only` and
  `ztlctl --json check --min-severity error` provide the errors-only view

**Expected Result**:
- Either default `check` should report only actionable integrity failures
- Or the output contract should make warning-only healthy states explicit enough
  that automation does not need to infer health from `data.count`

**Remaining Work**:
- Decide whether default `check` should stay advisory-inclusive
- If not, either:
  - downgrade best-practice findings further, or
  - split counts by severity, or
  - exclude warnings from the top-level health count

## What Is Left

- `BUG-05` is the only BAT item still tracked here.
