---
name: orient
description: >
  Use when entering a vault cold, starting any work, or needing to understand
  what is in the vault. Orients to vault identity, strategic priorities, and
  assembles topic-focused context. Activates on "orient", "load context",
  "what is in the vault", or "vault status".
version: 1.0.0
---

# Vault Orientation

Orient to the vault before doing any work. This skill assembles the full context
payload: identity, polaris priorities, and topic-relevant content.

## Workflow

1. **Read `ztlctl://self/identity`** — understand vault personality, owner, and
   structure. This establishes who owns the vault and what its core purpose is.

2. **Read `ztlctl://polaris`** — load strategic priorities (mission, active
   priorities, and decision principles). Polaris is Layer 1 of every context
   payload — always load it.

3. **Call `agent_context(topic="<user-topic>", budget=8000)`** — assemble the
   5-layer context payload (polaris, related notes, graph neighbors, session
   history, methodology). If no specific topic was requested, omit the topic
   parameter for general vault orientation.

4. **Report structured summary** to the user before proceeding with any work.

## What to report

After completing the workflow, surface:

- **Vault identity** — name, owner (if present in identity), and stated purpose
- **Top 3 polaris priorities** — the strategic priorities most relevant to the
  current topic
- **Related content count** — number of related notes found for the topic
- **Session status** — whether a session is currently open (name and ID if so)
- **Methodology summary** — one-liner from the vault identity describing the
  owner's working style

## When NOT to use

- If already oriented in this conversation — skip re-reading identity and polaris
  (the context is still in your window). Call `agent_context` again only if the
  topic changes significantly.
- If the user issued a specific tool call — do not pre-orient before every single
  action. Orient once per conversation entry point, not before each operation.
- If orientation data is already present — check whether you have already read
  `ztlctl://self/identity` and `ztlctl://polaris` before re-reading them.

See `references/context-assembly.md` for details on the 5-layer context payload
and budget tuning.
