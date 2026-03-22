---
phase: 25-new-v3-0-feature-pages
verified: 2026-03-21T00:00:00Z
status: gaps_found
score: 5/6 must-haves verified
gaps:
  - truth: "Each new page has an llms-full.txt append with accurate content"
    status: partial
    reason: "llms-full.txt entries exist for all 5 pages but two entries contain inaccurate tool names and resource URIs that do not match the actual source"
    artifacts:
      - path: "docs/llms-full.txt"
        issue: "Contradiction detection entry shows non-existent --dismiss flag and wrong resource URI ztlctl://contradictions/review (actual: ztlctl://review/contradictions)"
      - path: "docs/llms-full.txt"
        issue: "Media ingestion entry lists ingest_file, ingest_transcript, ingest_batch as MCP tools — none of these exist for media ingestion; the actual tool is ingest_media"
    missing:
      - "Correct contradiction detection entry: remove --dismiss example, fix URI to ztlctl://review/contradictions"
      - "Correct media ingestion entry: replace ingest_file/ingest_transcript/ingest_batch MCP tool table with ingest_media"
human_verification:
  - test: "Navigate to each of the 5 new pages in a rendered docs site"
    expected: "Each page renders with correct heading structure, working relative links in What's next sections, and properly rendered admonitions"
    why_human: "mkdocs build passes but rendered cross-link navigation and visual admonition rendering require browser verification"
---

# Phase 25: New v3.0 Feature Pages — Verification Report

**Phase Goal:** All five v3.0 features shipped without documentation now have standalone pages that are navigable, agent-discoverable, and cross-referenced from existing pages
**Verified:** 2026-03-21
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can find and read session-recall.md covering temporal, topic, and topology recall with CLI usage, MCP tools, and agent workflow example | VERIFIED | File exists at docs/session-recall.md with all three recall modes, `recall_temporal`/`recall_topic`/`recall_topology` tool table, `ztlctl://sessions/recent` resource, agent workflow section, and "What's next" |
| 2 | User can find and read polaris.md covering init scaffold, ztlctl://polaris MCP resource, check_alignment action, and agent alignment workflow | VERIFIED | File exists at docs/polaris.md; polaris.md.j2 scaffold shown, `ztlctl://polaris` resource documented, `check_alignment` MCP tool and `ztlctl check alignment --decision` CLI documented, agent decision workflow present |
| 3 | User can find and read contradiction-detection.md covering heuristic scoring, CAT_SEMANTIC check, confirm_contradiction, graph edges, and MCP review resource | VERIFIED | File exists at docs/contradiction-detection.md; three-signal scoring (cosine, negation density, key-points divergence) documented, `CAT_SEMANTIC (semantic analysis)` referenced, `ztlctl://review/contradictions` MCP resource documented, agent review workflow present |
| 4 | User can find and read media-ingestion.md with prominent optional-dependency callout, format coverage, ingest_media CLI/MCP, and two-phase captured-to-annotated workflow | VERIFIED | File exists at docs/media-ingestion.md; `!!! warning` for faster-whisper is second element on page (after H1 intro paragraph, before Supported formats), all 11 formats documented, `ztlctl ingest media PATH [OPTIONS]` with verified flags, two-phase section explicit |
| 5 | User can find and read methodology.md covering prose-as-title convention, title quality check severity, and garden backlog candidates | VERIFIED | File exists at docs/methodology.md; prose-as-title table with 5 good/bad examples, `info` severity documented with `structural_validation` category, `ztlctl://garden/backlog` resource mentioned with title_improvement_candidates |
| 6 | Each new page has a mkdocs.yml nav entry, llms.txt entry, and llms-full.txt append — agent discovery indexes are current | PARTIAL | mkdocs.yml: all 5 entries confirmed, positioned between Configuration and Built-in Plugins, no placeholder comments remain. llms.txt: all 5 entries present with accurate descriptions. llms-full.txt: all 5 entries present but two contain inaccurate tool names and resource URIs |

**Score:** 5/6 truths verified (truth 6 is partial)

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `docs/session-recall.md` | Session recall feature documentation | VERIFIED | 229 lines; contains recall_temporal, recall_topic, recall_topology, ztlctl://sessions/recent, agent workflow, What's next |
| `docs/polaris.md` | Polaris priorities layer documentation | VERIFIED | 219 lines; contains check_alignment, ztlctl://polaris, polaris.md.j2 scaffold, context assembly Layer 1, agent decision workflow, What's next |
| `docs/contradiction-detection.md` | Contradiction detection feature documentation | VERIFIED | 189 lines; contains check_contradictions, confirm_contradiction, CAT_SEMANTIC, ztlctl://review/contradictions, agent review workflow, What's next |
| `docs/media-ingestion.md` | Media ingestion feature documentation | VERIFIED | 206 lines; prominent !!! warning for faster-whisper, 11 formats, ingest_media, [ingest.media] config, two-phase workflow, What's next |
| `docs/methodology.md` | Methodology guidance documentation | VERIFIED | 114 lines; prose-as-title, info-severity title quality check, garden backlog candidates, methodology.md.j2 init template, What's next |
| `mkdocs.yml` | Navigation entries for all 5 new pages | VERIFIED | Lines 32–36: Session Recall, Polaris Priorities, Contradiction Detection, Media Ingestion, Methodology Guidance — no placeholder comments remain |
| `docs/llms.txt` | Agent discovery index with new page entries | VERIFIED | Lines 23–27: all 5 entries with accurate descriptions and correct URLs |
| `docs/llms-full.txt` | Full agent discovery index with new page content summaries | PARTIAL | All 5 entries present; session-recall and polaris entries are accurate; contradiction detection and media ingestion entries contain inaccurate tool names and resource URIs |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `docs/session-recall.md` | `src/ztlctl/services/recall.py` | CLI flags and MCP tool names | VERIFIED | `recall_temporal`, `recall_topic`, `recall_topology` all confirmed in recall.py lines 25, 106, 198; `ztlctl://sessions/recent` confirmed in resources.py line 74 |
| `docs/polaris.md` | `src/ztlctl/services/check.py` | MCP resource and check_alignment | VERIFIED | `check_alignment` confirmed in _check.py line 96, check.py line 351; `ztlctl://polaris` confirmed in resources.py line 33 |
| `docs/contradiction-detection.md` | `src/ztlctl/services/contradiction.py` | CLI flags and scoring details | VERIFIED | `check_contradictions` (_check.py line 133), `confirm_contradiction` (_check.py line 166), `CAT_SEMANTIC = "semantic_analysis"` (check.py line 53), `ztlctl://review/contradictions` (resources.py line 78) all confirmed |
| `docs/media-ingestion.md` | `src/ztlctl/services/ingest.py` | CLI flags and config | VERIFIED | `ingest_media` (_ingest.py line 170), `MediaIngestConfig` (config/models.py line 112), all CLI flags match `uv run ztlctl ingest media --help` exactly |
| `mkdocs.yml` | `docs/session-recall.md` | nav entry replaces placeholder | VERIFIED | Line 32: `- Session Recall: session-recall.md`; grep for `# session-recall.md` returns no results |
| `docs/llms.txt` | `docs/` | URL entries for all 5 new pages | VERIFIED | Lines 23–27 confirmed; all 5 URLs present |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| NDOC-01 | 25-01-PLAN.md | Standalone session-recall.md page covering temporal/topic/topology recall, CLI usage, MCP tools, agent workflow, config | SATISFIED | docs/session-recall.md covers all four areas; CLI flags verified against `uv run ztlctl session recall-temporal/topic/topology --help` |
| NDOC-02 | 25-01-PLAN.md | Standalone polaris.md page covering priorities layer: init scaffold, ztlctl://polaris, context assembly, check_alignment, agent decision workflows | SATISFIED | docs/polaris.md covers all five areas; `ztlctl check alignment --decision TEXT` verified against `uv run ztlctl check alignment --help` |
| NDOC-03 | 25-02-PLAN.md | Standalone contradiction-detection.md page covering check_contradictions, heuristic scoring, confirm_contradiction, graph edges, MCP review resource | SATISFIED | docs/contradiction-detection.md covers all five areas; `ztlctl://review/contradictions` URI verified in resources.py |
| NDOC-04 | 25-02-PLAN.md | Standalone media-ingestion.md page covering formats, faster-whisper transcription, ingest_media CLI/MCP, two-phase captured→annotated workflow, [ingest.media] config | SATISFIED | docs/media-ingestion.md covers all five areas; all flags verified; MediaIngestConfig fields (whisper_model, language, compute_type) confirmed in config/models.py |
| NDOC-05 | 25-03-PLAN.md | Standalone methodology.md page covering prose-as-title convention, title quality checks, garden backlog title candidates | SATISFIED | docs/methodology.md covers all three areas; info severity and structural_validation category match check.py source |

All five requirements declared across the three plans are accounted for. No orphaned requirements found in REQUIREMENTS.md for Phase 25 — the tracking table shows NDOC-01 through NDOC-05 all mapped to Phase 25 and marked Complete.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `docs/llms-full.txt` | 5023 | `--dismiss` flag shown for `ztlctl check confirm-contradiction` — this flag does not exist in the ActionDefinition or CLI | Warning | Agent using llms-full.txt to learn the contradiction CLI will issue an invalid command; standalone docs page is correct |
| `docs/llms-full.txt` | 5033 | `ztlctl://contradictions/review` resource URI — actual URI is `ztlctl://review/contradictions` | Warning | Agent reading llms-full.txt will use the wrong resource URI; standalone docs page is correct |
| `docs/llms-full.txt` | 5029–5031 | MCP tools listed as `ingest_file`, `ingest_transcript`, `ingest_batch` for media ingestion — the actual MCP tool is `ingest_media` | Warning | Agent using llms-full.txt to discover media ingestion MCP tools will not find the listed tool names; standalone docs page correctly documents `ingest_media` |

**Classification notes:**

These are Warning severity — they affect agent discovery quality but do not block users who navigate to the standalone docs pages. The standalone pages (contradiction-detection.md, media-ingestion.md) are accurate. The inaccuracies are confined to the llms-full.txt agent discovery index.

The `ingest_file` action does exist (`_ingest.py` line 101) as a separate action for plain text/markdown file ingestion — but it is not the media ingestion tool. The llms-full.txt media ingestion entry conflates file ingestion with media ingestion.

---

## Human Verification Required

### 1. Cross-reference link resolution

**Test:** Open the rendered docs site, navigate to each of the 5 new pages, and click each link in the "What's next" section.
**Expected:** All relative links (e.g., `agentic-workflows.md`, `concepts.md`, `commands.md`) resolve to existing pages with no 404s.
**Why human:** mkdocs build --strict verifies nav entries but does not check all relative links in body content.

### 2. Media ingestion page prerequisite callout prominence

**Test:** Open docs/media-ingestion.md in the rendered site and scan the visual layout.
**Expected:** The `!!! warning` faster-whisper callout appears near the top of the page (under "Prerequisites" which is the first H2 section), clearly visible before any code examples.
**Why human:** "Prominent" is a visual quality judgment requiring rendered view.

---

## Gaps Summary

One gap was found. The standalone documentation pages for all 5 features are complete, accurate, and correctly wired into mkdocs.yml navigation and llms.txt. The gap is confined to two entries in llms-full.txt — the full agent discovery index — which contain inaccurate CLI flags and MCP tool names:

1. **Contradiction detection llms-full.txt entry** (line ~5023): Shows a non-existent `--dismiss` flag for `ztlctl check confirm-contradiction` and uses the wrong MCP resource URI (`ztlctl://contradictions/review` instead of `ztlctl://review/contradictions`). The standalone docs page at docs/contradiction-detection.md is correct.

2. **Media ingestion llms-full.txt entry** (lines ~5029–5031): Lists `ingest_file`, `ingest_transcript`, and `ingest_batch` as MCP tools for media ingestion. None of these are the media ingestion tool. The actual tool is `ingest_media`. The standalone docs page at docs/media-ingestion.md correctly documents `ingest_media`.

The root cause is that the llms-full.txt entries appear to have been written from a different mental model than the ActionRegistry source (possibly from an earlier design iteration), while the standalone pages were verified against actual source and CLI output.

To close this gap: correct the two llms-full.txt entries to match the standalone docs pages and the actual source.

---

_Verified: 2026-03-21_
_Verifier: Claude (gsd-verifier)_
