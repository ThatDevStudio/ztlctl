---
description: Start a structured research session in the vault
argument-hint: <topic>
---

Use the `ztl:session` skill to manage the session lifecycle with `$ARGUMENTS` as the topic.

The skill handles the full workflow: pre-flight check for an already-open session, polaris alignment, session start, and session close with enrichment pipeline reporting. Pass `$ARGUMENTS` directly — if no topic is provided, the skill will prompt for one.

Do not duplicate session lifecycle logic here — delegate entirely to the skill.
