---
name: session-workflow
description: >
  Use when starting, running, or closing research sessions. Guides structured
  knowledge capture workflows: start → capture → synthesize → close.
version: 1.0.0
---

# Research Session Workflow

Sessions are the primary workflow unit in ztlctl. They provide structure, tracking, and enrichment for research activities.

## Session Lifecycle

```
START → CAPTURE → SYNTHESIZE → CLOSE
```

### 1. Start (`create_log` MCP tool)

Begin a session with a clear topic:
- Creates a `LOG-NNNN` entry tracking everything in this session
- Only one session can be open at a time
- All content created during the session is linked via the `session` field

**Before starting**: Check the work queue and recent activity to orient yourself.

### 2. Capture (during session)

Create content as discoveries are made:
- **Notes** for insights and ideas (`create_note`)
- **References** for external sources (`create_reference`)
- **Tasks** for follow-up actions (`create_task`)
- **Seeds** for quick ideas (`garden_seed`)

**Best practices during capture**:
- Use tags consistently (`domain/scope` format)
- Write wikilinks to connect new content to existing knowledge
- Set `topic` to match the session focus for better reweave scoring
- Check for existing content before creating duplicates (use `search` first)

### 3. Synthesize (before closing)

Review what was captured and create synthesis:
- Look for patterns across captured notes
- Create summary notes connecting related captures
- Run reweave to discover connections you missed
- Use graph tools (themes, gaps) to understand how new content fits

### 4. Close (`session_close` MCP tool)

Close the session with a summary. The close triggers an enrichment pipeline:

1. **Cross-session reweave** — reweaves all notes/references created in this session
2. **Orphan sweep** — finds notes with 0 outgoing links and attempts to connect them
3. **Integrity check** — scans for broken links, orphan edges, missing files
4. **Graph materialization** — persists PageRank, betweenness, cluster IDs

**Always provide a summary** when closing — it becomes part of the session record.

## Pre-Close Checklist

Before closing a session, verify:

1. **Knowledge extraction** — Were insights captured as notes?
2. **Resource capture** — Were external sources saved as references?
3. **Decision recording** — Were choices documented (decision subtype)?
4. **Task tracking** — Were follow-ups captured as tasks?
5. **Connections made** — Were new items linked to existing knowledge?

See `references/session-checklist.md` for the full checklist.
See `references/enrichment.md` for details on the enrichment pipeline.
