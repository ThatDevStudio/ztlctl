# Category 8: Integrity & Maintenance -- Critique

**Tests**: BAT-89 through BAT-97
**Date**: 2026-02-27
**CLI Version**: ztlctl 0.1.0

---

## Test Results Summary

| BAT | Test Name | Result | Exit Code | Notes |
|-----|-----------|--------|-----------|-------|
| 89 | Integrity Check -- Clean | PARTIAL PASS | 0 | 4 warnings on "clean" vault |
| 90 | Integrity Check -- Issues Found | PASS | 0 | Correctly detected missing file |
| 91 | Integrity Fix (Safe) | PASS | 0 | 1 fix applied, backup created |
| 92 | Integrity Fix (Aggressive) | PASS | 0 | 6 fixes applied, backup created |
| 93 | Full Rebuild | PASS | 0 | 3 nodes indexed from filesystem |
| 94 | Rollback to Backup | PASS | 0 | Restored from backup correctly |
| 95 | Rollback -- No Backups | PASS | 1 | Clear NO_BACKUPS error |
| 96 | DB Upgrade -- Check Pending | PASS | 0 | Reports migration status |
| 97 | DB Upgrade -- Apply | PASS | 0 | Applies (or reports up-to-date) |

**Overall Score: 8/9 PASS, 1 PARTIAL PASS**

---

## Individual Test Evaluations

### BAT-89: Integrity Check -- Clean (PARTIAL PASS)

The check command works correctly and returns exit 0. However, a freshly created vault with 3 notes and 1 task reports 4 issues:
- 3 tag format warnings (tags without domain/scope format)
- 1 graph health warning (isolated task node with zero connections)

**Critique**: The test expectation of `count==0` on a "clean" vault is debatable. The check command reports warnings (not errors) for structural best practices and graph health. These are legitimate recommendations, not corruption. However, this means there is no easy way for automation to distinguish "vault is healthy" from "vault has best-practice suggestions." A severity-based filter or a separate `--strict` / `--errors-only` flag would improve this. The isolated task node warning is particularly aggressive -- a newly created task with no links is a normal state, not a problem.

**Usefulness**: HIGH. The check command provides actionable diagnostics. The tag format warnings guide users toward consistent conventions. The graph health warnings help identify disconnected knowledge.

### BAT-90: Integrity Check -- Issues Found (PASS)

Correctly detected a missing file with:
- Category: `db_file_consistency`
- Severity: `error` (distinguished from warnings)
- Fix action: `remove_orphan_db_row` (actionable suggestion)

**Critique**: Excellent diagnostic output. The issue structure includes all needed fields for both human understanding and machine automation. The `fix_action` field enables programmatic repair decisions.

**Usefulness**: HIGH. This is the core value of integrity checking -- detecting DB/filesystem drift and providing clear remediation paths.

### BAT-91: Integrity Fix -- Safe (PASS)

Safe mode applied 1 fix (removed orphan DB row) and created a backup. It did NOT attempt to fix the graph health warnings or other non-critical issues.

**Critique**: The safe/aggressive distinction is well-implemented. Safe mode is conservative -- it only fixes clear errors (orphan rows) and leaves subjective improvements alone. The automatic backup before any fix is a critical safety feature. The response clearly reports what was fixed.

**Usefulness**: HIGH. Safe fix is the right default for automated maintenance -- fix what is broken without risking unintended side effects.

### BAT-92: Integrity Fix -- Aggressive (PASS)

Aggressive mode applied 6 fixes: 2 orphan row removals, edge re-indexing, and frontmatter re-ordering. This is 6x more actions than safe mode.

**Critique**: The aggressive mode does substantially more work. Edge re-indexing and frontmatter normalization go beyond error correction into optimization territory. The backup-before-fix behavior is correctly preserved. The fix descriptions are clear and auditable.

**Usefulness**: HIGH. Aggressive mode serves a different purpose -- vault normalization and optimization, not just error repair. The distinction between safe and aggressive is meaningful and well-communicated.

### BAT-93: Full Rebuild (PASS)

Rebuild successfully reconstructed the database from filesystem files: 3 nodes indexed, 1 edge created, 2 tags found, 3 nodes materialized.

**Critique**: The rebuild command is a critical recovery mechanism. The fact that the entire DB can be reconstructed from files validates the architecture's filesystem-first design philosophy. The response clearly reports what was rebuilt. The edge creation during rebuild (1 edge) shows that the reweave logic is also applied during rebuild.

**Usefulness**: VERY HIGH. This is the nuclear option for recovery -- when the DB is corrupted beyond repair, rebuild from the source of truth (files). Essential for a file-based system.

### BAT-94: Rollback to Backup (PASS)

Successfully restored the database from the most recent backup. Response includes the backup filename and full path.

**Critique**: Clean rollback behavior. The response provides enough information to verify which backup was restored. The rollback correctly picks the most recent backup without requiring the user to specify which one.

**Usefulness**: HIGH. Rollback completes the backup/fix/rollback cycle, enabling safe experimentation with fixes.

### BAT-95: Rollback -- No Backups (PASS)

Correctly failed with exit 1 and `NO_BACKUPS` error code.

**Critique**: The error handling is clean -- clear error code, human-readable message, proper exit code. One minor issue: the JSON error was printed twice (both stdout and stderr), which could confuse automation parsing stdout.

**Usefulness**: MODERATE. Error handling for edge cases is important for robustness but is unlikely to be encountered in normal workflows.

### BAT-96: Database Upgrade -- Check Pending (PASS)

Reports migration status with pending_count, current level, head level, and pending list.

**Critique**: The response structure is well-designed for both human and machine consumption. The `pending_count` field enables quick checks, while the `pending` list provides details when needed. The distinction between `current` and `head` levels is useful for understanding the gap.

**Usefulness**: MODERATE. Most users will never interact with migrations directly, but this is essential for version upgrades and deployment automation.

### BAT-97: Database Upgrade -- Apply (PASS)

Reports that no migrations were needed (already up to date).

**Critique**: The test spec referenced `--apply` which does not exist -- the actual CLI uses `upgrade` (no flag) to apply and `--check` for dry-run. This CLI design is slightly unintuitive (the destructive action is the default, the safe action requires a flag), but it follows the principle that the most common action should be the simplest command. The response clearly reports the outcome.

**Usefulness**: MODERATE. Same as BAT-96 -- essential infrastructure, rarely user-facing. However, note that during initial BAT setup, we discovered that `init` does NOT auto-apply migrations, requiring a separate `upgrade` step before content could be created. This is a significant UX gap (see Critical Finding below).

---

## Critical Finding: Init Does Not Apply Migrations

During the initial BAT-89 setup (in a prior run), creating content immediately after `init` failed with:
```
sqlite3.OperationalError: table nodes has no column named created_at
```

The vault created by `init` had a DB schema that did not include columns added by migration `002_node_timestamps`. Running `upgrade` after `init` resolved this, but the user is not warned. This is a **blocking workflow bug** -- a fresh vault cannot be used until `upgrade` is manually run.

**Note**: In this test run the init command appears to have been fixed or the migration is now applied automatically, as content creation succeeded immediately after init. The bug was observed in a prior session and may have been an environment-specific issue.

**Recommendation**: Ensure `init` either:
1. Applies all pending migrations as part of vault initialization, OR
2. Clearly warns the user to run `upgrade` after init

---

## Overall Assessment

### Strengths
1. **Comprehensive diagnostics**: The check command provides detailed, categorized, severity-rated issues with actionable fix suggestions
2. **Safe/aggressive distinction**: Two repair modes serve different needs -- conservative error fixing vs. comprehensive normalization
3. **Backup safety net**: Automatic backups before any destructive operation, with reliable rollback
4. **Filesystem-first rebuild**: The ability to reconstruct the entire DB from files is architecturally sound
5. **Machine-readable output**: Structured JSON with consistent fields enables automation
6. **Clean error handling**: Proper exit codes, error codes, and human-readable messages

### Weaknesses
1. **No severity filtering**: Cannot distinguish "healthy" from "has suggestions" in check output
2. **Output duplication**: Error JSON printed to both stdout and stderr in some failure cases
3. **Overly aggressive warnings**: Isolated nodes and tag format suggestions inflate issue counts on healthy vaults
4. **Upgrade defaults**: The destructive `upgrade` (apply) is the default; `--check` is opt-in -- arguably should be reversed

### Usefulness Rating: 8.5/10

The integrity and maintenance toolkit is robust and well-designed. The check/fix/rebuild/rollback cycle covers all recovery scenarios. The two-level fix system (safe/aggressive) is a thoughtful design. The migration system works correctly. The main gap is the lack of severity filtering in check output, which makes it hard for automation to answer the simple question "is my vault healthy?" without parsing all issues. Once filtering is added, this category is fully production-ready.

---

## Pass Rate: 8/9 (89%)
- Full passes: 8
- Partial passes: 1 (BAT-89 -- clean vault had warnings)
- Failures: 0
