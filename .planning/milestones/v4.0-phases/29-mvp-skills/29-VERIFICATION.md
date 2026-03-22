---
phase: 29-mvp-skills
verified: 2026-03-22T05:00:00Z
status: gaps_found
score: 7/9 must-haves verified
re_verification: false
gaps:
  - truth: "orient skill surfaces recent activity, open sessions, polaris priorities, and work queue without manual tool invocation (SC1)"
    status: partial
    reason: "Orient workflow reads identity, polaris, and calls agent_context — session status is surfaced indirectly via agent_context Layer 4 (session history) but the skill never calls session_status() explicitly. SC1 specifies 'open sessions' as a top-level surface, not a payload layer detail. 'Recent activity' and 'work queue summary' are also absent from the orient workflow."
    artifacts:
      - path: "plugin/skills/orient/SKILL.md"
        issue: "No session_status() call. No work_queue summary. 'What to report' section mentions session status but no workflow step fetches it directly — agent_context returns session history summaries, not current open session ID and topic."
    missing:
      - "Explicit session_status() call in step 1 or step 4 to surface whether a session is currently open (not just session history)"
      - "Work queue summary step (work_queue() or reference to it) if orient is intended to give a full vault status overview per SC1"
  - truth: "review-triage skill surfaces integrity issues per SC4"
    status: failed
    reason: "SC4 states review-triage must 'surface integrity issues, work queue priorities, and garden backlog.' The skill covers work queue priorities and garden-style items (stale seeds, orphans, drafts) but includes zero integrity checking — no check_integrity call, no integrity_issues field, no reference to structural problems. The skill is a work queue triage tool, not a vault health check."
    artifacts:
      - path: "plugin/skills/review-triage/SKILL.md"
        issue: "No check_integrity call. No integrity_issues output. Skill is purely work_queue-based triage with no health-check surface."
      - path: "plugin/skills/review-triage/references/triage-workflow.md"
        issue: "No mention of integrity checking, check_integrity, or broken links — focuses entirely on maturity/status classification."
    missing:
      - "An integrity check step (check_integrity or similar) in the workflow, or explicit documentation that integrity checking is handled by ztl:session close path only"
      - "If integrity check is intentionally absent: REQUIREMENTS.md SKIL-04 description should be updated to reflect the narrower scope of review-triage (work queue only, not vault health)"
human_verification:
  - test: "Natural language activation of ztl:orient"
    expected: "Saying 'what is the state of my vault?' or 'orient yourself' in a Claude Code session with the plugin installed causes the ztl:orient skill to activate without the user specifying any MCP tool names"
    why_human: "Skill activation from natural language depends on Claude's inference against the skill description field — cannot verify statically that the description triggers the skill correctly"
  - test: "Natural language activation of all five skills"
    expected: "Each skill activates on its trigger phrases (session=start/close, capture=capture/create/ingest, align=aligns/priorities, review-triage=review queue/triage/backlog) without triggering the wrong skill"
    why_human: "Description uniqueness can be read statically but actual disambiguation between similar phrases ('start work' vs 'start a session') requires live invocation"
  - test: "disable-model-invocation gate on session, capture, review-triage"
    expected: "Claude Code does not auto-invoke session, capture, or review-triage skills without explicit user confirmation; orient and align fire autonomously"
    why_human: "disable-model-invocation: true behavior is a Claude Code runtime behavior, not verifiable from the file content alone"
---

# Phase 29: MVP Skills Verification Report

**Phase Goal:** Five table-stakes skills are installed, correctly activated by natural language, and guide agents through the most common vault workflows without requiring knowledge of raw MCP tool names
**Verified:** 2026-03-22T05:00:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | ztl:orient skill exists and describes vault orientation workflow composing identity, polaris, and agent_context | VERIFIED | plugin/skills/orient/SKILL.md: 55 lines, name: orient, reads ztlctl://self/identity, ztlctl://polaris, calls agent_context |
| 2 | ztl:capture skill exists with search, ingest_source, create_note and duplicate detection | VERIFIED | plugin/skills/capture/SKILL.md: 73 lines, search step 1, ingest_source step 3, create_note step 4, Iron Law "always search before creating" |
| 3 | ztl:align skill exists with polaris resource and check_alignment | VERIFIED | plugin/skills/align/SKILL.md: 56 lines, name: align, reads ztlctl://polaris, calls check_alignment, Standalone Design section |
| 4 | orient and align do NOT have disable-model-invocation: true | VERIFIED | grep returns 0 matches for disable-model-invocation in both orient and align SKILL.md files |
| 5 | capture HAS disable-model-invocation: true | VERIFIED | plugin/skills/capture/SKILL.md line 8: `disable-model-invocation: true` |
| 6 | ztl:session skill exists with dual-path detection (open/close), session_start, session_close, disable-model-invocation: true | VERIFIED | plugin/skills/session/SKILL.md: 64 lines, Open Path and Close Path sections, session_start, session_close, session_status, Path Detection section |
| 7 | ztl:review-triage skill exists with work_queue, batch confirmation, disable-model-invocation: true | VERIFIED | plugin/skills/review-triage/SKILL.md: 59 lines, work_queue, get_document, update_content, close_content, Batch Confirmation Pattern section |
| 8 | Orient skill surfaces open sessions and work queue per SC1 | PARTIAL | Orient surfaces session status in "What to report" section but does NOT call session_status() — relies on agent_context Layer 4 for session history. No work_queue summary step. SC1 requires "open sessions, polaris priorities, and work queue summary" explicitly. |
| 9 | Review-triage surfaces integrity issues per SC4 | FAILED | SC4 requires "integrity issues, work queue priorities, and garden backlog." The skill has no check_integrity call, no integrity_issues field, and no integrity workflow step. Work queue and garden-style items (stale seeds, orphans) are present; integrity check is absent. |

**Score:** 7/9 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `plugin/skills/orient/SKILL.md` | Vault orientation workflow, name: orient | VERIFIED | 55 lines, frontmatter correct, agent_context, identity, polaris present |
| `plugin/skills/orient/references/context-assembly.md` | 5-layer context payload reference | VERIFIED | 60 lines, 5-layer documentation, budget parameter docs, topic parameter docs |
| `plugin/skills/capture/SKILL.md` | Research capture, disable-model-invocation: true | VERIFIED | 73 lines, frontmatter correct, search + ingest_source + create_note, Iron Law, Anti-patterns |
| `plugin/skills/capture/references/capture-workflow.md` | Content type decision tree | VERIFIED | Content Type Decision Tree section, tagging conventions, session integration |
| `plugin/skills/align/SKILL.md` | Polaris alignment, name: align, no disable-model-invocation | VERIFIED | 56 lines, frontmatter correct, check_alignment, polaris, Standalone Design |
| `plugin/skills/align/references/polaris-workflow.md` | Polaris document structure, decision audit trail | VERIFIED | Decision Audit Trail section, polaris structure, check_alignment response fields |
| `plugin/skills/session/SKILL.md` | Session lifecycle, disable-model-invocation: true, dual-path | VERIFIED | 64 lines, Iron Laws, Open Path, Close Path, Path Detection, session_start, session_close, session_status |
| `plugin/skills/session/references/session-lifecycle.md` | Session state machine | VERIFIED | Session States section, session-linked content, pre-flight alignment |
| `plugin/skills/session/references/enrichment-report.md` | 4-stage enrichment pipeline | VERIFIED | Enrichment Pipeline section, 4 stages documented, field interpretation |
| `plugin/skills/review-triage/SKILL.md` | Work queue triage, disable-model-invocation: true, batch confirmation | VERIFIED | 59 lines, work_queue, get_document, update_content, close_content, Batch Confirmation Pattern, Iron Laws |
| `plugin/skills/review-triage/references/triage-workflow.md` | Item evaluation criteria | VERIFIED | Evaluation Criteria, Work Queue Scoring, Batch vs Individual Processing, Status Transitions |

**All 11 artifacts exist and are substantive (no stubs, no placeholder text).**

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| plugin/skills/orient/SKILL.md | agent_context MCP tool | workflow step 3 | WIRED | "Call `agent_context(topic="<user-topic>", budget=8000)`" |
| plugin/skills/capture/SKILL.md | create_note MCP tool | workflow step 4 | WIRED | "`create_note(title="<synthesis title>", tags=[...], session=...)`" |
| plugin/skills/align/SKILL.md | check_alignment MCP tool | workflow step 2 | WIRED | "`check_alignment(decision="<proposed action or decision>")`" |
| plugin/skills/session/SKILL.md | session_start and session_close MCP tools | Open Path step 4, Close Path step 2 | WIRED | Both calls present with correct parameters |
| plugin/skills/review-triage/SKILL.md | work_queue MCP tool | workflow step 1 | WIRED | "`work_queue()`: load the prioritized work queue" |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| SKIL-01 | 29-01-PLAN.md | ztl:orient provides vault status overview via discover_tools, session_status, and agent_context | PARTIAL | orient exists and uses agent_context. Does NOT call discover_tools or session_status explicitly. Session status surfaced indirectly via agent_context Layer 4, not as a direct call. Work queue summary absent. The FEATURES.md design (the refined spec) does not include discover_tools for orient — this is a REQUIREMENTS.md vs. FEATURES.md divergence resolved in favor of FEATURES.md. However, the SC1 observable truth is partially unmet. |
| SKIL-02 | 29-02-PLAN.md | ztl:session manages full session lifecycle with polaris alignment, capture, close with enrichment | SATISFIED | session SKILL.md covers: polaris alignment (check_alignment advisory), session_start, session_close, enrichment report parsing, dual-path detection |
| SKIL-03 | 29-01-PLAN.md | ztl:capture guides structured content creation via create_note, create_reference, create_task with reweave | SATISFIED | capture SKILL.md covers: create_note, ingest_source (creates reference), create_task, reweave (anti-pattern preventing double-reweave). REQUIREMENTS.md mentions create_reference — implementation uses ingest_source which creates a "captured" reference — functionally equivalent |
| SKIL-04 | 29-02-PLAN.md | ztl:review-triage runs vault health check and surfaces integrity issues, work queue priorities, garden backlog | PARTIAL | work queue priorities and garden-style items covered. Integrity issues absent — no check_integrity call, no integrity_issues output. |
| SKIL-05 | 29-01-PLAN.md | ztl:align evaluates decisions against polaris priorities via check_alignment | SATISFIED | align SKILL.md: reads ztlctl://polaris, calls check_alignment, presents structured alignment analysis with match/no-match handling |

### Anti-Patterns Found

No anti-patterns detected. All SKILL.md files scanned for TODO, FIXME, placeholder text, and stub patterns:

| Scan | Result |
|------|--------|
| TODO/FIXME/XXX/HACK | Zero matches across all 5 skill directories |
| Placeholder/coming soon/not implemented | Zero matches |
| Empty return stubs | Not applicable (Markdown files, not code) |

All SKILL.md files are substantive: 55–73 lines each, well under the 200-line limit, containing specific MCP tool names, concrete workflow steps, and domain-specific guidance.

### Human Verification Required

#### 1. Natural Language Activation — orient

**Test:** In an active Claude Code session with the ztlctl plugin installed, say "what is the state of my vault?" or "orient yourself" without specifying any tool names.
**Expected:** The ztl:orient skill activates, reads identity and polaris resources, calls agent_context, and returns a structured vault summary.
**Why human:** Skill activation from natural language depends on Claude's runtime inference against the description field — static analysis cannot confirm activation occurs correctly.

#### 2. Description Disambiguation — Five Skills

**Test:** Attempt phrases that could overlap: "start work" (could trigger orient or session), "create a note" (capture vs. no skill), "review my priorities" (align vs. review-triage), "close the session" (session close path).
**Expected:** Each phrase activates the correct and only the correct skill; no cross-activation occurs.
**Why human:** Description uniqueness looks correct statically (no overlapping action verbs), but actual Claude inference against similar phrases requires live testing.

#### 3. disable-model-invocation Gate

**Test:** In a Claude Code session, observe whether session, capture, and review-triage ever auto-invoke from ambient context, and whether orient and align invoke autonomously.
**Expected:** session/capture/review-triage require explicit user request before activating; orient and align can activate on contextual cues.
**Why human:** The disable-model-invocation: true behavior is a Claude Code runtime gate, not inferable from file content alone.

### Gaps Summary

Two gaps block full goal achievement against the ROADMAP.md Success Criteria:

**Gap 1 — orient incomplete for SC1.** The success criterion requires orient to surface "recent activity, open sessions, polaris priorities, and work queue" without manual tool invocation. The skill surfaces polaris priorities (direct read) and session history (via agent_context Layer 4), but does not explicitly check current session status via `session_status()`, does not report recent activity as a distinct surface, and does not include a work queue summary step. The user asking "what is the state of my vault?" would not receive an open-session ID, current session topic, or work queue depth from this skill.

**Gap 2 — review-triage incomplete for SC4.** The success criterion requires review-triage to "surface integrity issues, work queue priorities, and garden backlog." The skill covers work queue priorities and garden-style items (stale seeds, orphans, drafts needing attention) but entirely omits integrity checking. SC4's "integrity issues" surface requires a `check_integrity` call or equivalent, which is absent. This means a user asking "review vault health" will not receive any structural integrity report from this skill.

**Root cause for both gaps:** The plans (29-01, 29-02) were written against FEATURES.md (the detailed design document), which defines narrower tool compositions for orient and review-triage than REQUIREMENTS.md specifies. The plans' own must-haves are fully satisfied — the gap is between REQUIREMENTS.md/ROADMAP.md Success Criteria and the implemented scope.

**Note on SKIL-01 tool differences:** REQUIREMENTS.md specifies `discover_tools` for orient — FEATURES.md explicitly excludes it (orient is not a tool discovery skill). This divergence is not a gap; the FEATURES.md design is more authoritative for implementation details. The real gap is the missing `session_status()` and work queue step.

---

_Verified: 2026-03-22T05:00:00Z_
_Verifier: Claude (gsd-verifier)_
