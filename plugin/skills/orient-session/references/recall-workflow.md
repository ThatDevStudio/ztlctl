# Recall Workflow Reference

Detailed reference for `ztlctl://sessions/recent` resource format, `recall_topic`
output, and the session continuation pattern used by ztl:orient-session.

## ztlctl://sessions/recent resource

The `ztlctl://sessions/recent` MCP resource returns the last N sessions
(default: 5) with the following fields per session:

- **`session_id`** — unique session identifier
- **`topic`** — the topic string provided at `session_start`
- **`started_at`** — ISO 8601 timestamp of session open
- **`closed_at`** — ISO 8601 timestamp of session close (null if still open)
- **`note_count`** — number of notes created during the session
- **`summary`** — the summary provided at `session_close` (if recorded)
- **`note_ids`** — list of content IDs created or linked during the session

Use this resource to quickly scan whether any recent session is topically
relevant before running the heavier `recall_topic` query.

## recall_topic output

`recall_topic(query="<topic>")` searches session log entries for sessions
with matching topic strings or log content. Returns:

- **`sessions`** — list of matching sessions, each with:
  - `session_id`, `topic`, `started_at`, `relevance_score`
  - `note_ids` — IDs of notes created in this session
  - `matched_entries` — log entry fragments that matched the query
- **`total_matched`** — count of matching sessions found

"Relevance" in this context means: the session topic or logged notes contain
content matching the query. Higher `relevance_score` means stronger match.

Sessions are returned sorted by `relevance_score` descending — the most
topically relevant session is first, regardless of recency.

## Selecting notes to fetch

From the matching sessions, select notes for `get_document` using this priority:

- **Highest relevance_score sessions first** — most topically relevant
- **Most recently modified notes** — prefer recently updated content
- **Limit to 3–5 notes** — fetch enough to rebuild context without
  overloading the context window

Do not fetch all notes from all matching sessions. The goal is context, not
completeness — select the notes most likely to represent the prior session's
key findings.

## Continuation pattern

Session topic naming convention with " — continued" suffix:

- `session_start(topic="neural networks — continued")`
- Creates a session lineage traceable by `recall_topic`
- Future recall queries on "neural networks" will find both the original
  and the continuation sessions

The suffix is not required by the API — it is a naming convention that makes
lineage visible in the `ztlctl://sessions/recent` resource and in topic matching.
Consistent use of this pattern builds a queryable session history over time.

## Empty results handling

**No prior sessions found (recall_topic returns empty):** The topic is new —
no session history exists. Report to the user:
"No prior sessions found on '<topic>'. This appears to be a new topic for your
vault. Use `ztl:session` to start fresh."
Do not call `session_start` — return control to the user to choose their path.

**Sessions found but note_ids are empty:** The matching sessions logged the
topic but created no notes. Skip `get_document` calls. Report what the session
summaries say (from `summary` field) as prior context.

**Sessions found but all notes are archived:** `get_document` may return
archived content. Report the archived note titles as prior context but note
that they are archived — the user may want to unarchive key ones before continuing.
