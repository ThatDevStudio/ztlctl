---
name: decision-support
description: >
  Use when the user wants to evaluate options, assemble decision context, get a
  structured briefing before deciding, or understand what their vault says about
  a decision. Activates on "help me decide X", "decision context for X", "what
  do my notes say about X decision", "decision briefing", or "evaluate options".
version: 1.0.0
disable-model-invocation: true
---

# Decision-Support Assembly

Assemble a structured decision briefing from multiple vault sources: prior
decisions, active tasks, polaris priorities, and supporting/conflicting notes.
This skill is read-only by default — it presents context for the user to decide,
never records a decision without explicit request.

## Iron Laws

**Read-only by default.** The briefing pipeline makes no vault writes. A decision
note is created only if the user explicitly requests it after reviewing the
briefing.

**Check `result.success` after every MCP call.** If `decision_support` or
`topic_packet` fails, stop and surface the error — a partial briefing is worse
than no briefing.

## Workflow

1. **`decision_support(topic="<topic>")`** — aggregate relevant decisions, open
   tasks, and references from the vault scoped to the topic. This is the
   foundation of the briefing.

2. **Read `ztlctl://decision-queue`** — load recent decisions plus the active
   work queue. Surfaces what decisions have already been made and what tasks are
   in flight.

3. **Read `ztlctl://polaris`** — load the vault's current mission, ordered
   priorities, and decision principles.

4. **`check_alignment(decision="<proposed decision>")`** — advisory polaris
   check. Returns `relevant_priorities` and alignment reasoning. This never
   blocks — record the result and proceed.

5. **`topic_packet(topic="<topic>", mode="decision")`** — decision-mode packet
   with supporting and conflicting note links, related decisions, and open
   questions on the topic.

6. **Synthesize and present structured briefing:**
   - **Prior decisions** — from steps 1 and 2: what has already been decided here
   - **Active context** — open tasks and in-flight work from step 2
   - **Conflicting signals** — notes in step 5 that oppose the proposed direction
   - **Polaris alignment** — from step 4: which priorities this decision serves
   - **Recommended action** — your synthesis of all inputs

## Optional decision note

Only if the user explicitly asks after reviewing the briefing:
`create_note(title="Decision: <title>", subtype="decision", body="<briefing summary>")`

Do NOT suggest this unless prompted. Do NOT auto-create decision notes.

## Distinction from ztl:align

`ztl:align` is a quick polaris pass/fail check (2 MCP calls). `ztl:decision-support`
is a comprehensive multi-source briefing (5–6 calls). Use align for "is this
on-strategy?" and decision-support for "what do I need to know before deciding?"

See `references/decision-workflow.md` for decision_support output fields,
decision-queue resource format, and briefing structure guidance.
