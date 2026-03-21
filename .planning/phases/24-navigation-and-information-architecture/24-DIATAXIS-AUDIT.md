# Diataxis Audit: ztlctl Docs (v3.1 Navigation Phase)

**Date:** 2026-03-21
**Phase:** 24 — Navigation and Information Architecture
**Purpose:** Classify every existing docs page by Diataxis type to inform nav ordering and identify mixed-purpose pages requiring remediation.

---

## Summary

| Diataxis Type | Count | Pages |
|---------------|-------|-------|
| **Tutorial** | 2 | quickstart.md, tutorial.md |
| **How-to** | 6 | installation.md, obsidian.md, agentic-workflows.md, best-practices.md (primary), troubleshooting.md, development.md |
| **Reference** | 6 | commands.md, configuration.md, plugins.md, api-reference.md, mcp.md, agents.md |
| **Explanation** | 2 | concepts.md, paradigms.md |
| **Landing** | 4 | index.md, guide/index.md, dev/index.md, plugin-guide.md (mixed) |

Total pages audited: **20**

Mixed-purpose pages flagged: **3** (best-practices.md, plugin-guide.md, agentic-workflows.md)

---

## Full Classification Table

| Page | File | Diataxis Type | Primary Signal | Mixed? | Remediation (Phase 26) |
|------|------|---------------|----------------|--------|------------------------|
| Home | `index.md` | Landing | Hub of links to all three audiences; no narrative content | No | — |
| Installation | `installation.md` | How-to | Step-by-step install commands for pip/uv/brew/pipx; goal-driven | No | — |
| Quick Start | `quickstart.md` | Tutorial | Guided, follow-along experience ("Set up a knowledge vault for a focused research project"); learning by doing | No | — |
| Tutorial | `tutorial.md` | Tutorial | Extended learning path with 9 numbered steps; "This tutorial walks through..." | No | — |
| Core Concepts | `concepts.md` | Explanation | Mental models, content types, ID patterns, lifecycle states, vault structure; no task steps | No | — |
| Knowledge Paradigms | `paradigms.md` | Explanation | Conceptual framing of two-layer model; "Why ztlctl uses..." pattern; scenario walkthroughs illustrate concepts rather than guide task completion | No | Scenarios 1–3 are illustrative examples within an explanation page — acceptable. No split needed. |
| Command Reference | `commands.md` | Reference | Complete CLI command catalog with flags and defaults; information-oriented; "All available commands..." | No | — |
| Configuration | `configuration.md` | Reference | Config option catalog (`ztlctl.toml` sections, env vars); complete reference format | No | — |
| Built-in Plugins | `plugins.md` | Reference | Plugin listing and config reference (Git plugin, Reweave plugin); structured tables, config keys | Mixed | **Minor**: Contains setup walkthrough-style prose ("Setup Walkthrough" for Obsidian Starter Kit reference was in obsidian.md; plugins.md has "Prerequisites" and "What Gets Committed" — these are acceptable within a Reference page.) Flag for Phase 26 if prose grows. |
| Obsidian Starter Kit | `obsidian.md` | How-to | "This guide walks through setting up..."; setup walkthrough with step-by-step commands and expected output | No | — |
| Agentic Workflows | `agentic-workflows.md` | How-to | Recipe walkthroughs — each section is a task-oriented goal ("Capture and Synthesis Workflow", "Ingestion"); starts with `--json` examples | Mixed | **Moderate**: Page mixes How-to recipes with Reference-style coverage (MCP tool listing). Phase 26: extract Reference content (tool inventory) to `mcp.md` and keep `agentic-workflows.md` as pure How-to. |
| Best Practices | `best-practices.md` | How-to / Explanation | Primarily opinionated How-to guidance with anti-patterns ("Opinionated guidance from building and maintaining..."); includes conceptual context explaining *why* each practice applies | Mixed | **Moderate**: Split or pick primary type. Page is more How-to (patterns, anti-patterns, concrete commands) than Explanation. Phase 26: retitle H2s to task-oriented framing ("How to initialize a vault") and push conceptual context to `concepts.md` or `paradigms.md`. |
| Troubleshooting | `troubleshooting.md` | How-to | Problem-solution pairs; goal = "fix the problem"; each section is a task with a clear trigger condition | No | — |
| User Guide Index | `guide/index.md` | Landing | Section index with navigation table to sub-pages; no content | No | — |
| Developer Guide Index | `dev/index.md` | Landing | Section index with navigation table; no content | No | — |
| Contributing | `development.md` | How-to | Contributor setup walkthrough (clone → install → run tests); step-by-step task structure | No | — |
| Plugin Authoring | `plugin-guide.md` | How-to (primary) / Reference | Starts with a numbered tutorial ("Tutorial: Build Your First Plugin") then transitions to a complete Hookspec Reference catalog | Mixed | **Major**: Page serves two distinct purposes — Tutorial (build first plugin) and Reference (hookspec catalog). Phase 26: split into `plugin-tutorial.md` (Tutorial type) and keep `plugin-guide.md` as Reference. Alternatively: rename existing Tutorial section to its own page. |
| API Reference | `api-reference.md` | Reference | Auto-generated from Python source; information-oriented, complete catalog; "All signatures and docstrings reflect the current codebase" | No | — |
| MCP Server | `mcp.md` | Reference | MCP tool categories, resource list, transport config; structured tables and schemas | Mixed | **Minor**: Has setup walkthrough (Claude Desktop integration JSON). Phase 26: move setup into How-to or ensure it's clearly labeled as a short how-to section within a Reference page. |
| Agent System Manual | `agents.md` | Reference | Machine-readable system manual; capability tables, ID formats, state machines, error codes; explicitly for LLM consumers | No | — |

---

## Remediation Priority

| Page | Priority | Issue | Phase |
|------|----------|-------|-------|
| `plugin-guide.md` | High | Tutorial + Reference mixed in same page — both halves are substantial | 26 |
| `agentic-workflows.md` | Medium | How-to + Reference content mixed — MCP tool listings belong in `mcp.md` | 26 |
| `best-practices.md` | Medium | How-to + Explanation mixed — conceptual context padding each practice | 26 |
| `plugins.md` | Low | Minor Reference + setup prose mixing — acceptable for now | 26 |
| `mcp.md` | Low | Minor Reference + How-to setup mixing — acceptable for now | 26 |

---

## Nav Ordering Rationale

Based on this audit, the User Guide nav should follow Diataxis progression:
**Tutorial → Tutorial → Explanation → Explanation → Reference → Reference → [Feature pages] → Reference → How-to → How-to → How-to → How-to**

Which maps to the locked nav ordering:
1. Tutorial (quickstart.md is top-level, above User Guide)
2. Tutorial: tutorial.md
3. Explanation: concepts.md
4. Explanation: paradigms.md
5. Reference: commands.md
6. Reference: configuration.md
7. [5 v3.0 feature page slots — Phase 25]
8. Reference: plugins.md
9. How-to: obsidian.md
10. How-to: agentic-workflows.md
11. How-to/Explanation: best-practices.md
12. How-to: troubleshooting.md
