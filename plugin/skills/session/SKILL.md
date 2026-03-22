---
name: session
description: >
  Use when the user wants to start, begin, or open a work session, OR close,
  end, or finish an active session. Manages the full session lifecycle:
  pre-flight checks, polaris alignment, session start, and session close with
  enrichment pipeline.
version: 1.0.0
disable-model-invocation: true
---

# Session Lifecycle

Sessions are the primary coordination unit in ztlctl. This skill manages the full arc: pre-flight check, polaris alignment, start, and close with enrichment. Detect which path to run from the user's intent — "start/begin/open" runs the open path; "close/end/finish" runs the close path.

## Iron Laws

**Check `result.success` after every MCP call.** If `session_start` or `session_close` fails, stop and surface the error message. Do not silently continue.

**Only one session can be open at a time.** If a session is already open when the user asks to start, surface the active session ID, topic, and start time. Ask: "Session `<ID>` is open on `<topic>`. Close it first, or continue with it?"

## Open Path

1. **Pre-flight check** — `session_status()`: check if a session is already open.
   - If open: surface the active session ID, topic, and start time. Ask: "Session `<ID>` is open on `<topic>`. Close it first, or continue with it?" Stop here until user responds.
   - If no session open: proceed to step 2.

2. **Load priorities** — Read `ztlctl://polaris`: load the vault's current strategic priorities.

3. **Alignment check** — `check_alignment(decision="Open session: <topic>")`: advisory check against polaris priorities. Report which priorities this session relates to. This never blocks — proceed to step 4 regardless.

4. **Open session** — `session_start(topic="<topic>")`: start the session. Capture the returned `session_id`. Check `result.success` — stop and report error if false.

5. **Load methodology** — Read `ztlctl://self/methodology`: load vault workflow conventions for this session context.

6. **Report to user** — Summarize: session ID, aligned polaris priorities, methodology summary. "Session `<ID>` is now open. Relevant priorities: [list]. Ready to capture."

## Close Path

1. **Get summary** — If the user has not provided a session summary, ask for one: "In one sentence, what did you accomplish in this session?"

2. **Close session** — `session_close(summary="<summary>")`: close the active session and receive the enrichment report. Check `result.success` — stop and report error if false.

3. **Parse enrichment report** — Extract and present:
   - `reweave_count`: notes rewoven (linked to related content)
   - `orphan_count`: previously isolated notes connected
   - `integrity_issues`: structural problems found

4. **Surface integrity warning** — If `integrity_issues > 0`: "Found [N] integrity issues during enrichment. Consider running `ztlctl check check` for details."

## Path Detection

Determine which path to run from the user's phrasing:

**Open path triggers:** "start", "begin", "open", "new session", "work on X", "let's start"

**Close path triggers:** "close", "end", "finish", "wrap up", "done", "done with session"

**Ambiguous:** If unclear, ask: "Do you want to start a new session or close the current one?"

---

See `references/session-lifecycle.md` for the full session state machine and session-linked content details.
See `references/enrichment-report.md` for interpreting the enrichment pipeline output after `session_close`.
