---
description: Guided knowledge capture with duplicate checking
argument-hint: [title or topic]
---

Use the `ztl:capture` skill to capture knowledge into the vault with `$ARGUMENTS` as context for what to capture.

The skill handles type detection (note, reference, task, seed), duplicate checking, metadata gathering, content creation, and post-create reweave. Pass `$ARGUMENTS` as the capture context — if no arguments provided, the skill will ask what to capture.

Do not duplicate capture workflow logic here — delegate entirely to the skill.
