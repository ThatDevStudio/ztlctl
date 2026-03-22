---
name: orient-session
description: >
  Use when the user wants to continue prior work, resume a topic, or pick up
  where they left off on a recurring subject. Recalls prior session context
  before opening a new session. Activates on "continue work on X", "resume
  research on X", "pick up where I left off on X", or "start session with
  context on X".
version: 1.0.0
disable-model-invocation: true
---

# Recall-Driven Session Start

Load prior session context on a topic before opening a new session. This skill
prevents re-doing work by surfacing what prior sessions covered, then starting
grounded in that context. Use this when resuming — not for cold-start sessions
(use `ztl:session` for that).

## Iron Laws

**Present prior context summary before opening any session.** Never call
`session_start` without first showing the user what prior sessions found.
The checkpoint in step 5 is not optional.

**Check `result.success` after every MCP call.** If `recall_topic` fails,
stop and report the error — do not start a session on incomplete recall.

## Workflow

1. **Read `ztlctl://sessions/recent`** — load the last 5 sessions. Scan
   topics and timestamps for relevance to the user's stated subject.

2. **`recall_topic(query="<topic>")`** — search session log entries for
   sessions matching the topic. Returns matching sessions with note IDs,
   timestamps, and relevance scores.

3. **For the top relevant sessions:** extract `note_ids`; call
   `get_document(content_id="<id>")` on the highest-scored and most recently
   modified notes to rebuild context. Parallel fetches are acceptable.

4. **Summarize prior context:**
   "Found N prior sessions on '<topic>'. Key notes: [titles]. Last worked
   on: [date]. Main findings: [summary of note bodies from step 3]."

5. **Present summary and ask user to confirm continuation.** Do not open
   the session until the user confirms. Ask: "Continue from this context, or
   start fresh?" Stop here until the user responds.

6. **`session_start(topic="<topic> — continued")`** — open a new session
   grounded in prior context. The " — continued" suffix creates a session
   lineage that `recall_topic` can trace in future runs. Check `result.success`.
   Report: session ID, prior session count, key note IDs loaded.

## Path detection

This skill is for RESUMING prior work on a recurring topic. If the user is
starting work on a topic for the first time (no prior sessions), use `ztl:session`
instead — orient-session adds recall overhead with no benefit on a fresh topic.

If `recall_topic` returns no matching sessions, report: "No prior sessions found
on '<topic>'. Suggest using `ztl:session` for a clean start."

See `references/recall-workflow.md` for sessions/recent resource format,
recall_topic output, and continuation pattern details.
