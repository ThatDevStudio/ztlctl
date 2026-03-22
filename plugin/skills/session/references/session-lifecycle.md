# Session Lifecycle Reference

## Session States

Sessions follow a simple state machine with strict one-at-a-time enforcement:

```
No session
    │
    └──[session_start(topic)]──> Active session
                                        │
                                        └──[session_close(summary)]──> Closed session
                                                                              │
                                                                              └──enrichment pipeline runs
```

**Key invariant:** Only one session can be open at a time. `session_start` fails if a session is already open — always call `session_status()` first in the open path to check.

**Reopen:** Closed sessions can be reopened via the `session_reopen` action if needed, but the standard workflow is open → work → close.

## Session-Linked Content

All content created during a session should include `session=<session_id>` in the creation call:

- `create_note(title="...", session="<session_id>")`
- `create_reference(title="...", session="<session_id>")`
- `create_task(title="...", session="<session_id>")`

Session-linked content gets cross-session reweave during close — the enrichment pipeline uses session membership to find notes that should be linked to each other.

Content without a session ID is valid but misses enrichment benefits: orphan sweep and cross-session reweave only process session-linked items.

## Pre-Flight Alignment

The `check_alignment` step in the open path is advisory — it never blocks session start:

- `check_alignment(decision="Open session: <topic>")` returns `relevant_priorities`: the polaris priorities this session relates to.
- If `relevant_priorities` is non-empty: report the matching priorities. The session aligns with the vault's strategic focus.
- If `relevant_priorities` is empty: that is information, not a blocker. The session may be exploratory. Report "No direct priority overlap found" and proceed.

Alignment is a discipline check, not a gate.

## Error Handling

If `session_start` returns `result.success = false`:
- Check `result.error.code` — common codes: `SESSION_ALREADY_OPEN` (a session is already active), `INVALID_TOPIC` (topic is empty or too long).
- For `SESSION_ALREADY_OPEN`: surface the active session via `session_status()` and ask user to confirm close or reuse.
- For other errors: surface `result.error.message` and stop.
