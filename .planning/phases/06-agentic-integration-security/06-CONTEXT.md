# Phase 6: Agentic Integration & Security - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning
**Source:** Auto-selected defaults (--auto flag)

<domain>
## Phase Boundary

Agents can orchestrate ztlctl end-to-end without workarounds. Every ServiceResult error includes machine-readable recovery guidance. MCP resources expose multi-step orchestration recipes. The MCP tool surface supports category-based progressive disclosure so plugins don't overwhelm agents. Plugin-contributed Copier workflow templates are security-constrained (`--trust=false`). Plugins declare required capabilities and the host validates access with audit logging. This is the final phase of the v2 milestone.

</domain>

<decisions>
## Implementation Decisions

### Structured error recovery (AGNT-01)
- **Add `recovery` field to ServiceError** — a `str | None` field with machine-readable next steps. When an error occurs, the recovery field tells agents exactly what to do next (e.g., "Call search() to verify the ID exists" or "Start a session with create_log() first").
- **Extend COMMON_ERROR_RECOVERY** — the existing dict in `mcp/response.py` maps error codes to recovery strings. Extend to cover all failure modes across all services. McpResponse.from_result() automatically populates recovery from this mapping.
- **Recovery field on ServiceError, not ServiceResult** — the recovery guidance belongs with the error that needs recovering, not the result envelope.

### Orchestration recipes (AGNT-03)
- **MCP resources as structured JSON step lists** — each recipe is an MCP resource (e.g., `ztlctl://recipes/research-capture`) that returns a JSON array of step objects. Each step has: `action` (the MCP tool to call), `params` (template parameters), `description` (what this step does), `conditions` (when to skip/branch).
- **Three core recipes** — research-capture (search → create notes → link), review-triage (list work-queue → update priorities → close stale), knowledge-synthesis (search topic → analyze gaps → create synthesis note).
- **Recipes are read-only resources** — agents read the recipe and execute the steps themselves. No server-side orchestration. This keeps the tool stateless.

### Progressive tool disclosure (AGNT-04)
- **Category-based activation** — MCP tools are grouped by ActionDefinition.category. On startup, only core categories are active (discovery, creation, query, lifecycle). Agents call `discover_categories` to see all available categories and `activate_category`/`deactivate_category` to expand/contract the tool surface.
- **Plugin categories auto-register** — plugin-contributed ActionDefinitions carry their own category strings. These categories start inactive and appear in `discover_categories` for agents to activate on demand.
- **Session-scoped activation** — category state lives in the server session, not persisted. Each MCP session starts with the default active set.

### Plugin security (SECU-01, SECU-02)
- **Copier --trust=false by default** — plugin-contributed workflow templates execute with `--trust=false` (Copier parameter is `unsafe=False`). A `--force-trust` CLI flag overrides this. Templates that need hooks must be explicitly trusted.
- **Plugin capability declarations** — plugins declare required capabilities in their hookspec response: `capabilities: set[str]` with values from `{"filesystem", "network", "database", "git"}`. Host validates at load time — unneeded capabilities trigger a warning, missing declarations are noted.
- **Audit logging for plugin operations** — plugin-initiated operations (filesystem writes, git commands, network calls) are logged via structlog with plugin name and capability tag. Uses the existing telemetry infrastructure from Phase 7 (v1).

### Claude's Discretion
- **Recipe step schema** — exact JSON structure for orchestration recipe steps. Whether to use a strict schema or flexible dict.
- **Category activation mechanism** — whether activate_category returns the newly visible tools or just a success/failure signal.
- **Default active categories** — exactly which categories are active on session start. The recommendation is: discovery, creation, query, lifecycle, session (the core CRUD operations).
- **Capability validation strictness** — whether missing capability declarations are warnings or errors. Recommendation: warnings for v1 (don't break existing plugins), errors in future API versions.
- **Audit log format** — exact structlog fields for plugin operation audit entries.
- **Recovery string format** — whether recovery strings are plain text or structured (e.g., JSON with action + params). Recommendation: plain text for v1, structured in future.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Error recovery (generation source)
- `src/ztlctl/services/result.py` — ServiceResult + ServiceError (Pydantic models, frozen). ServiceError needs `recovery` field added.
- `src/ztlctl/mcp/response.py` — McpResponse + COMMON_ERROR_RECOVERY dict. Maps error codes to recovery strings.

### MCP resources (orchestration recipes target)
- `src/ztlctl/mcp/resources.py` — Hand-written MCP resources (overview, context, topic, etc.). Recipes register here.
- `src/ztlctl/mcp/prompts.py` — Hand-written MCP prompts (vault_orientation, etc.).
- `src/ztlctl/mcp/server.py` — create_server() wiring point.

### MCP generator (progressive disclosure target)
- `src/ztlctl/mcp/generator.py` — generate_tools() iterates ActionRegistry. Category-based activation filters here.
- `src/ztlctl/actions/registry.py` — ActionRegistry with list_actions(category=...) filter already exists.
- `src/ztlctl/actions/definitions.py` — ActionDefinition.category field (already present).

### Plugin system (security target)
- `src/ztlctl/plugins/manager.py` — PluginManager with discover_and_load(), API version checking, config injection.
- `src/ztlctl/plugins/hookspecs.py` — All hookspecs including Phase 5 additions (pre_action, post_action, etc.).
- `src/ztlctl/plugins/contracts.py` — Contribution dataclasses.
- `src/ztlctl/plugins/_version.py` — PLUGIN_API_VERSION, check_plugin_api_version().

### Workflow templates (Copier security target)
- `src/ztlctl/services/workflow.py` — WorkflowService with Copier integration.
- `src/ztlctl/controllers/workflow.py` — WorkflowController.

### Requirements
- `.planning/REQUIREMENTS.md` — AGNT-01, AGNT-03, AGNT-04, SECU-01, SECU-02

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `COMMON_ERROR_RECOVERY` dict in response.py: Already maps 9 error codes to recovery strings — extend to cover all codes
- `ActionRegistry.list_actions(category=...)`: Category filtering already implemented — progressive disclosure builds on this
- `McpResponse.from_result()`: Already converts ServiceResult to MCP dict — will auto-include recovery field
- `structlog` telemetry infrastructure (Phase 7 v1): Hierarchical spans, @traced decorator — audit logging uses same system
- `PluginManager.check_plugin_api_version()`: Plugin validation at load time — capability checks add to this

### Established Patterns
- **MCP resources as functions**: `register_resources()` in resources.py registers functions that return dicts — recipe resources follow same pattern
- **Frozen Pydantic models**: ServiceError is frozen — `recovery` field must have a default (None)
- **Category strings on ActionDefinition**: Already used for grouping in catalogs.py and test_parity.py — 13 categories exist

### Integration Points
- `ServiceError` in result.py: Where `recovery` field is added
- `McpResponse.from_result()`: Where recovery is injected from COMMON_ERROR_RECOVERY
- `resources.py:register_resources()`: Where orchestration recipe resources register
- `generator.py:generate_tools()`: Where category-based filtering intercepts tool registration
- `PluginManager.discover_and_load()`: Where capability validation runs
- `WorkflowService`: Where --trust=false enforcement applies to plugin templates

</code_context>

<specifics>
## Specific Ideas

- The existing `list_actions(category=...)` filter in ActionRegistry means progressive disclosure is mostly a UI concern — the generator just needs to check which categories are "active" before registering tools.
- Orchestration recipes are essentially documented best practices turned into machine-readable MCP resources. They don't need new infrastructure — just new resource registrations with structured JSON payloads.
- Recovery strings should reference actual MCP tool names (e.g., "Call `search` to verify") since agents will parse and execute them.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-agentic-integration-security*
*Context gathered: 2026-03-20 via --auto defaults*
