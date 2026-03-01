---
description: Guided knowledge capture with duplicate checking
argument-hint: [title or topic]
---

Guide the user through capturing knowledge into the ztlctl vault. This is a structured workflow that ensures quality and avoids duplicates.

## Instructions

1. **Understand what to capture** — if `$ARGUMENTS` is provided, use it as context. Otherwise, ask the user what they want to capture.

2. **Check for duplicates** — search the vault using the `search` MCP tool with the title/topic to see if similar content already exists. If matches are found:
   - Show the existing items
   - Ask if the user wants to update an existing item, link to it, or create something new

3. **Determine content type** — based on what's being captured:
   - **Insight or idea** → `create_note` (suggest tags, topic)
   - **External source** → `create_reference` (ask for URL, classify subtype: article/tool/spec)
   - **Action item** → `create_task` (ask for priority/impact/effort)
   - **Quick seed idea** → `garden_seed` (minimal ceremony)

4. **Gather metadata**:
   - Suggest relevant tags in `domain/scope` format based on existing vault tags
   - Suggest a topic if one seems appropriate
   - For notes: ask if it should be a decision or knowledge subtype

5. **Create the content** using the appropriate MCP tool.

6. **Connect it** — after creation:
   - Run `reweave` MCP tool on the new content ID to discover connections
   - Show the reweave suggestions
   - Suggest manual wikilinks the user might want to add

Use MCP tools exclusively — do not shell out to the ztlctl CLI.
