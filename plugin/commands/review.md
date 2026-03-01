---
description: Review vault state, connections, and knowledge gaps
---

Review the current state of the ztlctl vault and present actionable insights.

## Instructions

1. **Gather vault overview**:
   - Read `ztlctl://overview` MCP resource for vault statistics
   - Call `list_items` with `sort=recency`, `limit=10` for recent activity
   - Call `work_queue` to see pending tasks

2. **Run graph analysis**:
   - Call `graph_themes` to identify knowledge clusters
   - Call `graph_gaps` to find structural holes
   - Call `graph_rank` with `top=10` to find the most important items

3. **Present findings** in a structured summary:

   **Vault Health**
   - Total items by type
   - Recent activity highlights

   **Knowledge Clusters**
   - List communities from themes analysis
   - Note which clusters are well-developed vs. sparse

   **Important Items**
   - Top-ranked items by PageRank
   - Items that serve as bridges between clusters

   **Gaps & Opportunities**
   - Structural holes — items that need cross-cluster connections
   - Orphan notes — items with no connections
   - Stale seeds — seed notes older than 7 days

   **Work Queue**
   - Prioritized tasks with scores

4. **Suggest actions** — based on the analysis, suggest 3-5 specific actions:
   - Notes to create for bridging gaps
   - Seeds to develop
   - Tasks to address
   - Links to add between isolated clusters

Use MCP tools exclusively — do not shell out to the ztlctl CLI.
