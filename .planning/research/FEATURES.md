# Feature Research: ztlctl Claude Code Plugin Skills

**Domain:** Claude Code plugin with deep zettelkasten workflow skills
**Researched:** 2026-03-22
**Confidence:** HIGH (ztlctl docs, agents.md, and agentic-workflows.md are primary source; superpowers/feature-dev skill structure observed directly from installed plugins)

---

## Context

This research covers the v4.0 milestone: creating a production-grade Claude Code plugin that wraps the ztlctl MCP server with deep skills encoding core vault workflows. The MCP server already exposes 73+ tools. The plugin's job is NOT to add more tools — it is to encode the knowledge-work workflows those tools enable into skills that guide agents through correct multi-step sequences.

**Key insight from existing plugin analysis (superpowers, feature-dev):** Skills are workflow encoders. They answer "how to do X with these tools" — not "what tools exist." The agent already has the tool list from MCP discovery. Skills encode the WHY, WHEN, and SEQUENCE of tool composition.

**What already exists in ztlctl that skills should wrap:**

From `agentic-workflows.md` and `agents.md`:
- Session lifecycle: `session_start` → work → `session_close` with enrichment pipeline
- Context assembly: 5-layer context payload via `agent_context`
- Research capture: `search` → `ingest_source` → `create_note` → `reweave`
- Recall loading: `ztlctl://sessions/recent` → `recall_temporal` → `recall_topic` → `get_document`
- Polaris alignment: `ztlctl://polaris` → `check_alignment` before any significant action
- Contradiction review: `ztlctl://review/contradictions` → `get_document` → `confirm_contradiction`
- Review triage: `work_queue` → `get_document` → `update_content` / `close_content`
- Knowledge synthesis: `search` → `graph_gaps` → `draft_from_topic` → `reweave`
- Garden maintenance: `vault_review` → `graph_gaps` → `graph_bridges` → targeted updates
- Decision support: `decision_support` → `check_alignment` → `create_note --subtype decision`

---

## Docs-to-Skills Mapping

Every docs page that describes a workflow is a candidate for a skill. The mapping below is direct — from page to skill.

| Docs Page | Workflow Described | Skill Name | Complexity |
|-----------|-------------------|------------|------------|
| `agentic-workflows.md` — Session Lifecycle | start → work → close with enrichment pipeline | `ztl:session` | MEDIUM |
| `agentic-workflows.md` — Polaris-aligned startup | read polaris → check alignment → start session | `ztl:start-session` | LOW |
| `agentic-workflows.md` — Recall-driven context loading | read recent sessions → recall → fetch notes → start | `ztl:recall-context` | MEDIUM |
| `agentic-workflows.md` — Contradiction review | read contradictions → inspect pairs → confirm | `ztl:review-contradictions` | MEDIUM |
| `agentic-workflows.md` — Recipe 1: Research Capture | search → create note → reweave | `ztl:capture` | LOW |
| `agentic-workflows.md` — Recipe 2: Review Triage | work-queue → inspect → update/archive | `ztl:review-triage` | MEDIUM |
| `agentic-workflows.md` — Recipe 3: Knowledge Synthesis | search → gaps → draft → reweave | `ztl:synthesize` | MEDIUM |
| `agentic-workflows.md` — Context Assembly | agent_context with layers | `ztl:orient` | LOW |
| `session-recall.md` — Full recall workflow | temporal + topic + topology recall | `ztl:recall-context` | MEDIUM |
| `polaris.md` — Alignment checking | check_alignment before decisions | `ztl:check-alignment` | LOW |
| `contradiction-detection.md` — Agent review loop | contradictions → inspect → confirm | `ztl:review-contradictions` | MEDIUM |
| `best-practices.md` — Agent workflow discipline | session wrap, success-check discipline | Built into all skills | N/A |
| `agents.md` — Session Management Flow | status check → start → work → close | `ztl:session` | MEDIUM |
| `agents.md` — Recall Flow | 5-step recall sequence | `ztl:recall-context` | MEDIUM |
| `agents.md` — Research Capture Flow | 6-step research → capture → close | `ztl:capture` | LOW |
| `mcp.md` — Discovery pattern | discover_tools → describe_tool → agent-reference | `ztl:orient` | LOW |

---

## Table Stakes Skills

Skills users expect from a ztlctl Claude Code plugin. Missing any = the plugin feels incomplete and forces agents back to raw MCP calls.

### 1. `ztl:orient` — Vault Orientation

**What it does:** Load vault context before any work begins. Reads identity, methodology, polaris priorities, and assembles a topic-focused context payload.

**Why expected:** Agents entering a vault cold have no idea what's in it, what the vault's owner cares about, or what existing content is relevant. Every agent workflow starts with orientation. Without this skill, every agent has to figure out the `ztlctl://` resource chain from scratch.

**MCP tools composed:** `ztlctl://self/identity` (resource), `ztlctl://self/methodology` (resource), `ztlctl://polaris` (resource), `agent_context`

**Trigger pattern:** "start work", "what's in the vault", "orient yourself", "load context", beginning of any session

**Workflow:**
1. Read `ztlctl://self/identity` — understand vault personality and structure
2. Read `ztlctl://polaris` — load strategic priorities (always included in Layer 1 context)
3. Call `agent_context(topic=<user-topic>, budget=8000)` — assemble 5-layer context payload
4. Report: current session state, active priorities, relevant content count

**Interaction model:** Autonomous. No user checkpoints. Returns structured context summary.

**Complexity:** LOW

---

### 2. `ztl:session` — Session Lifecycle Management

**What it does:** Manages the full arc of a bounded work session: pre-flight check → polaris alignment → start → work gate → close with enrichment report.

**Why expected:** Sessions are the primary coordination primitive in ztlctl. Every agent-driven workflow should be wrapped in a session. This skill encodes the discipline documented in `best-practices.md` and `agents.md` Session Management Flow.

**MCP tools composed:** `session_status`, `ztlctl://polaris`, `check_alignment`, `session_start`, `session_close`

**Trigger pattern:** "start a session", "begin work on X", "open a research session", "close session", "end session"

**Workflow (open path):**
1. `session_status()` — check if a session is already open; if yes, surface the active session ID and ask user to confirm close or reuse
2. Read `ztlctl://polaris` — load current priorities
3. `check_alignment(decision="Open session: {topic}")` — advisory alignment check; report relevant_priorities
4. `session_start(topic="{topic}")` — open session; return session ID
5. Read `ztlctl://self/methodology` — ensure agent knows vault's workflow conventions
6. Report: session ID, relevant polaris priorities, methodology summary

**Workflow (close path):**
1. `session_close(summary="{summary}")` — close session; receive enrichment report
2. Parse and report: reweave_count, orphan_count, integrity_issues
3. If integrity_issues > 0: surface warning with `ztlctl check check` suggestion

**Interaction model:** Checkpoint-based on open path (user confirms topic before starting). Autonomous on close path.

**Complexity:** MEDIUM

---

### 3. `ztl:capture` — Research Capture

**What it does:** Encode the research-capture workflow: orient to existing knowledge → ingest sources → create synthesis note → auto-link.

**Why expected:** Capturing knowledge is the most frequent agent operation in a zettelkasten. This directly encodes Recipe 1 from `agentic-workflows.md` with the pre-flight orientation step added.

**MCP tools composed:** `search`, `agent_context`, `ingest_source`, `create_note`, `reweave`

**Trigger pattern:** "capture this", "create a note about X", "ingest this source", "add to vault", "save this research"

**Workflow:**
1. `search(query="{topic}", limit=10)` — check what already exists; avoid duplicates
2. If active session: skip `agent_context` (already oriented); else call `agent_context(topic="{topic}", budget=4000)`
3. For each source to ingest: `ingest_source(title="{title}", content="{text}", input_kind="text", target_type="reference")` — creates `captured` reference
4. `create_note(title="{synthesis title}", tags=["{domain/scope}"], session=<session_id>)` — create synthesis note; Reweave plugin fires automatically
5. Report: created IDs, reweave_suggestions from create response, any duplicate warnings from step 1

**Anti-pattern prevented:** Agents calling `reweave` manually after each create (double-reweave). This skill relies on the Reweave plugin's auto-fire and only calls explicit `reweave` when `--no-reweave` was used.

**Interaction model:** Autonomous. Surfaces duplicate warnings as checkpoints only when step 1 finds a near-duplicate title.

**Complexity:** LOW

---

### 4. `ztl:review-triage` — Work Queue Review

**What it does:** Surface the prioritized work queue, inspect each item, update or archive as appropriate.

**Why expected:** Review cycles are table stakes for any knowledge management tool. This directly encodes Recipe 2 from `agentic-workflows.md`.

**MCP tools composed:** `work_queue`, `get_document`, `update_content`, `close_content`

**Trigger pattern:** "review my notes", "work queue", "what needs attention", "clear the backlog", "triage"

**Workflow:**
1. `work_queue()` — load prioritized queue (all actionable items)
2. For each item in queue: `get_document(content_id="{id}")` — fetch full content
3. Evaluate each item: stale? actionable? complete? orphaned?
4. For items needing updates: `update_content(content_id="{id}", changes={maturity: "budding"})` or status transition
5. For completed/irrecoverable items: `close_content(content_id="{id}")`
6. Report: items reviewed, items updated, items archived, items left in queue

**Interaction model:** Checkpoint-based. After scanning queue, present summary and ask "Should I process all, or only items with score > X?" Batch process approved items. Surface any irreversible archives for explicit confirmation.

**Complexity:** MEDIUM

---

### 5. `ztl:orient-session` — Recall-Driven Session Start

**What it does:** Before starting a new session on a recurring topic, load context from prior sessions to avoid re-doing work.

**Why expected:** Knowledge work is iterative. Agents that don't load prior session context repeat work and miss continuations. This directly encodes the Recall-driven context loading recipe from `agentic-workflows.md`.

**MCP tools composed:** `ztlctl://sessions/recent` (resource), `recall_temporal`, `recall_topic`, `get_document`, `session_start`

**Trigger pattern:** "continue work on X", "resume research", "pick up where I left off on X", "start session with context"

**Workflow:**
1. Read `ztlctl://sessions/recent` — scan last 5 sessions for relevance
2. `recall_topic(query="{topic}")` — find sessions with matching log entries
3. For relevant sessions: extract `note_ids`; call `get_document` on key notes to rebuild context
4. Summarize: "Found N prior sessions on this topic. Key notes: [list]. Last worked on: [date]."
5. `session_start(topic="{topic} — continued")` — start new session grounded in prior context
6. Report: session ID, prior context summary, relevant note IDs loaded

**Interaction model:** Checkpoint-based. Before opening the new session, present prior context summary and ask user to confirm continuation.

**Complexity:** MEDIUM

---

## Differentiator Skills

Skills that make this plugin unique. Not expected by users of generic MCP plugins, but immediately valuable when discovered.

### 6. `ztl:align` — Polaris-First Decision Gate

**What it does:** Before any significant decision, content creation, or session opening, check alignment against vault strategic priorities. Makes polaris a lived habit rather than a document that gets written once and never consulted.

**Why it's a differentiator:** No other knowledge management plugin has a first-class "is this on-strategy?" check as a skill. This directly implements the `polaris.md` agent decision workflow and the strategic audit trail pattern.

**MCP tools composed:** `ztlctl://polaris` (resource), `check_alignment`, `create_note`

**Trigger pattern:** "should I work on X", "is this aligned", "check priority", "polaris check", "before deciding"

**Workflow:**
1. Read `ztlctl://polaris` — load mission, priorities, decision principles
2. `check_alignment(decision="{proposed action}")` — get relevant_priorities and reasoning
3. If `relevant_priorities` is non-empty: "Decision aligns with [N] polaris priorities: [list]. Proceeding."
4. If `relevant_priorities` is empty: "No direct priority overlap found. Polaris priorities are: [list]. Proceed anyway? (yes/no)"
5. Optionally: `create_note(title="Decision: {title}", subtype="decision", body="Alignment checked: ...")` — create audit trail note

**Interaction model:** Checkpoint-based. Always surfaces alignment result before proceeding. User confirms on empty-overlap case.

**Complexity:** LOW

---

### 7. `ztl:synthesize` — Knowledge Synthesis

**What it does:** Consolidate scattered knowledge on a topic into a synthesis artifact, surfacing structural gaps in the process.

**Why it's a differentiator:** Synthesis is the core value of a zettelkasten — not just capturing, but connecting. This skill encodes Recipe 3 from `agentic-workflows.md`, which no raw MCP call sequence makes obvious.

**MCP tools composed:** `search`, `graph_gaps`, `topic_packet`, `draft_from_topic`, `create_note`, `reweave`

**Trigger pattern:** "synthesize X", "summarize what I know about X", "connect my notes on X", "find gaps in X", "create synthesis"

**Workflow:**
1. `search(query="{topic}", limit=20)` — survey existing content
2. `graph_gaps(top=10)` — find structural isolation in the knowledge graph
3. `topic_packet(topic="{topic}", mode="learn")` — get comprehensive topic context with gaps, bridges, stale items
4. If no mature synthesis note exists: `draft_from_topic(topic="{topic}", target="note")` — generate draft payload
5. Present draft to user for approval/modification
6. `create_note(title="{synthesis title}", body="{approved draft}", tags=["{topic}"])` — write to vault
7. Report: note ID, existing notes connected, gaps surfaced, bridge candidates

**Interaction model:** Checkpoint-based. Draft is presented for approval before writing to vault. User can modify title and key points before commit.

**Complexity:** MEDIUM

---

### 8. `ztl:review-contradictions` — Contradiction Review

**What it does:** Run the contradiction detection loop: find semantically-close conflicting notes, inspect each pair, confirm genuine contradictions as graph edges.

**Why it's a differentiator:** Contradiction management is a unique ztlctl capability with no analog in typical knowledge tools. The agent review loop in `contradiction-detection.md` is complex enough that it needs a skill to encode the correct evaluation process.

**MCP tools composed:** `ztlctl://review/contradictions` (resource), `check_contradictions`, `get_document`, `confirm_contradiction`

**Trigger pattern:** "review contradictions", "find conflicting notes", "check for inconsistencies", "contradiction check"

**Workflow:**
1. Read `ztlctl://review/contradictions` — load current candidate list
2. If no candidates: run `check_contradictions(max_pairs=20)` to generate fresh candidates
3. For each candidate pair (score > 0.5):
   a. `get_document(content_id="{note_a}")` and `get_document(content_id="{note_b}")` in parallel
   b. Evaluate: do the notes genuinely contradict each other? Check `signals` field.
   c. Present pair with verdict: "Genuine contradiction" or "False positive (compatible claims)"
4. For confirmed contradictions: `confirm_contradiction(note_a="{a}", note_b="{b}")`
5. Report: pairs reviewed, genuine contradictions confirmed, false positives dismissed

**Interaction model:** Checkpoint-based per pair. Agent proposes verdict; user confirms before `confirm_contradiction` fires. Never auto-confirm — contradictions require human judgment.

**Complexity:** MEDIUM

---

### 9. `ztl:garden-health` — Garden Maintenance

**What it does:** Audit vault health: orphan notes, structural gaps, bridge nodes at risk, stale seeds. Produces a prioritized remediation queue.

**Why it's a differentiator:** Garden health is a holistic vault operation that requires composing multiple analysis tools in the right sequence. No single MCP tool surfaces the full picture. This skill assembles the complete view.

**MCP tools composed:** `vault_review`, `graph_gaps`, `graph_bridges`, `ztlctl://garden/backlog` (resource), `ztlctl://review/dashboard` (resource), `work_queue`

**Trigger pattern:** "vault health", "garden review", "check my vault", "orphan sweep", "what's stale", "maintenance"

**Workflow:**
1. Read `ztlctl://garden/backlog` — stale seeds and orphan notes
2. Read `ztlctl://review/dashboard` — external review workbench snapshot
3. `vault_review()` — comprehensive aggregate snapshot (stale count, orphan count, maturity distribution)
4. `graph_gaps(top=10)` — structurally isolated clusters
5. `graph_bridges(top=10)` — high-value bridge nodes that, if lost, would disconnect clusters
6. Synthesize: "Vault health: X orphans, Y stale seeds, Z structural gaps. Top bridge risk: [note title]."
7. Produce prioritized action list: connect orphans → promote stale seeds → document gaps

**Interaction model:** Autonomous audit, then checkpoint. Present health summary. Ask: "Should I process orphans automatically (reweave), or review each manually?"

**Complexity:** HIGH

---

### 10. `ztl:decision-support` — Decision-Support Assembly

**What it does:** Assemble structured decision context: existing decision notes, contradictions, polaris alignment, relevant references — all scoped to a topic.

**Why it's a differentiator:** Decision support combines `decision_support`, `check_alignment`, contradiction data, and topic packets into a unified briefing. Raw tool calls don't compose these automatically.

**MCP tools composed:** `decision_support`, `ztlctl://polaris` (resource), `check_alignment`, `ztlctl://decision-queue` (resource), `topic_packet`

**Trigger pattern:** "help me decide X", "decision context for X", "what do my notes say about X decision", "decision briefing"

**Workflow:**
1. `decision_support(topic="{topic}")` — aggregate relevant decisions, tasks, references
2. Read `ztlctl://decision-queue` — recent decisions plus active work queue
3. Read `ztlctl://polaris` — current priorities
4. `check_alignment(decision="{proposed decision}")` — advisory polaris check
5. `topic_packet(topic="{topic}", mode="decision")` — decision-mode packet with supporting/conflicting links
6. Synthesize and present: prior decisions, conflicting signals, polaris alignment, recommended action

**Interaction model:** Autonomous. Returns structured briefing. No writes unless user asks to record a decision after reviewing.

**Complexity:** MEDIUM

---

## Anti-Features

Skills that seem valuable but should NOT be built.

| Anti-Feature | Why Requested | Why Problematic | What to Do Instead |
|--------------|---------------|-----------------|-------------------|
| `ztl:search` — Skill that just calls `search` | "Make searching easier" | This is a single raw MCP call. Skills should encode multi-step workflows, not wrap atomic operations. A skill that calls `search` is just friction. | Call `search` directly from MCP. Use `ztl:orient` when you need context before searching. |
| `ztl:create-note` — Skill wrapping `create_note` | "Ensure correct tagging" | A single-tool skill with validation is CLAUDE.md system prompt content, not a skill. Skills encode sequences, not validation rules. | Put tagging conventions in the skill's system prompt context. Add `domain/scope` tagging guidance to `ztl:capture`. |
| `ztl:get` — Skill wrapping `get_document` | "Always load full content" | `get_document` IS the full content call. Adding a skill around it adds no value. | Call `get_document` directly. |
| Fully autonomous contradiction confirming | "Save time in review" | `confirm_contradiction` inserts permanent bidirectional graph edges. Auto-confirming without human judgment can corrupt the knowledge graph with false positives. | Always checkpoint before `confirm_contradiction`. Never auto-confirm. |
| Rigid session templates ("daily review session", "weekly synthesis session") | "Structure my week" | Time-based triggers are user calendar territory. Rigid templates force workflows that don't match the user's actual patterns. The vault doesn't know what day it is. | Compose existing skills (orient + session + review-triage) ad hoc. Let users build their own sequences. |
| `ztl:init-vault` — Skill for initializing a vault | "Make setup easier" | Init is a one-time operation, not a recurring workflow. It doesn't need skill-level encoding — `ztlctl init` with the right flags is sufficient, and there's nothing to compose. | Document `ztlctl init` properly; don't wrap it in a skill. |
| Skills that duplicate the 3 existing recipes verbatim | "Encode the recipes as skills" | `ztlctl://recipes/research-capture`, `ztlctl://recipes/review-triage`, `ztlctl://recipes/knowledge-synthesis` are already MCP resources. Skills should extend and compose, not duplicate. | `ztl:capture` extends Recipe 1 with polaris orientation. `ztl:synthesize` extends Recipe 3 with draft-and-approve gate. `ztl:review-triage` extends Recipe 2 with batch confirmation. |
| Skills that manage plugin configuration | "Configure reweave thresholds" | Plugin config is TOML file territory. Skills shouldn't write config files. | Direct the user to `ztlctl.toml` and `configuration.md`. |
| A single "do everything" `ztl:workflow` skill | "One command to rule them all" | Monolithic skills lose the composability that makes the skill system valuable. An 800-token omnibus skill that tries to handle all cases degrades every invocation. | Keep skills scoped to one workflow pattern. Let users compose `ztl:orient` + `ztl:session` + `ztl:capture` as needed. |

---

## Skill Composition Patterns

From analyzing superpowers skills and ztlctl's agentic workflow docs, three composition patterns emerge:

### Pattern 1: Sequential — Read-Decide-Write

Used by: `ztl:capture`, `ztl:align`, `ztl:session`

```
resource_read → tool_read → decision_gate → tool_write → report
```

Steps are strictly ordered. Each step's output feeds the next. No parallelism needed. The decision gate is where checkpoints live — before any write operation.

**Implementation guidance:** Use `result.ok` check between every step. Surface `error.recovery` on failure. Never proceed to write phase if read phase fails.

---

### Pattern 2: Fan-Out — Parallel Reads, Synthesized Report

Used by: `ztl:garden-health`, `ztl:decision-support`, `ztl:orient`

```
parallel_reads → synthesis → conditional_writes
```

Multiple read-only calls run simultaneously (vault_review + graph_gaps + graph_bridges). Synthesis assembles the full picture. Optional write phase only if user confirms.

**Implementation guidance:** Call all read tools in a single round before synthesizing. Don't read one, synthesize, read another — that leaks intermediate state into the report. Fan out, then consolidate.

---

### Pattern 3: Loop — Enumerate-Inspect-Act

Used by: `ztl:review-triage`, `ztl:review-contradictions`

```
list_all → for each item: inspect → checkpoint → conditional_act → report
```

The loop pattern is the riskiest — it scales with vault size and can issue many write calls. Skills using this pattern MUST batch checkpoint: present the full proposed action set before any writes, let user approve/prune, then execute in bulk.

**Implementation guidance:** Never call `confirm_contradiction` or `close_content` in a loop without a pre-loop checkpoint. The loop generates a proposed action list; execution is a separate phase after user approval.

---

## MCP Tool Composition Reference

The 10 skills above decompose into these MCP tool/resource calls:

| MCP Surface | Used By | Read/Write |
|-------------|---------|------------|
| `ztlctl://self/identity` | `ztl:orient` | Read |
| `ztlctl://self/methodology` | `ztl:orient`, `ztl:session` | Read |
| `ztlctl://polaris` | `ztl:orient`, `ztl:session`, `ztl:align`, `ztl:decision-support` | Read |
| `ztlctl://sessions/recent` | `ztl:orient-session` | Read |
| `ztlctl://review/contradictions` | `ztl:review-contradictions` | Read |
| `ztlctl://review/dashboard` | `ztl:garden-health` | Read |
| `ztlctl://garden/backlog` | `ztl:garden-health` | Read |
| `ztlctl://decision-queue` | `ztl:decision-support` | Read |
| `session_status` | `ztl:session` | Read |
| `session_start` | `ztl:session`, `ztl:orient-session` | Write |
| `session_close` | `ztl:session` | Write |
| `check_alignment` | `ztl:align`, `ztl:session`, `ztl:decision-support` | Read |
| `agent_context` | `ztl:orient`, `ztl:capture` | Read |
| `search` | `ztl:capture`, `ztl:synthesize` | Read |
| `ingest_source` | `ztl:capture` | Write |
| `create_note` | `ztl:capture`, `ztl:synthesize` | Write |
| `reweave` | `ztl:capture`, `ztl:synthesize` | Write |
| `work_queue` | `ztl:review-triage` | Read |
| `get_document` | `ztl:review-triage`, `ztl:review-contradictions` | Read |
| `update_content` | `ztl:review-triage` | Write |
| `close_content` | `ztl:review-triage` | Write |
| `recall_temporal` | `ztl:orient-session` | Read |
| `recall_topic` | `ztl:orient-session` | Read |
| `vault_review` | `ztl:garden-health` | Read |
| `graph_gaps` | `ztl:synthesize`, `ztl:garden-health` | Read |
| `graph_bridges` | `ztl:garden-health` | Read |
| `check_contradictions` | `ztl:review-contradictions` | Read |
| `confirm_contradiction` | `ztl:review-contradictions` | Write |
| `decision_support` | `ztl:decision-support` | Read |
| `topic_packet` | `ztl:synthesize`, `ztl:decision-support` | Read |
| `draft_from_topic` | `ztl:synthesize` | Read (draft only, no vault write) |

---

## User Interaction Model

**Three tiers from observed plugin patterns (superpowers, feature-dev):**

| Tier | Pattern | Used When |
|------|---------|-----------|
| Autonomous | Skill runs to completion, reports results | Read-only workflows, orientation, analysis |
| Checkpoint-based | Skill pauses before writes, presents proposed actions, proceeds on approval | Any skill with write operations that are hard to undo |
| Interactive | Skill asks questions during execution to handle ambiguity | Synthesis (draft approval), session start (topic confirmation) |

**Recommendation for ztlctl skills:** Default to checkpoint-based for all write operations. The vault is the user's knowledge system — writes should never happen without user awareness. Fully autonomous mode is appropriate for `ztl:orient` and `ztl:garden-health` (analysis-only). Interactive mode is appropriate for `ztl:synthesize` (draft approval gate).

**Key principle from superpowers analysis:** "If a skill applies, you don't have a choice. You MUST use it." Skills should be invoked eagerly based on intent matching, not only when the user explicitly names the skill.

---

## Skill Trigger Pattern Recommendations

From analysis of superpowers and feature-dev trigger patterns, the most reliable triggers are:

| Trigger Type | Examples | Reliability |
|--------------|---------|-------------|
| Explicit intent verb | "synthesize", "capture", "orient", "triage" | HIGH — unambiguous |
| Topic + action | "start session on X", "review my notes on X" | HIGH — context-rich |
| Feeling/state | "continue work", "pick up where I left off" | MEDIUM — needs recall |
| Review request | "what needs attention", "check vault health" | MEDIUM — could route to triage OR health |
| Creation request | "create a note", "save this" | MEDIUM — should usually route to `ztl:capture` not raw `create_note` |
| Ambiguous state | "do X" with no established session | LOW — need pre-flight orientation |

**For ambiguous trigger matching:** The skill system prompt should contain a decision matrix mapping user phrases to skill names. When two skills could apply (e.g., "review my vault" → `ztl:review-triage` vs `ztl:garden-health`), the skill should ask: "Do you want to review the work queue (actionable items) or vault health (structural gaps)?"

---

## Skill Catalog Summary

| Skill Name | Category | Trigger | Complexity | Interaction | MCP Calls |
|------------|----------|---------|------------|-------------|-----------|
| `ztl:orient` | Table stakes | "orient", "load context", session start | LOW | Autonomous | 3 reads |
| `ztl:session` | Table stakes | "start session", "close session" | MEDIUM | Checkpoint | 4–6 calls |
| `ztl:capture` | Table stakes | "capture", "create note", "ingest" | LOW | Autonomous + dup warning | 3–5 calls |
| `ztl:review-triage` | Table stakes | "triage", "work queue", "what needs attention" | MEDIUM | Checkpoint-batch | 5–15 calls |
| `ztl:orient-session` | Table stakes | "continue", "resume", "pick up" | MEDIUM | Checkpoint | 4–8 calls |
| `ztl:align` | Differentiator | "should I", "is this aligned", "check priority" | LOW | Checkpoint | 2–4 calls |
| `ztl:synthesize` | Differentiator | "synthesize", "consolidate", "connect notes" | MEDIUM | Interactive (draft gate) | 5–8 calls |
| `ztl:review-contradictions` | Differentiator | "contradictions", "conflicts", "inconsistencies" | MEDIUM | Checkpoint-per-pair | 3–10+ calls |
| `ztl:garden-health` | Differentiator | "vault health", "maintenance", "garden review" | HIGH | Autonomous + checkpoint | 6–8 reads |
| `ztl:decision-support` | Differentiator | "help me decide", "decision context", "briefing" | MEDIUM | Autonomous | 5–6 calls |

---

## Feature Dependencies

```
ztl:orient
    └──enables──> ztl:session (polaris already loaded, skip re-read)
    └──enables──> ztl:capture (context already assembled)
    └──enables──> all other skills (orientation is the universal prerequisite)

ztl:session (open)
    └──requires──> ztl:orient (polaris + context loaded first)
    └──enables──> ztl:capture (session ID available for note creation)
    └──enables──> ztl:synthesize (session context loaded)

ztl:orient-session
    └──subsumes──> ztl:orient (orientation is part of recall workflow)
    └──precedes──> ztl:session (recall before starting new session)

ztl:capture
    └──composes_with──> active session (session ID passed to create_note)
    └──feeds──> ztl:review-triage (created content enters work queue)

ztl:align
    └──composes_with──> ztl:session (alignment checked before session start)
    └──composes_with──> ztl:synthesize (alignment checked before creating synthesis)

ztl:review-contradictions
    └──requires──> semantic search (sqlite-vec; graceful error if not installed)
    └──produces──> graph edges (contradicts edges in vault)

ztl:garden-health
    └──reads from──> outputs of ztl:capture, ztl:session (content those skills created)

ztl:decision-support
    └──composes_with──> ztl:align (polaris check is one step in decision-support)
    └──reads from──> ztl:session results (prior session decisions)
```

---

## MVP Skill Set

The five skills that deliver the most value for the least implementation complexity:

1. `ztl:orient` — Universal prerequisite; zero writes; unlocks all subsequent workflows
2. `ztl:session` — Encodes the core session discipline; highest usage frequency
3. `ztl:capture` — Encodes the most common agent operation; directly wraps Recipe 1
4. `ztl:review-triage` — Encodes the review cycle; directly wraps Recipe 2
5. `ztl:align` — Unique differentiator; adds polaris to every decision; low complexity

Defer to v4.1+:
- `ztl:garden-health` — High complexity; requires vault with sufficient content to be meaningful
- `ztl:orient-session` — Useful after the user has accumulated session history; low value on fresh vaults
- `ztl:review-contradictions` — Requires `sqlite-vec` (optional dependency); error-prone on unconfigured vaults

---

## Skill Authoring Constraints

From `superpowers/skills/writing-skills/SKILL.md` patterns (direct observation):

1. **Concise is key.** The skill shares the context window with everything else. Skills should be 200–500 tokens of prose, not comprehensive workflow documentation. Reference `agents.md` for schemas rather than inlining them.

2. **Degree of freedom matching.** High freedom (text instructions) for steps where multiple approaches are valid. Pseudocode for steps with a preferred pattern. Exact tool call signatures only for steps where the wrong call causes data corruption.

3. **SKILL.md format:** Name field maps to trigger matching. Description field is what Claude reads to decide whether to invoke the skill. Iron Laws (gates) go at the top. The main content is step-by-step workflow.

4. **No duplicating agents.md.** Skills reference `agents.md` by name; they do not inline the full error table, entity schemas, or lifecycle state machines. Those live in `agents.md` — the skill just says "check `.success` before proceeding" not "here is every possible error code."

5. **Always check `.success`.** Every skill that calls a write tool must include an explicit "check `result.success` before proceeding to the next step" instruction. This is the single most important discipline documented in `best-practices.md`.

---

## Sources

- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/agentic-workflows.md` — primary workflow source; Recipe 1/2/3; agent recipes for polaris, recall, contradiction
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/agents.md` — source-verified schemas, lifecycle state machines, interaction flows, error handling
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/polaris.md` — alignment checking workflow and agent decision pattern
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/session-recall.md` — recall workflow and MCP tool contracts
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/contradiction-detection.md` — agent review loop pattern
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/best-practices.md` — anti-patterns and discipline rules (`.success` check, session wrap, no double-reweave)
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/mcp.md` — tool categories, resource list, MCP surface reference
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills/` — skill structure patterns (SKILL.md format, Iron Law pattern, trigger matching, degree of freedom model)
- `~/.claude/plugins/cache/claude-plugins-official/feature-dev/61c0597779bd/commands/feature-dev.md` — checkpoint-based workflow pattern (phases, explicit user approval gates)
- `~/.claude/plugins/cache/claude-plugins-official/superpowers/5.0.5/skills/writing-skills/SKILL.md` — skill authoring best practices (concise, degrees of freedom, token cost reasoning)

---

*Feature research for: ztlctl Claude Code plugin skills (v4.0 Agentic Skills milestone)*
*Researched: 2026-03-22*
