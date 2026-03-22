# Project Research Summary

**Project:** ztlctl Claude Code Plugin — v4.0 Agentic Skills
**Domain:** Claude Code plugin with deep zettelkasten workflow skills wrapping an existing Python MCP server
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

ztlctl v4.0 is a Claude Code plugin upgrade, not a new Python product. The MCP server (73+ tools) already ships in v3.x. The milestone's job is to wrap those tools in production-grade Agent Skills that encode the WHY, WHEN, and SEQUENCE of multi-step zettelkasten workflows — the patterns documented in `agentic-workflows.md`, `agents.md`, `polaris.md`, and `session-recall.md`. Research confirms that skills are workflow orchestrators, not tool wrappers: the value is in encoding correct multi-step sequences, not in creating indirection around atomic MCP calls. The existing `plugin/` directory provides a working v1 skeleton (3 skills, 4 commands, 2 agents, 1 hook) to upgrade from — this is not a greenfield build.

The recommended build order is: scaffold the plugin structure correctly first (directory layout, plugin.json, hooks.json), then implement skills in MVP-to-full order (orient → session → capture → review-triage → align, then differentiators), then validate distribution end-to-end before declaring readiness. The plugin itself is a pure filesystem artifact — no new Python packages, no build step, no npm. All runtime logic runs through the already-deployed `ztlctl serve` MCP server via stdio subprocess managed by Claude Code.

The dominant risks are infrastructure-level, not feature-level: wrong directory layout (components inside `.claude-plugin/`), Python stdout pollution breaking the stdio transport, skill description overlap causing silent non-activation, skill content too long persisting in the context window throughout the session, and mismatched MCP tool names between `--plugin-dir` development and installed state. Every one of these failures is silent — the plugin appears correct while delivering nothing. The mitigation is a strict test-under-installed-state gate: no skill is considered complete until it is tested as an installed plugin, not just under `--plugin-dir`.

---

## Key Findings

### Recommended Stack

The Claude Code plugin is a pure filesystem artifact. No new Python packages, no build step, no npm. Plugin components are Markdown files (skills, commands, agents), JSON config (plugin.json, hooks.json, .mcp.json), and optional bash/Python hook scripts. All domain logic runs through the already-deployed `ztlctl serve` MCP server. The Vercel plugin (60+ skills, 3 agents, 6 commands) is the production-scale reference implementation.

**Core technologies:**
- **SKILL.md format (markdown frontmatter + body):** skill definition — `description` field is the trigger mechanism; body encodes step-by-step workflow with explicit `mcp__plugin_ztlctl_ztlctl__<action>` tool names; 500-line body limit enforced
- **hooks.json (plugin wrapper format `{"hooks": {...}}`):** hook event registration — distinct from user settings.json format; PreToolUse vault gate, SessionStart orientation, Stop session-guard
- **.mcp.json (stdio transport):** connects Claude Code to `ztlctl serve`; CWD-based vault discovery; `PYTHONUNBUFFERED=1` in env to prevent buffering stalls
- **plugin.json (.claude-plugin/ manifest):** registers name, version; only file inside `.claude-plugin/`; `skills/` auto-discovered from default location
- **marketplace.json (git-subdir source):** sparse clone of `plugin/` subdirectory for mono-repo distribution; allows PyPI and plugin to share one repo with independent versioning
- **Vercel plugin (reference template):** advanced `pathPatterns`, `bashPatterns`, `promptSignals`, `chainTo` frontmatter for precision skill triggering; use `description` field as primary trigger for v4.0, advanced fields as progressive enhancement

See `.planning/research/STACK.md` for full field reference, verified formats, hook I/O protocol, and distribution options.

### Expected Features

Ten skills researched map directly to documented ztlctl agentic workflows. Five are table stakes (users expect them to exist); five are differentiators (unique to ztlctl's capabilities). Three lower-priority skills should defer to v4.1.

**Must have (table stakes):**
- `ztl:orient` — vault orientation before any work; reads identity, polaris, assembles agent context; universal prerequisite — all other skills skip redundant reads when orient has already fired
- `ztl:session` — full session lifecycle (status check → polaris alignment → start → close with enrichment report); the primary coordination primitive in ztlctl
- `ztl:capture` — research capture workflow (search existing → ingest source → create synthesis note → auto-link); most frequent agent operation; extends Recipe 1 from agentic-workflows.md with pre-flight orientation
- `ztl:review-triage` — work queue review (list → inspect → update/archive); extends Recipe 2; checkpoint-batch pattern — generates proposed action set before any writes
- `ztl:orient-session` — recall-driven session start (load prior sessions → rebuild context → start grounded); prevents repeat work on recurring topics

**Should have (differentiators):**
- `ztl:align` — polaris-first decision gate; unique "is this on-strategy?" check before any significant action; LOW complexity; included in MVP
- `ztl:synthesize` — knowledge synthesis (search → graph gaps → topic packet → draft → approve → create); extends Recipe 3 with draft-approval interaction gate
- `ztl:review-contradictions` — contradiction review loop (detect → inspect pairs → confirm genuine conflicts); requires human judgment before every `confirm_contradiction` write; never auto-confirm
- `ztl:garden-health` — vault maintenance audit (orphans, structural gaps, bridge nodes); fan-out read pattern; autonomous audit then checkpoint before writes
- `ztl:decision-support` — decision context briefing (decision_support + polaris + check_alignment + topic_packet); autonomous read-only synthesis

**Defer to v4.1+:**
- `ztl:garden-health` — HIGH complexity; low value on fresh or small vaults
- `ztl:orient-session` — useful only after session history has accumulated; low value on new installations
- `ztl:review-contradictions` — requires `sqlite-vec` (optional dependency); error-prone on unconfigured vaults

**Anti-features (do not build):**
- Single-tool wrapper skills (`ztl:search`, `ztl:create-note`, `ztl:get`) — skills encode sequences, not atomic operations; these add friction without value
- Autonomous contradiction confirming — `confirm_contradiction` inserts permanent bidirectional graph edges; always requires human checkpoint
- Rigid time-based session templates ("daily review") — user calendar territory, not vault territory; compose existing skills ad hoc instead
- A single monolithic "do everything" skill — kills composability; degrades every invocation with 800-token overhead

See `.planning/research/FEATURES.md` for full skill specifications, MCP tool composition tables, interaction model tiers, and feature dependency graph.

### Architecture Approach

The plugin architecture is a thin orchestration layer over a fully-featured MCP server. Claude Code manages the subprocess lifecycle; the plugin provides model-invoked skills, user-invoked commands, autonomous agents, and hook scripts. All domain logic lives in `ztlctl serve` — the plugin only encodes workflow sequencing and interaction discipline. Three composition patterns cover all ten skills.

**Major components:**
1. **`plugin/.claude-plugin/plugin.json`** — manifest; only file inside `.claude-plugin/`; registers name, version, MCP config pointer
2. **`plugin/.mcp.json`** — stdio subprocess config; CWD-based vault discovery; `PYTHONUNBUFFERED=1` in env
3. **`plugin/skills/<name>/SKILL.md`** — skill workflows; three-level progressive disclosure (frontmatter triggers → body workflow → reference files loaded on demand); 500-line body limit; `disable-model-invocation: true` on all write-operation skills
4. **`plugin/commands/*.md`** — user-invoked slash commands; thin entry points that activate skill context; do not duplicate skill content
5. **`plugin/agents/*.md`** — autonomous subagents with explicit `tools` allowlist and `maxTurns` constraint; no `hooks`, `mcpServers`, or `permissionMode` fields (unsupported in plugin agents)
6. **`plugin/hooks/hooks.json`** — hook event handlers in `{"hooks": {...}}` plugin wrapper format; PreToolUse vault existence gate, SessionStart polaris orientation
7. **`plugin/hooks/scripts/`** — bash/Python hook scripts; all paths via `${CLAUDE_PLUGIN_ROOT}`; execute bit must be committed

**Three composition patterns (cover all 10 skills):**
- **Sequential (read-decide-write):** `ztl:capture`, `ztl:align`, `ztl:session` — strict step order, decision gate before any write, `result.success` check between every step
- **Fan-out (parallel reads, synthesized report):** `ztl:garden-health`, `ztl:decision-support`, `ztl:orient` — all reads in one round before synthesizing; optional conditional writes only after user confirmation
- **Loop (enumerate-inspect-act):** `ztl:review-triage`, `ztl:review-contradictions` — list → inspect → pre-loop checkpoint → bulk execute after approval; never write inside the loop without prior batch approval

See `.planning/research/ARCHITECTURE.md` for full directory layout, plugin.json schema, hook I/O protocol, anti-patterns, vault discovery contract, and the component interaction diagram.

### Critical Pitfalls

1. **Components inside `.claude-plugin/`** — all skills, agents, commands, hooks must be at plugin root; only `plugin.json` belongs in `.claude-plugin/`; failure is silent (plugin loads, all components absent). Prevention: enforce structure from first commit; run `claude plugin validate` before any skill testing.

2. **Python stdout pollution breaking stdio transport** — any `print()`, startup banner, or library that writes to stdout corrupts JSON-RPC; server disconnects with a timeout that looks like a config problem, not a logging problem. Prevention: all output to stderr; `PYTHONUNBUFFERED=1` in `.mcp.json` env; verify with `echo '{"jsonrpc":"2.0",...}' | ztlctl serve` before skill testing begins.

3. **Plugin version not bumped = stale cache** — users never see skill fixes or improvements because Claude Code caches by version string; `claude plugin update` reports "already at latest." Prevention: treat `plugin.json` version increment as a mandatory PR gate enforced by CI from day one.

4. **MCP tool names differ between `--plugin-dir` and installed state** — known Claude Code bug (#29360); `allowed-tools` wildcards are not transformed under `--plugin-dir`, causing skills to require per-use approval in production that never appeared in development. Prevention: test every skill under installed state before declaring it ready; `--plugin-dir` testing is necessary but not sufficient.

5. **Stop hook infinite loop** — a `Stop` hook using `exit 2` causes Claude to retry the stop indefinitely; session hangs and must be force-quit. Prevention: every `Stop` hook must check `stop_hook_active` field in hook input; if `true`, exit 0 unconditionally.

6. **Skill description overlap causing silent non-activation** — two skills with overlapping descriptions cause incorrect selection or no activation; the skill is installed but never fires for its intended scenarios. Prevention: review all descriptions as a set; write 5 trigger prompts and 3 non-trigger prompts per skill; unique action verbs and context markers per description.

7. **Skill content bloating context window** — every activated SKILL.md body persists in context for the entire session; multiple heavy skills accumulate and crowd out conversation history. Prevention: 500-line body limit; move reference docs to `references/` subdirectory; use `context: fork` for heavy multi-step workflows like session management.

8. **Side-effect skills auto-invoking without user intent** — write-operation skills (capture, session-start, close) can fire from ambient context matching. Prevention: `disable-model-invocation: true` in frontmatter on all skills that perform writes.

See `.planning/research/PITFALLS.md` for 20 documented pitfalls with detection/prevention, a Python/plugin boundary failure mode table, a testing strategy (development loop → installed-state gate), and a distribution checklist.

---

## Implications for Roadmap

### Phase 1: Plugin Foundation
**Rationale:** The existing `plugin/` skeleton must be upgraded to the correct v4.0 structure before any skill work begins. Wrong directory layout (Pitfall 1) is the most common plugin failure and is undetectable from the skill authoring side — all subsequent work builds on a broken scaffold. This phase also establishes the MCP integration test baseline (Pitfall 2) — no skill work should proceed until `ztlctl serve` stdio is verified to produce clean JSON-RPC.
**Delivers:** Updated `plugin.json` (version 4.0.0 with explicit `mcpServers` pointer), validated `.mcp.json` with `PYTHONUNBUFFERED=1`, `hooks.json` in plugin wrapper format with PreToolUse vault gate (`mcp-gate.sh`) and enhanced SessionStart hook (polaris output added), updated `marketplace.json` with `git-subdir` source. All passing `claude plugin validate`. MCP stdio verified clean.
**Addresses:** Pitfall 1 (directory structure), Pitfall 2 (stdout pollution), Pitfall 3 (version bump CI gate), Pitfall 8 (hook script execute bit), Pitfall 11 (env variable expansion in hooks)
**Research flag:** Standard patterns — official docs are definitive; no additional research needed

### Phase 2: MVP Skills (Table Stakes + Align)
**Rationale:** Five highest-value, lowest-complexity skills form the MVP. `ztl:orient` is the universal prerequisite and must be implemented first within this phase — it has zero writes and its polaris + context output is explicitly referenced by `ztl:session` and `ztl:capture` as skippable when already fired. `ztl:align` is included in MVP despite being classified as a differentiator because it is LOW complexity and the polaris integration is a core ztlctl identity marker that should be visible from v4.0 day one.
**Delivers:** 5 skills: `ztl:orient`, `ztl:session`, `ztl:capture`, `ztl:review-triage`, `ztl:align`. All with correct frontmatter (`disable-model-invocation: true` on write skills), 500-line body limit enforced, supporting `references/` files for complex workflows, activation tested under installed state (5 trigger prompts + 3 non-trigger prompts per skill).
**Implements:** Sequential and loop composition patterns; checkpoint-based interaction model for all write operations; `result.success` check discipline before every write step
**Avoids:** Pitfall 4 (test under installed state), Pitfall 6 (description overlap — review all 5 descriptions as a set before implementation), Pitfall 7 (context window persistence — session skill uses `context: fork`), Pitfall 16 (reimplementing server logic in skill body), Pitfall 20 (auto-invocation of write skills)
**Research flag:** Standard patterns — FEATURES.md provides complete skill specifications; no additional research needed

### Phase 3: Differentiator Skills
**Rationale:** The five differentiator skills involve greater tool composition complexity and in two cases have conditional dependencies (sqlite-vec for contradictions, accumulated session history for orient-session). Build order within this phase: `ztl:synthesize` first (extends Recipe 3, medium complexity, no optional dependencies), `ztl:decision-support` second (autonomous read-only, fan-out pattern, medium complexity), `ztl:orient-session` third (recall workflow, medium complexity), `ztl:garden-health` fourth (fan-out pattern with most tool calls, HIGH complexity), `ztl:review-contradictions` last (sqlite-vec dependency, per-pair checkpoint loop, most complex interaction model).
**Delivers:** 5 differentiator skills with full activation testing. `ztl:garden-health` uses `context: fork` to prevent context bloat. `ztl:review-contradictions` includes graceful degradation when sqlite-vec is absent. All 10 skill descriptions reviewed as a set for overlap after this phase completes.
**Implements:** Fan-out composition pattern; loop with pre-loop batch checkpoint; draft-approval interactive model for synthesize
**Avoids:** Pitfall 6 (description overlap — review all 10 descriptions together after this phase), Pitfall 7 (garden-health is highest-risk for context bloat; `context: fork` mandatory), Pitfall 9 (wrong exit code — confirm-contradiction must never auto-fire)
**Research flag:** Standard patterns — FEATURES.md specifications are complete; sqlite-vec graceful degradation follows existing ztlctl service patterns

### Phase 4: Commands, Agents, and Distribution
**Rationale:** Commands and agents build on top of working skills. Commands are thin user-invoked entry points that activate skill context — they do not duplicate skill content. Agents are autonomous subagents with constrained tool allowlists. Distribution validation (Pitfalls 3, 12, 13, 15) must occur before any public release claim. End-to-end install test on a clean machine is the gate.
**Delivers:** Updated slash commands (`/ztlctl:session`, `/ztlctl:capture`, `/ztlctl:review`, `/ztlctl:seed`, `/ztlctl:research`); new agents (`contradiction-resolver.md`, `session-orchestrator.md`; updated `knowledge-synthesizer.md`, `vault-analyst.md`); end-to-end install test on clean machine; `claude mcp list` verification post-install; Windows compatibility documented in README; plugin README updated with prerequisites (`ztlctl[mcp]`), installation steps, post-install verification.
**Implements:** Command-as-entry-point pattern; agent `tools` allowlist + `maxTurns` constraint
**Avoids:** Pitfall 12 (no path traversal outside plugin root), Pitfall 13 (plugin-MCP sync mismatch — `claude mcp list` post-install check), Pitfall 15 (Windows uvx PATH — document prerequisite), Pitfall 17 (plugin name kebab-case), Pitfall 19 (unsupported agent frontmatter fields — no `hooks`, `mcpServers`, or `permissionMode` in plugin agents)
**Research flag:** Agent frontmatter supported field list (Pitfall 19) should be verified against current Claude Code docs at implementation time — supported fields list may change across Claude Code releases

### Phase 5: Validation and Hardening
**Rationale:** All prior phases produce artifacts that can fail silently under installed state. A dedicated hardening phase running the full distribution checklist from PITFALLS.md is non-negotiable before marketplace submission. This phase also locks in the version bump CI gate established in Phase 1 and validates the complete skill activation test suite across all 10 skills.
**Delivers:** Full distribution checklist pass (all 20+ checklist items in PITFALLS.md); CI enforcement of `plugin.json` version increment on plugin-modifying PRs; complete skill activation test suite (5 trigger + 3 non-trigger prompts per skill, 10 skills total); context window budget validation (`/context` check with all skills loaded); `CHANGELOG.md` in plugin directory; `claude plugin validate` with zero warnings.
**Addresses:** All 20 pitfalls systematically; marketplace submission readiness
**Research flag:** No additional research needed — PITFALLS.md distribution checklist is comprehensive

### Phase Ordering Rationale

- Foundation before skills: a single directory layout mistake makes all skills invisible and is undetectable from the skill authoring side; fixing it after 10 skills are written risks cascading rework
- MVP skills before differentiators: `ztl:orient` is an explicit prerequisite that later skills reference by name ("if orient has already fired, skip polaris read"); shipping it first enables correct composition logic in all subsequent skills
- Skills before commands and agents: commands are entry points to skills; agents compose skills in autonomous loops; building on unvalidated skills produces compounded failures
- Distribution validation before hardening: distribution test reveals environment-specific failures (Windows PATH, plugin-MCP sync) that must be documented before the checklist pass
- Hardening last: the distribution checklist and CI gates are meaningless until there is a complete set of artifacts to check against

### Research Flags

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** official Claude Code plugin docs are definitive; existing `plugin/` skeleton provides concrete upgrade baseline; no unknowns
- **Phase 2 (MVP Skills):** FEATURES.md skill specifications are production-ready; hook and SKILL.md formats are fully verified from first-party sources
- **Phase 3 (Differentiator Skills):** specifications complete in FEATURES.md; sqlite-vec graceful degradation is established ztlctl pattern
- **Phase 5 (Hardening):** PITFALLS.md checklist is comprehensive; no unknowns

Phases needing targeted verification at implementation time:
- **Phase 4 (Agents):** Agent frontmatter supported field list (Pitfall 19) should be spot-checked against current Claude Code docs before agent files are written — the documented unsupported fields reflect current behavior but could change across releases

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All findings from first-party sources: live installed plugin source code (example-plugin, hookify, plugin-dev, skill-creator, Vercel), official Claude Code docs, existing `plugin/` directory in this repo |
| Features | HIGH | Primary sources: ztlctl docs (agentic-workflows.md, agents.md, polaris.md, session-recall.md, contradiction-detection.md, best-practices.md), direct superpowers/feature-dev plugin inspection. Skill specifications derived directly from documented workflows |
| Architecture | HIGH | Official Claude Code docs verified; existing plugin/ directory as ground truth; MCP server source code inspected (serve.py, server.py). Component interaction diagram verified against live plugin loading behavior |
| Pitfalls | HIGH (official-sourced) / MEDIUM (community-sourced) | Critical pitfalls 1-8 sourced from official docs and GitHub issues with official confirmation. Community-sourced pitfalls cross-referenced; key findings confirmed by official docs even where article URLs returned 403 |

**Overall confidence:** HIGH

### Gaps to Address

- **Advanced SKILL.md frontmatter fields** (`pathPatterns`, `bashPatterns`, `promptSignals`, `chainTo`, `validate`, `retrieval`): verified from Vercel plugin source code but undocumented in official Anthropic reference. Treat as progressive enhancement — use `description` field as primary trigger, add advanced fields only if activation rate testing in Phase 2 reveals inadequate triggering.

- **Plugin-dir vs installed-state tool naming** (Pitfall 4 / GitHub issue #29360): open Claude Code bug. The workaround (test under installed state) is documented and enforced. Monitor the issue during Phase 2 skill testing — if fixed, the installed-state testing requirement becomes less critical but remains best practice.

- **Skill context budget with 10 skills loaded**: the 2% context window budget for skill descriptions is approximately 16,000 characters. Ten skills at 150 characters each is well within budget. If description field needs longer trigger specifications for reliable activation, add a context budget check to Phase 5 validation. Currently not a risk.

- **Skill activation rates under real usage**: the FEATURES.md trigger pattern recommendations are derived from analyzed plugin patterns, not ztlctl production data. Phase 2 activation testing (5 trigger prompts per skill) will either confirm them or reveal gaps. If activation rates are low, apply advanced frontmatter fields as progressive enhancement.

---

## Sources

### Primary (HIGH confidence)
- `/Users/shparki/.claude/plugins/cache/claude-plugins-official/` — live installed plugin source: example-plugin, hookify, plugin-dev, skill-creator, Vercel (3fe23669ec5a); plugin.json schemas, SKILL.md format, hooks.json format, agent format, marketplace structure
- `https://code.claude.com/docs/en/plugins-reference` — plugin manifest schema, directory structure, `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA`
- `https://code.claude.com/docs/en/plugins` — plugin creation guide, skill structure, `--plugin-dir` testing, `/reload-plugins`
- `https://code.claude.com/docs/en/plugin-marketplaces` — marketplace.json schema, git-subdir source type
- `https://code.claude.com/docs/en/hooks` — hook events, exit codes, `stop_hook_active`, MCP tool matching
- `https://code.claude.com/docs/en/mcp` — `.mcp.json` format, stdio transport
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/plugin/` — existing v1 plugin skeleton (ground truth for upgrade)
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/src/ztlctl/mcp/server.py` — vault discovery via CWD, `create_server()` signature
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/src/ztlctl/commands/serve.py` — transport options, `vault.close()` lifecycle
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/agentic-workflows.md` — Recipe 1/2/3, session lifecycle, polaris workflow, recall workflow, contradiction review
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/agents.md` — schemas, lifecycle state machines, interaction flows, error handling
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/polaris.md` — alignment checking workflow, agent decision pattern
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/session-recall.md` — recall workflow and MCP tool contracts
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/contradiction-detection.md` — agent review loop pattern
- `/Users/shparki/Documents/Workspace/thatdev/ztlctl/docs/best-practices.md` — anti-patterns and discipline rules (.success check, session wrap, no double-reweave)

### Secondary (MEDIUM confidence)
- `https://gofastmcp.com/integrations/claude-code` — Python MCP stdio stdout pollution; confirmed by official MCP docs
- `https://dev.to/yurukusa/5-claude-code-hook-mistakes-that-silently-break-your-safety-net-58l3` — exit code mistakes, $HOME expansion, slow hooks; verified against official docs
- GitHub issue #29360 (anthropics/claude-code) — plugin-dir namespacing breaks allowed-tools; open issue
- GitHub issue #18762 (anthropics/claude-code) — plugin-MCP config mismatch causing timeout errors
- GitHub issue #15145 (anthropics/claude-code) — incorrect plugin namespacing for MCP servers
- `https://claudefa.st/blog/guide/mechanics/context-buffer-management` — skill context window persistence; verified against official docs behavior

### Tertiary (LOW confidence)
- `https://medium.com/@taki4416/...` — skill description overlap anti-pattern; 403 on verification; key findings confirmed by independent sources
- `https://medium.com/@cheparsky/...` — context accumulation, skill budget overflow; 403 on verification; consistent with official docs
- `https://pierce-lamb.medium.com/...` — directory structure mistakes, context limits; 403 on verification; key findings confirmed by official docs

---

*Research completed: 2026-03-22*
*Ready for roadmap: yes*
