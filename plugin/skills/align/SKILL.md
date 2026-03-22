---
name: align
description: >
  Use when the user asks whether a decision, action, or direction aligns with
  their priorities. Checks proposed actions against polaris strategic priorities
  and presents a structured alignment analysis.
version: 1.0.0
---

# Polaris Alignment Check

Check any proposed decision or action against the vault's strategic priorities.
Polaris is the vault's north star — this skill makes alignment checking a habit,
not an afterthought.

## Workflow

1. **Read `ztlctl://polaris`** — load the vault's mission statement, ordered
   priorities, and decision principles.

2. **`check_alignment(decision="<proposed action or decision>")`** — get
   `relevant_priorities` and the alignment reasoning from the vault's polaris
   layer.

3. **Present the result:**

   - If `relevant_priorities` is non-empty: "This decision aligns with [N]
     polaris priorities: [list priorities]. Reasoning: [alignment reasoning]."

   - If `relevant_priorities` is empty: "No direct priority overlap found.
     Current polaris priorities are: [list all]. Consider whether this is
     intentional scope expansion or a distraction."

4. **Optional decision note** (only if the user explicitly asks): Suggest
   creating an audit trail note with `subtype="decision"` to record the
   alignment result. Do NOT auto-create the note. Suggest it and wait for
   the user to confirm before using any create tool.

## When to activate

- User asks "should I work on X?"
- User asks "is this aligned with my priorities?"
- User is about to start a new initiative or direction
- User asks for a "polaris check" or "priority check"
- User presents a significant decision and has not yet consulted polaris

## Standalone design

This skill is standalone. Other skills (session, capture) may mention polaris
checks in their own workflows, but do NOT invoke `ztl:align` as a sub-skill.
Each skill handles its own polaris checks independently. This prevents
skill-chaining complexity where one skill triggers another, creating
unpredictable invocation cascades.

See `references/polaris-workflow.md` for details on polaris document structure
and the alignment algorithm.
