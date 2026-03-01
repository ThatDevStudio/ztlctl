---
description: Start a structured research session in the vault
argument-hint: <topic>
---

Start a structured research session in the ztlctl vault.

## Instructions

1. **Read vault context** by calling the `ztlctl://context` MCP resource to understand current vault state.

2. **Check for active sessions** — if a session is already open, inform the user and ask if they want to close it first or continue working in it.

3. **Start the session** by calling the `create_log` MCP tool with the topic provided as the argument: `$ARGUMENTS`

4. **Orient the user** by presenting:
   - The session ID created (LOG-NNNN)
   - Recent vault activity (last 5 items via `list_items` with `sort=recency`, `limit=5`)
   - Work queue items (via `work_queue`) if any exist
   - Suggested focus areas based on the topic

5. **Activate session workflow** — remind the user of the capture → synthesize → close workflow:
   - Use `/ztlctl:capture` to capture knowledge during the session
   - Use `/ztlctl:seed` for quick idea capture
   - Use `/ztlctl:review` to review vault state before closing
   - Close the session with the `session_close` MCP tool when done

Use MCP tools exclusively — do not shell out to the ztlctl CLI.
