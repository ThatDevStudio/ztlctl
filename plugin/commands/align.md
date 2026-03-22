---
description: Check if a decision aligns with vault priorities
argument-hint: <decision or question>
---

Use the `ztl:align` skill to check whether `$ARGUMENTS` aligns with the vault's polaris priorities.

The skill reads the polaris resource, runs `check_alignment`, and presents a structured analysis of which priorities are relevant and why. Pass `$ARGUMENTS` as the decision or question to evaluate — the skill handles the full alignment workflow.

Do not duplicate alignment logic here — delegate entirely to the skill.
