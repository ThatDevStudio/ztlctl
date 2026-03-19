# Feature Landscape

**Domain:** Extensible plugin-based CLI tool with agentic integration (note-taking / knowledge management)
**Researched:** 2026-03-19

## Table Stakes

Features users (and plugin authors) expect. Missing = plugin system feels incomplete or agentic integration feels broken.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Plugin API versioning | Plugin authors need to know when the contract changes; SemVer on the plugin API surface is baseline for any extensible system | Low | Already using SemVer for the project; need to explicitly version the plugin API contract separately or pin it to project version |
| Plugin lifecycle hooks (pre/post on core actions) | Every extensible tool (Obsidian, pytest, webpack) provides before/after hooks on core operations; v1 already has 8 post_ hooks | Low | v1 has post_ hooks only; adding pre_ hooks (with cancellation/modification) is the gap |
| Plugin discovery and loading (entry points + local) | Standard Python plugin discovery via setuptools entry points; v1 already implements this | Done | Already implemented in PluginManager with both entry-point and local file discovery |
| Plugin error isolation | A broken plugin must never crash the host; v1 already demotes plugin failures to warnings | Done | Already implemented via try/except in PluginManager and BaseService._dispatch_event() |
| Plugin-contributed CLI commands | Plugins that cannot add commands feel incomplete; v1 has the hookspec but no evidence of CLI integration wiring | Med | register_cli_commands hookspec exists but needs verification that contributed commands actually appear in the CLI |
| Plugin-contributed MCP tools | Same as CLI; plugins must be able to surface tools to agents; v1 has the hookspec and register_tools wires them | Done | Already working: register_tools() collects plugin MCP tools and registers them on the server |
| Complete MCP tool parity with CLI | Agents that hit "you can't do X via MCP" immediately lose trust in the tool surface; every CLI command must have an MCP equivalent | High | Current gap: CLI has commands (archive, extract, supersede, upgrade, check, init, workflow) with no MCP tool equivalents |
| Structured error responses with recovery guidance | Agents need machine-readable errors with actionable recovery; v1 has COMMON_ERROR_RECOVERY but coverage is partial | Med | Extend error catalog to cover all possible failure modes; agents calling tools blindly need clear "what to do next" |
| Self-describing tool catalog (discover_tools, describe_tool) | Agents need to discover what tools exist and how to use them without external docs; v1 has this | Done | Already implemented with rich catalog entries including when_to_use, avoid_when, args_guidance |
| Event bus for cross-plugin communication | Plugins need to react to events from other plugins, not just core events; v1 has WAL-backed EventBus | Low | Already implemented; may need to formalize event schema/contracts for third-party plugins |
| Plugin configuration via vault config (ztlctl.toml) | Plugins need a sanctioned way to accept user configuration; no config-from-toml path exists for plugins today | Med | Need a `[plugins.<name>]` section in ztlctl.toml that gets passed to plugins during init |
| Deprecation warnings before breaking changes | Plugin authors need advance notice of API changes; standard practice in every plugin ecosystem (pytest, webpack, Obsidian) | Low | Add deprecation decorator/helper that warns for N versions before removal |

## Differentiators

Features that set ztlctl v2 apart from typical plugin systems. Not expected, but create significant competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Define-once action registry with auto-generated CLI + MCP surfaces | Single source of truth for every operation; eliminates the massive duplication between CLI commands and MCP tools (currently ~1500 lines of MCP wrappers duplicating CLI logic); the "Skills" pattern emerging in agentic tooling | Very High | This is the biggest architectural shift in v2. An `@action` decorator on service methods auto-generates both Click commands and MCP tools from the same function signature, metadata, and type hints |
| Custom note types with custom lifecycles via plugins | No other Zettelkasten tool lets you define new content types (e.g., "hypothesis", "experiment", "meeting-note") with their own status transitions and validation rules | High | Requires formalizing ContentModel as an extensible primitive with plugin-registered lifecycle state machines |
| Pre-action hooks with modification/cancellation | Most plugin systems only offer post-event observation; letting plugins modify inputs before an action executes or cancel the action entirely enables transformative workflows (auto-tagging, content policies, approval gates) | Med | Requires careful design: hook ordering, short-circuit semantics, input mutation contract |
| Agent orchestration recipes (defined multi-step workflows) | Agents today improvise tool sequences; providing explicit "recipes" (research-capture, review-triage, knowledge-synthesis) that agents can follow step-by-step makes agent behavior predictable and debuggable | Med | Not a protocol/SDK concern; these are documented workflow patterns that map to existing MCP tool sequences, possibly with a recipe MCP resource |
| Plugin-contributed content type rendering | Plugins that register custom note types should also control how those notes render in Rich CLI output and in MCP responses | Med | Requires a render hook or render contribution contract alongside content model registration |
| Plugin sandboxing with capability declarations | Plugins declare what they need (filesystem, network, database, git) and the host restricts access accordingly; moves beyond "trust everything" | High | Significant implementation effort; may be overkill for current user base but becomes important at scale |
| Token-budget-aware MCP responses | Agents operate under context window constraints; tools that can trim responses to fit a budget (already partially done with topic_packet budget param) are more agent-friendly | Low | Extend the budget pattern from topic_packet to other high-volume tools (list_items, search, vault_review) |
| Plugin marketplace/registry metadata | Structured plugin metadata (name, version, author, capabilities, compatibility) that enables future discovery and marketplace features | Low | Define a ztlctl-plugin.toml or pyproject.toml section convention for plugin metadata |
| Bidirectional MCP (sampling support) | MCP sampling lets the server request LLM completions through the client, enabling the tool itself to leverage AI for operations like auto-summarization or smart reweave suggestions | High | Requires MCP sampling protocol support; powerful but adds complexity and LLM dependency |

## Anti-Features

Features to explicitly NOT build. Each has been considered and rejected.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Agent SDK / agent framework integration | ztlctl is a tool, not an agent framework; MCP is the standardized integration layer; building agent SDK bindings couples the tool to specific frameworks (LangChain, CrewAI, etc.) that churn rapidly | Provide excellent MCP tools and documented orchestration recipes; let agent frameworks consume via MCP |
| Plugin GUI / visual plugin manager | ztlctl is CLI/MCP-first; Obsidian serves as the visual layer; building a plugin management UI adds maintenance burden for minimal value | `ztlctl plugin list`, `ztlctl plugin install <name>` commands; plugin management stays in the terminal |
| Runtime plugin hot-reload | Hot-reloading plugins during a session adds enormous complexity (state cleanup, re-registration, partial failures) for a CLI tool where each invocation is short-lived | Plugins load once at vault init; changes take effect on next CLI invocation |
| Plugin-to-plugin direct dependencies | Allowing plugins to declare and import from other plugins creates a dependency graph management nightmare; every plugin ecosystem that allows this (WordPress, Eclipse) regrets it | Plugins communicate via events and hooks only; shared abstractions live in the core |
| Multi-transport MCP (WebSocket, gRPC) | stdio and HTTP cover all current MCP client implementations; adding WebSocket or gRPC transports adds maintenance burden with no current demand | Keep stdio (primary) and streamable HTTP (secondary); revisit only if MCP spec mandates new transports |
| AI-powered plugin generation | Auto-generating plugins from natural language descriptions sounds appealing but produces unmaintainable code with subtle bugs | Provide excellent plugin authoring docs, a cookiecutter/template, and a plugin test harness instead |
| Read/write permission separation on MCP tools | The RudderStack "CLI for writes, MCP for reads" pattern does not apply here; ztlctl's value is that agents can create and manage content, not just read it | Keep all operations available via both CLI and MCP; use session/audit trails for accountability instead of restricting write access |

## Feature Dependencies

```
Plugin API versioning (contract stability)
  --> Plugin configuration via ztlctl.toml (plugins need config before they do anything useful)
  --> Custom note types with lifecycles (depends on stable content model API)
  --> Pre-action hooks (depends on stable action contract)

Define-once action registry
  --> Complete MCP tool parity with CLI (unified registry eliminates parity gaps by construction)
  --> Plugin-contributed CLI commands + MCP tools (plugins register actions, not CLI/MCP separately)
  --> Token-budget-aware MCP responses (budget handling lives in the action metadata)

Plugin-contributed content types
  --> Plugin-contributed content type rendering (rendering follows content registration)

Event bus formalization
  --> Plugin-to-plugin communication via events (needs typed event contracts)
```

## MVP Recommendation

Prioritize:

1. **Plugin API versioning + deprecation helpers** -- Foundation for all plugin ecosystem work. Low effort, high trust-building. Without this, any plugin API change breaks third-party plugins silently.

2. **Pre-action hooks with modification/cancellation** -- Completes the hook system (v1 only has post_ hooks). Enables the most valuable plugin use cases: auto-tagging, content policies, validation gates. Medium effort.

3. **Plugin configuration via ztlctl.toml** -- Plugins without configuration are limited to hardcoded behavior. Adds `[plugins.<name>]` TOML sections. Medium effort.

4. **Complete MCP tool parity with CLI** -- Agents cannot work around missing tools. Every CLI command needs an MCP equivalent. High effort but critical for the "agents only orchestrate" vision.

5. **Define-once action registry** -- The highest-value differentiator, but also the highest-complexity. Eliminates the ~1500 lines of MCP wrapper duplication and ensures CLI/MCP parity by construction. Should come after the plugin system is stable because it rewrites how actions are registered.

Defer:

- **Custom note types with lifecycles**: High value but high complexity; depends on stable action registry. Phase 2+ work.
- **Agent orchestration recipes**: Valuable but can be delivered as documentation before being codified as MCP resources.
- **Plugin sandboxing**: Important at scale but overkill for current small user base. Revisit when third-party plugins exist.
- **Bidirectional MCP (sampling)**: Powerful but adds LLM dependency to core tool operations; contradicts the "works fully without agentic systems" constraint.

## Sources

- [pluggy documentation](https://pluggy.readthedocs.io/) - Hook specification patterns, entry-point discovery (HIGH confidence)
- [Obsidian plugin ecosystem](https://obsidian.md/) - 1500+ community plugins, core vs community split, plugin API patterns (MEDIUM confidence)
- [AI agents need two interfaces: CLI and MCP](https://www.rudderstack.com/blog/ai-agents-cli-mcp-design-pattern/) - Unified interface design patterns (MEDIUM confidence)
- [MCP vs CLI architecture tradeoffs](https://unified.to/blog/cli_vs_mcp_architecture_tradeoffs_for_ai_agents_and_saas_applications) - Transport decision framework (MEDIUM confidence)
- [Model Context Protocol specification](https://modelcontextprotocol.io/) - MCP tools, resources, prompts, sampling (HIGH confidence)
- [Python plugin architecture patterns](https://oneuptime.com/blog/post/2026-01-30-python-plugin-systems/view) - Registry pattern, decorator-based discovery (MEDIUM confidence)
- [Semantic Versioning](https://semver.org/) - API versioning contract (HIGH confidence)
- [Agentic workflow patterns 2025-2026](https://vellum.ai/blog/agentic-workflows-emerging-architectures-and-design-patterns) - Agent orchestration, tool-use patterns (MEDIUM confidence)
- Existing ztlctl v1 codebase analysis: hookspecs.py, contracts.py, manager.py, tools.py (HIGH confidence)
