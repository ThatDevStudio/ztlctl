# T-001: Post-Create Automatic Reweave

> Design document for automatic reweave after content creation.
> Created 2026-02-27.

## Problem

DESIGN.md Section 4 states: "Reweave runs unless `--no-reweave` is passed." Currently reweave only runs manually (`ztlctl reweave`) or at session close. The `--no-reweave` CLI flag parses into `ZtlSettings.no_reweave` but is never consulted. New content is created without link suggestions until a manual reweave or session close.

## Decision

**Approach: Direct service call in `CreateService._create_content()`** (Option B from TASKS.md).

Rejected alternative: Plugin hookimpl on `post_create` (Option A). Rejected because the async EventBus dispatch cannot surface reweave results back to the caller — hookspecs return `None`. The user wants inline results (e.g., "2 links added") in the create output.

The direct service call follows the established pattern in `SessionService._cross_session_reweave()`.

## Design

### Pipeline Change

`_create_content()` gains a 6th stage between EVENT DISPATCH and RESPOND:

```
VALIDATE → GENERATE → PERSIST → INDEX → EVENT → REWEAVE → RESPOND
```

### Gate Logic

Two checks before calling `ReweaveService`:

1. **`self._vault.settings.no_reweave`** — CLI per-invocation flag (`--no-reweave`). Skip if `True`.
2. **Content type filter** — Only `note` and `reference`. Tasks don't participate in the knowledge graph (matching `_cross_session_reweave` in session.py).

`reweave.enabled` (vault-wide TOML config) is checked inside `ReweaveService.reweave()` itself — not duplicated here.

### Integration

```python
# ── REWEAVE ──────────────────────────────────
if (
    not self._vault.settings.no_reweave
    and content_type in ("note", "reference")
):
    with trace_span("post_create_reweave"):
        from ztlctl.services.reweave import ReweaveService
        rw = ReweaveService(self._vault).reweave(content_id=content_id)
        if rw.ok:
            count = rw.data.get("count", 0)
            if count > 0:
                warnings.append(f"Auto-reweave: {count} link(s) added")
        else:
            msg = rw.error.message if rw.error else "unknown"
            warnings.append(f"Auto-reweave skipped: {msg}")
```

### Result Surfacing

Reweave outcomes flow through the existing `warnings` list into `ServiceResult.warnings`. The output layer already renders warnings. Example output:

```
Created note ZTL-0042: "My New Note"
  ⚠ Auto-reweave: 2 link(s) added
```

### Telemetry

`trace_span("post_create_reweave")` nests under the parent `@traced` span on `create_note/reference/task`. Visible in `--verbose` span tree with duration color-coding.

### Graph State

After the INDEX stage transaction commits, `vault.transaction()` calls `self._graph.invalidate()`. When `ReweaveService._score_candidates()` accesses `self._vault.graph.graph`, it lazy-rebuilds from the freshly committed DB state. This is correct — reweave sees the new content.

## Files Modified

| File | Change |
|---|---|
| `src/ztlctl/services/create.py` | Add REWEAVE stage in `_create_content()` |
| `tests/services/test_create.py` | 5 new test cases (see below) |

## Test Plan

1. **Happy path** — create note in vault with existing content, verify `warnings` contains link count
2. **`--no-reweave` gate** — create with `no_reweave=True`, verify ReweaveService is not called
3. **Task skip** — create task, verify reweave is not called (content type filter)
4. **Reweave failure** — mock `reweave()` returning `ok=False`, verify warning and create still succeeds
5. **`reweave.enabled=False`** — verify ReweaveService internal gate short-circuits gracefully
