---
name: garden-health
description: >
  Use when the user wants to maintain vault health, garden the knowledge base,
  check for orphans, find what is stale, audit structural gaps, or see a vault
  health report. Composes analysis tools into a full health picture before
  proposing any remediation.
version: 1.0.0
disable-model-invocation: true
---

# Garden Health Audit

Garden and maintain the vault by composing a full structural health picture before
proposing any remediation. This skill uses the Fan-Out pattern: run all analysis
tools in parallel, synthesize the report, then confirm with the user before any
writes.

## Iron Laws

**Audit first, act second.** Complete the full analysis (steps 1-5) before
proposing any remediation. Never suggest fixes mid-audit — the full picture
changes the priority order.

**Never remediate without confirmation.** Present the complete maintenance report
and wait for explicit user approval before any writes. Orphan reweave, maturity
promotion, and note creation are all write operations.

**Check `result.success` after every MCP call.** If any analysis tool fails,
note the failure, continue the remaining reads, and report the partial results.

## Workflow

1. **Read `ztlctl://garden/backlog`** — load stale seeds (age, last-modified)
   and orphan notes (link counts). This is the maintenance backlog candidates list.

2. **Read `ztlctl://review/dashboard`** — load the external review workbench
   snapshot: pending reviews, external sources awaiting processing.

3. **`vault_review()`** — comprehensive aggregate snapshot: total notes, stale
   count, orphan count, maturity distribution, content type breakdown. Check
   `result.success`.

4. **`graph_gaps(top=10)`** — find structurally isolated clusters with no
   inter-cluster edges. These are knowledge islands that may need bridging notes.

5. **`graph_bridges(top=10)`** — find high-value bridge nodes whose removal
   would disconnect clusters. High-risk bridge nodes deserve protection or
   redundant linking.

6. **Synthesize health report** — combine all reads into a prioritized summary:
   - Orphan count and worst offenders (0 links, old age)
   - Stale seed count and top candidates for promotion
   - Structural gap clusters (isolated groups with no cross-links)
   - Bridge nodes at risk (high bridge_score, low redundancy)
   - External review backlog (pending sources from dashboard)

7. **Present action list with confirmation gate** — propose prioritized
   remediation with scope options:
   - Connect orphans: `reweave(content_id="<id>")` for each orphan
   - Promote stale seeds: `update_content(content_id="<id>", changes={"maturity": "budding"})`
   - Document gaps: `create_note(title="<bridging topic>")` to link isolated clusters

   Ask: "Process all / connect orphans only / promote seeds only / select
   specific items?" Wait for user response before any writes.

## Distinction from ztl:review-triage

ztl:review-triage focuses on the **work queue**: actionable items (tasks, stale
notes, drafts needing updates). ztl:garden-health focuses on **structural vault
health**: orphans, gaps, bridges, and maturity staleness across the full vault.
When the user asks "what needs attention," clarify: work queue items or vault
structure?

---

See `references/garden-audit.md` for tool output schemas and remediation option
details.
