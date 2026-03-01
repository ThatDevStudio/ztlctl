---
description: Quick-capture a seed note with minimal ceremony
argument-hint: <title> [tags...]
---

Quick-capture a seed note into the ztlctl vault. Minimal friction — capture the idea before it's lost.

## Instructions

1. **Parse arguments** from `$ARGUMENTS`:
   - First argument or quoted string = note title
   - Additional arguments that look like tags (contain `/`) = tags
   - If no arguments provided, ask the user for a title

2. **Create the seed** by calling the `garden_seed` MCP tool with:
   - `title`: the note title
   - `tags`: any tags parsed from arguments (optional)
   - `topic`: infer from context if a session is active (optional)

3. **Confirm creation** — show the user:
   - The seed ID and title
   - A brief note that seeds should be developed (seed → budding → evergreen)

Keep this fast and minimal. No duplicate checking, no reweave, no follow-up questions. The point is zero-friction capture.

Use MCP tools exclusively — do not shell out to the ztlctl CLI.
