---
description: Review vault health and triage actionable items
---

Use the `ztl:review-triage` skill to run a full vault health check and surface actionable items.

The skill runs vault health analysis, lists the work queue, proposes a prioritized action set, and presents a batch confirmation gate before executing any writes. No arguments needed — the skill orchestrates the full triage workflow.

Do not duplicate review logic here — delegate entirely to the skill.
