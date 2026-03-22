---
title: Polaris priorities
---

# Polaris priorities

Polaris is the strategic layer of your vault — a persistent document that captures your mission, current priorities, and decision principles. Agents consult polaris at every session context assembly and whenever checking alignment before significant decisions. It is the "why" behind your knowledge work.

Unlike notes and sessions that capture what happened, polaris captures what matters. Keeping it current ensures that agents always have a stable reference for decision guidance, even across long gaps between work sessions.

## The polaris document

Polaris lives at `garden/groves/polaris.md` in your vault. It is a plain markdown file with three sections:

- **Mission** — one to three sentences describing what you are ultimately trying to accomplish
- **Current Priorities** — a numbered list of active focus areas (update as these shift)
- **Decision Principles** — bullet-point criteria that guide how you make choices

```markdown
# Polaris — my-vault

## Mission

Build a personal knowledge system that accelerates research synthesis
and produces durable, retrievable insights.

## Current Priorities

1. Deepen understanding of transformer attention mechanisms
2. Complete the graph engine documentation
3. Establish a weekly review habit

## Decision Principles

- Prioritize depth over breadth: finish one research thread before starting another
- Prefer connections: always check what existing notes relate before creating new ones
- Avoid scope creep: decline requests that don't serve the current priorities
```

Keep polaris short. The context assembler caps polaris at 500 tokens to protect the overall context budget. A focused, concise polaris is more effective than an exhaustive one.

!!! tip
    Treat polaris as a living document. Review and update it at the start of each major work period. The alignment check is only as useful as polaris is current.

## Init scaffold

Running `ztlctl init` creates `garden/groves/polaris.md` automatically from the `polaris.md.j2` template. The scaffold gives you the correct structure with placeholder comments:

```markdown
---
generated: true
vault: "my-vault"
created: 2026-03-21
---

# Polaris — my-vault

Your polaris is your north star. Update it as your priorities evolve.

## Mission

<!-- What are you ultimately trying to accomplish? Write one to three sentences. -->

## Current Priorities

1. <!-- Priority one -->
2. <!-- Priority two -->
3. <!-- Priority three -->

## Decision Principles

- <!-- Principle one: what criteria guide your decisions? -->
- <!-- Principle two: what do you consistently optimize for? -->
- <!-- Principle three: what do you consistently avoid? -->
```

Replace the placeholder comments with your actual content immediately after init. Polaris returns no useful results until you populate it.

!!! note
    If you did not use `ztlctl init`, create `garden/groves/polaris.md` manually using the structure above. The alignment check and context assembler read the file path directly — no database registration is needed.

## MCP resource

The `ztlctl://polaris` MCP resource returns the full text of your polaris file. Agents read this resource to orient themselves before planning any significant action.

```
resource: ztlctl://polaris
```

The resource returns the raw markdown content of `garden/groves/polaris.md`, or a guidance message if the file does not exist:

```
No polaris file found. Run `ztlctl init` to generate one,
or create garden/groves/polaris.md manually.
```

Reading `ztlctl://polaris` is lightweight (one file read). Agents should consume it at the start of any workflow that involves creating content, making decisions, or planning work.

## Context assembly integration

Polaris is included in **Layer 1** of the context assembler — the operational state layer that is always present, regardless of token budget pressure. This means polaris is never dropped from context, even in tight-budget scenarios.

The context assembler reads polaris when you call `session context` or `session brief`:

```bash
$ ztlctl session context
$ ztlctl session brief
```

Or via MCP:

```
tool: context
args: { "budget": 8000 }
```

**Token budget:** The context assembler reserves up to 500 tokens for polaris content. If the file exceeds 500 tokens, it is truncated with a marker:

```
[... polaris truncated to fit token budget ...]
```

This truncation is intentional — if polaris is consistently hitting the limit, it is a signal to trim the document and promote less-critical items elsewhere in the vault.

!!! warning
    Polaris content above ~2000 characters (roughly 500 tokens) will be truncated in context assembly. Keep polaris focused — three to five priorities and three to five principles is the optimal size.

## Alignment checking

The `check alignment` command evaluates a proposed decision against your polaris priorities and decision principles. It uses keyword overlap heuristics to identify which priorities are relevant, then returns a structured result.

```bash
$ ztlctl check alignment --decision "Migrate the graph engine to use NetworkX 3.4"
```

**Options:**

| Flag | Type | Required | Description |
|------|------|----------|-------------|
| `--decision TEXT` | string | yes | Description of the decision to evaluate |

**Example output:**

```json
{
  "aligned": true,
  "relevant_priorities": [
    "Deepen understanding of transformer attention mechanisms",
    "Complete the graph engine documentation"
  ],
  "reasoning": "Decision relates to 2 polaris priorities/principles.",
  "polaris_exists": true,
  "decision": "Migrate the graph engine to use NetworkX 3.4",
  "all_priorities": ["...", "...", "..."],
  "all_principles": ["...", "...", "..."]
}
```

**Important:** `aligned` is always `true`. The check is advisory — it surfaces relevant context, never blocks the decision. If no keyword overlap is found, the reasoning field explains this.

!!! note
    The alignment check works on keyword overlap between your decision text and each priority and principle line. For best results, write polaris priorities and principles using specific, domain-relevant vocabulary rather than generic phrases.

**Via MCP:**

```
tool: check_alignment
args: { "decision": "Migrate the graph engine to use NetworkX 3.4" }
```

The MCP tool name is `check_alignment` (underscore). The CLI command is `ztlctl check alignment` (space, no subcommand group needed).

## Agent decision workflow

**Scenario:** An agent is considering a significant architectural change and wants to check alignment before proceeding.

**Step 1 — Read polaris:**

```
resource: ztlctl://polaris
```

The agent reads the full polaris document to understand the vault's mission, priorities, and principles.

**Step 2 — Check alignment on the proposed decision:**

```
tool: check_alignment
args: {
  "decision": "Refactor the embedding pipeline to support configurable dimensions"
}
```

The agent receives `relevant_priorities` listing which priorities overlap with the decision, and a `reasoning` explanation.

**Step 3 — Proceed with context:**

If `relevant_priorities` is non-empty, the agent confirms the decision is on-strategy before creating notes, opening a session, or making changes. If the list is empty, the agent uses this as a signal to pause and verify whether the action is appropriate given the current polaris.

**Step 4 — Record the decision:**

```
tool: create_note
args: {
  "title": "Decision: refactor embedding pipeline for configurable dimensions",
  "subtype": "decision",
  "body": "Alignment checked: relates to priority 'Complete the graph engine documentation'."
}
```

!!! tip
    Agents should call `check_alignment` before any `create_note --subtype decision` call. This creates a lightweight strategic audit trail and keeps decision notes grounded in the current polaris.

## What's next

- [Agentic Workflows](agentic-workflows.md) — how polaris fits into agent context assembly and orchestration patterns
- [Configuration](configuration.md) — vault configuration options including context budget settings
- [Core Concepts](concepts.md) — the garden layer where polaris lives within the vault structure
