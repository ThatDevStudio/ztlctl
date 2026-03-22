---
name: review-triage
description: >
  Use when the user asks to review the work queue, triage pending items,
  clear the backlog, or find out what needs attention in the vault. Surfaces
  prioritized actionable items and batch-processes approved updates.
version: 1.0.0
disable-model-invocation: true
---

# Work Queue Review and Triage

Review the vault's work queue, evaluate each item, and batch-process approved actions. This skill uses the loop pattern: enumerate all items, inspect each, propose actions, then execute the approved set after user confirmation.

## Iron Laws

**Never write without confirmation.** Present the full proposed action set BEFORE executing any writes. The user approves or prunes the batch before a single write fires.

**Check `result.success` after every write.** If `update_content` or `close_content` fails, stop the batch and report what succeeded and what failed. Do not silently skip failures.

## Workflow

1. **Check vault integrity** — `check_integrity()`: run the 4-category integrity scanner (orphan edges, broken links, missing files, schema issues). Surface any critical issues before reviewing the work queue. If integrity issues are found, report them first — they may explain items in the queue.

2. **Load queue** — `work_queue()`: load the prioritized work queue. All actionable items are returned with composite scores. If the queue is empty and no integrity issues, report "Work queue is empty. Vault is clear." and stop.

3. **Inspect top items** — For each of the top items (up to 10): `get_document(content_id="<id>")` — fetch full content to evaluate. Parallel fetches are acceptable.

4. **Evaluate each item** — Classify and propose an action:
   - **Stale seed**: maturity=seed, age > 7 days, no body updates → suggest: promote to budding or archive
   - **Actionable task**: has a clear next step, not yet done → suggest: keep as-is or mark complete
   - **Orphan note**: 0 outgoing links, status=draft → suggest: add links via reweave, or archive
   - **Draft needing attention**: draft status, has content but no connections → suggest: add tags/links to promote

5. **Present summary table** — Show proposed actions before any writes:
   ```
   | # | ID | Title | Type | Suggestion | Priority |
   ```
   Ask: "Process all / only high-priority (score > X) / pick specific items?"

6. **Batch execute** — For each approved item, execute the proposed action:
   - Promote maturity: `update_content(content_id="<id>", changes={"maturity": "budding"})`
   - Mark complete: `update_content(content_id="<id>", changes={"status": "complete"})`
   - Archive: `close_content(content_id="<id>")`
   - Reweave orphan: `reweave(content_id="<id>")`
   Check `result.success` after each call. Stop the batch on failure, report progress.

7. **Report results** — Summarize: integrity issues found, items reviewed, items updated, items archived, items remaining in queue.

## Batch Confirmation Pattern

The confirmation model prevents accidental bulk writes:

- **Present first, execute second** — show the full proposed action set, then wait for approval
- **Scope selection** — user can select "all", "high-priority only" (score above a threshold), or name specific IDs
- **Archive warning** — archives are highlighted separately; `close_content` is a soft-delete that hides the item from default queries
- **After batch** — report successes and failures; surface any items that need manual review

---

See `references/triage-workflow.md` for item evaluation criteria and priority scoring details.
