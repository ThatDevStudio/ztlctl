# Phase 6: Agentic Integration & Security - Research

**Researched:** 2026-03-20
**Domain:** MCP agentic integration, plugin security, structured error recovery
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Structured error recovery (AGNT-01)**
- Add `recovery` field to ServiceError — a `str | None` field with machine-readable next steps. When an error occurs, the recovery field tells agents exactly what to do next (e.g., "Call search() to verify the ID exists" or "Start a session with create_log() first").
- Extend COMMON_ERROR_RECOVERY — the existing dict in `mcp/response.py` maps error codes to recovery strings. Extend to cover all failure modes across all services. McpResponse.from_result() automatically populates recovery from this mapping.
- Recovery field on ServiceError, not ServiceResult — the recovery guidance belongs with the error that needs recovering, not the result envelope.

**Orchestration recipes (AGNT-03)**
- MCP resources as structured JSON step lists — each recipe is an MCP resource (e.g., `ztlctl://recipes/research-capture`) that returns a JSON array of step objects. Each step has: `action` (the MCP tool to call), `params` (template parameters), `description` (what this step does), `conditions` (when to skip/branch).
- Three core recipes — research-capture (search → create notes → link), review-triage (list work-queue → update priorities → close stale), knowledge-synthesis (search topic → analyze gaps → create synthesis note).
- Recipes are read-only resources — agents read the recipe and execute the steps themselves. No server-side orchestration. This keeps the tool stateless.

**Progressive tool disclosure (AGNT-04)**
- Category-based activation — MCP tools are grouped by ActionDefinition.category. On startup, only core categories are active (discovery, creation, query, lifecycle). Agents call `discover_categories` to see all available categories and `activate_category`/`deactivate_category` to expand/contract the tool surface.
- Plugin categories auto-register — plugin-contributed ActionDefinitions carry their own category strings. These categories start inactive and appear in `discover_categories` for agents to activate on demand.
- Session-scoped activation — category state lives in the server session, not persisted. Each MCP session starts with the default active set.

**Plugin security (SECU-01, SECU-02)**
- Copier --trust=false by default — plugin-contributed workflow templates execute with `--trust=false` (Copier parameter is `unsafe=False`). A `--force-trust` CLI flag overrides this. Templates that need hooks must be explicitly trusted.
- Plugin capability declarations — plugins declare required capabilities in their hookspec response: `capabilities: set[str]` with values from `{"filesystem", "network", "database", "git"}`. Host validates at load time — unneeded capabilities trigger a warning, missing declarations are noted.
- Audit logging for plugin operations — plugin-initiated operations (filesystem writes, git commands, network calls) are logged via structlog with plugin name and capability tag. Uses the existing telemetry infrastructure from Phase 7 (v1).

### Claude's Discretion
- Recipe step schema — exact JSON structure for orchestration recipe steps. Whether to use a strict schema or flexible dict.
- Category activation mechanism — whether activate_category returns the newly visible tools or just a success/failure signal.
- Default active categories — exactly which categories are active on session start. The recommendation is: discovery, creation, query, lifecycle, session (the core CRUD operations).
- Capability validation strictness — whether missing capability declarations are warnings or errors. Recommendation: warnings for v1 (don't break existing plugins), errors in future API versions.
- Audit log format — exact structlog fields for plugin operation audit entries.
- Recovery string format — whether recovery strings are plain text or structured (e.g., JSON with action + params). Recommendation: plain text for v1, structured in future.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AGNT-01 | Structured error responses with machine-readable recovery guidance — extend COMMON_ERROR_RECOVERY to cover all failure modes; every ServiceResult error includes actionable "what to do next" for agents | ServiceError frozen Pydantic model needs `recovery: str | None = None` field; McpResponse.from_result() auto-populates from COMMON_ERROR_RECOVERY dict lookup |
| AGNT-03 | Agent orchestration recipe resources — defined multi-step workflows exposed as MCP resources that agents can follow step-by-step | resources.py register_resources() pattern is the right hook; three recipe URIs follow existing ztlctl:// scheme; JSON step list schema defined below |
| AGNT-04 | Progressive tool disclosure — category-based tool activation so plugins don't overwhelm the MCP tool surface; agents can discover and activate tool categories on demand | ActionRegistry.list_actions(category=...) already exists; generate_tools() filters at registration time; session state dict tracks active categories; two new MCP tools needed: discover_categories + activate_category |
| SECU-01 | Copier `--trust=false` enforcement for plugin-contributed workflow templates — restrict template hook execution; require explicit --force-trust flag for plugin templates | WorkflowService already uses unsafe=False for built-in templates; plugin path needs separate _run_plugin_copy() that requires explicit trust=True override |
| SECU-02 | Plugin capability declarations — plugins declare what they need (filesystem, network, database, git) and the host validates access; audit logging for plugin-initiated operations | hookspecs.py needs new declare_capabilities() hookspec; PluginManager.discover_and_load() adds capability validation pass; structlog already available via configure_logging() |
</phase_requirements>

---

## Summary

Phase 6 is a targeted enhancement phase that touches four distinct subsystems: the ServiceError model, the MCP resource catalog, the MCP tool generator, and the plugin security layer. No new infrastructure is required — every change builds on existing patterns.

The heaviest lift is AGNT-01: auditing all 30+ unique error codes across 12 service files and writing recovery strings for each. COMMON_ERROR_RECOVERY already covers 9 codes; the remaining ~25 need entries. The `recovery` field then propagates automatically through McpResponse.from_result().

AGNT-04 (progressive tool disclosure) requires a small category activation state that lives in the MCP server session. The ActionRegistry already supports category filtering. The main design question is where to store active-category state per MCP session — a module-level dict keyed by some session identity, or a server-scoped state object. Since FastMCP does not expose a per-session context, a simple module-level set shared within a single server process (one server = one MCP session) is the correct approach. This matches the existing `_vault_ref` module-level pattern in generator.py.

SECU-01 and SECU-02 are additive: plugin templates need a separate code path from built-in templates (currently built-in templates already use unsafe=False correctly), and the hookspecs need a new capability-declaration spec. Audit logging uses the existing structlog infrastructure.

**Primary recommendation:** Implement in dependency order: AGNT-01 (ServiceError recovery field) → AGNT-03 (recipe resources) → AGNT-04 (progressive disclosure) → SECU-01 (plugin template trust) → SECU-02 (capability declarations + audit).

---

## Standard Stack

### Core (All Existing — No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pydantic | 2.x (installed) | ServiceError frozen model extension | Already used for all models in the project |
| pluggy | 1.x (installed) | New hookspec for capability declarations | Already the plugin dispatch mechanism |
| structlog | 23.x (installed) | Audit logging for plugin operations | Already configured in telemetry infrastructure |
| fastmcp | installed | Session-scoped category state, new tool registration | Already used by MCP server |

### No New Packages Required

This phase adds no new dependencies. All functionality is implemented using the existing stack.

**Version verification:** No new packages to verify.

---

## Architecture Patterns

### Pattern 1: Recovery Field on Frozen ServiceError

ServiceError is a frozen Pydantic model. Adding a field requires `default=None` so existing construction sites (30+ callsites) are not broken.

```python
# Source: src/ztlctl/services/result.py (current state + proposed change)
class ServiceError(BaseModel):
    model_config = {"frozen": True}

    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)
    recovery: str | None = None  # NEW: machine-readable next step for agents
```

McpResponse.from_result() must then forward the recovery field to McpError, and McpError gets the same field:

```python
# src/ztlctl/mcp/response.py — McpError model extension
class McpError(BaseModel):
    model_config = {"frozen": True}

    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)
    recovery: str | None = None  # NEW: forwarded from ServiceError or COMMON_ERROR_RECOVERY
```

`from_result()` lookup priority: ServiceError.recovery (explicit) takes precedence over COMMON_ERROR_RECOVERY[code] (fallback). This allows services to override the generic string with context-specific guidance.

```python
# from_result() update
def from_result(cls, result: ServiceResult) -> McpResponse:
    error: McpError | None = None
    if result.error is not None:
        recovery = result.error.recovery or COMMON_ERROR_RECOVERY.get(result.error.code)
        error = McpError(
            code=result.error.code,
            message=result.error.message,
            recovery=recovery,
        )
    ...
```

### Pattern 2: COMMON_ERROR_RECOVERY Extension

All unique error codes found in the codebase (from grep analysis):

**Already covered (9 codes):**
NOT_FOUND, VALIDATION_FAILED, ID_COLLISION, NO_ACTIVE_SESSION, ACTIVE_SESSION_EXISTS, INVALID_TRANSITION, EMPTY_QUERY, UNKNOWN_TYPE, NO_PATH

**Missing codes that need recovery strings (from codebase audit):**

| Code | Service | Recovery Guidance |
|------|---------|------------------|
| ALREADY_OPEN | session.py | "The session is already open. Use session_status() to inspect it or close() to end it." |
| NO_ENTRIES | session.py | "The session has no entries. Add notes or references before closing." |
| NO_HISTORY | reweave.py | "No undo history exists for this note. Call reweave() without undo to create a new suggestion." |
| NO_LINK | graph.py | "No link exists between these nodes. Use link() to create a connection first." |
| BATCH_PARTIAL | create.py | "Some items in the batch failed. Check the data.results list for per-item status." |
| BATCH_FAILED | create.py | "All batch items failed. Validate your input list and retry individual creates." |
| INIT_STEP_FAILED | init.py | "An init step failed. Check the error detail for the step name and retry init." |
| INVALID_PROFILE | init.py / workflow.py | "The profile name is not recognized. Call workflow list-profiles to see valid options." |
| VAULT_EXISTS | init.py | "A vault already exists at this path. Use a different directory or remove the existing vault." |
| NO_CONFIG | init.py | "No ztlctl.toml found. Run ztlctl init to create a vault configuration first." |
| PROFILE_NOT_FOUND | init.py / workflow.py | "The requested profile is not installed. Check available profiles with workflow list-profiles." |
| NOT_A_VAULT | workflow.py | "This directory is not a ztlctl vault. Run ztlctl init first or change to your vault directory." |
| WORKFLOW_EXISTS | workflow.py | "Workflow is already initialized. Use workflow update to modify it." |
| WORKFLOW_NOT_INITIALIZED | workflow.py | "Workflow is not initialized. Run workflow init first." |
| WORKFLOW_INIT_FAILED | workflow.py | "Copier template application failed. Check that the vault directory is writable." |
| WORKFLOW_UPDATE_FAILED | workflow.py | "Copier update failed. Try running workflow init --force to reinitialize." |
| WORKFLOW_VALIDATION_FAILED | workflow.py | "Workflow asset validation failed. Run workflow export to regenerate assets." |
| CHECK_FAILED | upgrade.py | "Schema check failed. Run ztlctl check to inspect vault integrity before upgrading." |
| BACKUP_FAILED | upgrade.py | "Backup creation failed. Ensure the vault directory is writable before upgrading." |
| MIGRATION_FAILED | upgrade.py | "Migration failed. Restore from backup with check restore and retry." |
| STAMP_FAILED | upgrade.py | "Schema stamp failed. Run ztlctl upgrade check-pending to inspect migration state." |
| INVALID_FORMAT | export.py | "Unknown export format. Use one of: markdown, indexes, dot, json." |
| INVALID_VIEWER | export.py | "Unknown viewer. Use one of: vanilla, claude, codex." |
| NO_BACKUPS | check.py | "No backups found. Run ztlctl check backup to create one." |
| SEMANTIC_UNAVAILABLE | vector.py | "Semantic search is unavailable. Install the vector extra: pip install ztlctl[vector]." |
| UNSUPPORTED_INPUT | ingest.py | "Unsupported input kind. Use text or url." |
| NO_PROVIDER | ingest.py | "No source provider found for this URL scheme. Install a plugin that supports this scheme." |

### Pattern 3: Recipe Resources (AGNT-03)

Recipes follow the same `_impl` + `register_resources()` pattern as existing resources. Each recipe is a pure data structure — no service calls, no vault access needed.

**Recipe URI scheme:** `ztlctl://recipes/{name}`

**Step schema (Claude's Discretion recommendation — structured dict):**
```python
RecipeStep = TypedDict("RecipeStep", {
    "step": int,           # Ordinal step number (1-based)
    "action": str,         # MCP tool name from ActionRegistry
    "params": dict,        # Template parameters ({content_id} = "result from step N")
    "description": str,    # Human-readable purpose of this step
    "conditions": list[str],  # When to skip or branch ("skip if step 2 returned no results")
})
```

**Three recipes to implement:**

1. `ztlctl://recipes/research-capture` — search → create notes → link
   - Step 1: search(query={topic}, limit=10)
   - Step 2: create_note(title={synthesis_title}, maturity="seed") — skip if step 1 has duplicates
   - Step 3: reweave(content_id={step_2.content_id}) — connect to found content

2. `ztlctl://recipes/review-triage` — list work-queue → update priorities → close stale
   - Step 1: work_queue() — get scored task list
   - Step 2: get_document(content_id={highest_priority_id}) — inspect top item
   - Step 3: update(content_id={content_id}, status="in_progress") — advance if ready
   - Step 4: archive(content_id={stale_id}) — close items with no recent activity

3. `ztlctl://recipes/knowledge-synthesis` — search topic → analyze gaps → create synthesis note
   - Step 1: search(query={topic}, limit=20)
   - Step 2: gaps(top=10) — find disconnected knowledge areas
   - Step 3: draft_from_topic(topic={topic}, target="note") — generate synthesis draft
   - Step 4: reweave() — connect the synthesis note

**Registration in resources.py:**
```python
# _impl function (testable without mcp)
def recipe_research_capture_impl(_vault: Any) -> dict[str, Any]:
    return {
        "name": "research-capture",
        "description": "...",
        "steps": [...],
    }

# in register_resources():
@server.resource("ztlctl://recipes/research-capture")
def recipe_research_capture_resource() -> str:
    import json
    return json.dumps(recipe_research_capture_impl(vault), indent=2)
```

Also add `ztlctl://recipes` index resource listing available recipes.

### Pattern 4: Progressive Tool Disclosure (AGNT-04)

**Session-scoped state via module-level set (matching generator.py's `_vault_ref` pattern):**

```python
# src/ztlctl/mcp/generator.py additions

# Default categories active at session start
_DEFAULT_ACTIVE_CATEGORIES: frozenset[str] = frozenset(
    {"creation", "query", "graph", "lifecycle", "session"}
)

# Session-scoped active category set (one server process = one MCP session)
_active_categories: set[str] = set(_DEFAULT_ACTIVE_CATEGORIES)


def get_active_categories() -> set[str]:
    return set(_active_categories)


def activate_category(category: str) -> bool:
    """Add category to active set. Returns True if newly activated."""
    if category not in _get_all_categories():
        return False
    _active_categories.add(category)
    return True


def deactivate_category(category: str) -> bool:
    """Remove category from active set. Returns True if was active."""
    if category in _DEFAULT_ACTIVE_CATEGORIES:
        return False  # Cannot deactivate default categories
    return _active_categories.discard(category) is None  # set.discard returns None
```

**generate_tools() modification:**
```python
def generate_tools(server: Any, vault: Any) -> None:
    set_vault(vault)
    registry = get_action_registry()
    for action in registry.list_actions():
        if action.category not in _active_categories:
            continue  # Skip inactive categories
        fn = _make_tool_fn(action, vault)
        server.tool()(fn)
    _register_plugin_tools(server, vault)
```

**Two new ActionDefinitions** for category management (category="discovery"):
- `discover_categories` — returns all categories with their active status and tool counts
- `activate_category` — activates a category; returns list of newly visible tool names

**Note on FastMCP and dynamic tools:** FastMCP registers tools at server creation time (in `create_server()`). Category activation after server creation does NOT automatically add tools to the running server. The correct implementation: `generate_tools()` registers only active-category tools at startup. To change the active set, a new MCP session (new server process) is needed. The `activate_category` MCP tool therefore CANNOT add tools at runtime to an already-running server — it can only report what WOULD be active.

**Resolution:** The `discover_categories` tool shows available categories and their tools. The `activate_category` tool is informational (returns tool definitions the agent can understand and potentially call if they were registered). The real mechanism for tool activation is restarting the server with a different default active set OR providing a configuration file that sets active categories at startup.

**Simpler approach (recommended by discretion guidance):** Keep all tools registered but add `discover_categories` as an informational tool and `activate_category`/`deactivate_category` as tools that maintain state for agent awareness, NOT for dynamic registration. The `generate_tools()` registers ALL tools always; progressive disclosure is a documentation/guidance concern, not a hard registration gate. Category activation tells the agent which tool surface it should use, not which tools exist on the server.

**Concrete implementation (simpler and correct):**
- All tools registered at startup (no filtering in generate_tools)
- `discover_categories` MCP tool: returns all categories, marks which are "core" vs "extended", lists tools per category
- `activate_category` / `deactivate_category`: maintain a module-level set for agent-side state tracking; return the tool names in that category
- This is the correct interpretation given FastMCP's static tool registration model

### Pattern 5: Plugin Copier Trust (SECU-01)

Built-in templates already use `unsafe=False` (confirmed by code inspection of `_run_copy()` and `_run_update()`). The SECU-01 requirement is about PLUGIN-contributed workflow templates specifically.

Currently `WorkflowModuleContribution` contributes render functions, not Copier template paths. The security concern is: if a future plugin contributes a Copier template (as a `WorkflowModuleContribution` or new contract), it must default to `unsafe=False` and require explicit `--force-trust` to override.

**Current gap:** There is no existing mechanism for plugins to contribute Copier templates. SECU-01's concrete deliverable is:
1. Document that plugin templates are blocked from using Copier's task execution (`unsafe=False` enforced)
2. Add a `--force-trust` flag to the `workflow init` and `workflow update` CLI commands that, when present, passes `unsafe=True` to Copier for plugin templates only (built-in templates remain unaffected)
3. The WorkflowService currently has no plugin-Copier path — implement the validation so if/when plugins add Copier templates, the enforcement is already in place

**Practical implementation:** Add `force_trust: bool = False` parameter to `WorkflowService.init_workflow()` and `update_workflow()`, thread it through to `_run_copy()` and `_run_update()`. Built-in templates always use `unsafe=False` regardless of `force_trust`. A separate `_run_plugin_copy()` method would use `unsafe=force_trust`. Add `--force-trust` CLI flag to workflow commands.

### Pattern 6: Plugin Capability Declarations (SECU-02)

**New hookspec in hookspecs.py:**
```python
@hookspec
def declare_capabilities(self) -> set[str] | None:
    """Return the set of capabilities this plugin requires.

    Valid values: {"filesystem", "network", "database", "git"}
    Missing declaration is treated as a warning (not an error) in v1.
    """
```

**PluginManager validation in discover_and_load():**
```python
def _validate_capabilities(self) -> None:
    """Check plugin capability declarations and log warnings."""
    import structlog
    log = structlog.get_logger(__name__)

    for plugin in self._pm.get_plugins():
        plugin_name = self._pm.get_name(plugin) or plugin.__class__.__name__
        declare_fn = getattr(plugin, "declare_capabilities", None)
        if declare_fn is None:
            log.warning("plugin.no_capabilities_declared", plugin=plugin_name)
            continue
        try:
            caps = self._pm.hook.declare_capabilities.call_historic(...)
            # validate caps is a subset of VALID_CAPABILITIES
        except Exception:
            log.warning("plugin.capability_declaration_failed", plugin=plugin_name)
```

**Audit logging for plugin operations:**
The structlog telemetry infrastructure is already configured via `configure_logging()`. Plugin operations that touch filesystem, network, database, or git should log via structlog with standard fields:
```python
log.info(
    "plugin.operation",
    plugin=plugin_name,
    capability="filesystem",
    action="write",
    path=str(path),
)
```

The audit log entries live in the existing structlog output stream (stderr). No separate audit log file is needed for v1.

**Where audit logging is injected:** The existing `post_action` hookspec fires after every action. The GitPlugin's post_action already logs git operations internally. For filesystem and network operations, the audit log should be added in PluginManager._collect_contributions() when plugin hooks are dispatched, or in individual plugin methods via a shared helper.

### Anti-Patterns to Avoid

- **Dynamic FastMCP tool registration at runtime:** FastMCP registers tools at server creation time. Do not attempt to add/remove tools after `create_server()` returns — this is not how FastMCP works.
- **ServiceError recovery as structured JSON:** Plain text strings are the correct v1 format. Structured JSON requires agents to parse the recovery field, adding complexity without benefit at this stage.
- **Modifying frozen ServiceResult to add recovery:** The locked decision is recovery on ServiceError, not ServiceResult. Do not add recovery to ServiceResult.
- **Breaking existing ServiceError construction sites:** The `recovery` field MUST default to `None`. There are 30+ construction sites — they must all continue to work without modification.
- **Capability validation as hard errors:** Missing capability declarations are warnings in v1. Hard errors would break all existing plugins that haven't declared capabilities yet.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Error code lookup | Custom dict per service | COMMON_ERROR_RECOVERY in response.py | Single source of truth already established |
| Category filtering | New registry data structure | ActionRegistry.list_actions(category=...) | Filter already exists — just call it |
| Plugin hook dispatch | Direct method calls on plugin objects | pluggy hookspec + hookimpl pattern | Isolation, error handling, multiple plugins |
| Structured logging | print() or logging.basicConfig | structlog already configured via configure_logging() | Consistent JSON/Rich output, ContextVar propagation |
| Template rendering | String formatting for recipe steps | Plain Python dicts serialized to JSON | Recipes are data, not templates |

**Key insight:** This phase is almost entirely additive. The infrastructure (registry, hooks, structlog, MCP server, Pydantic models) already exists. Every task is extending existing patterns, not creating new ones.

---

## Common Pitfalls

### Pitfall 1: McpError.detail Not Forwarded in from_result()

**What goes wrong:** The current `from_result()` creates `McpError(code=..., message=...)` without forwarding `detail`. The new `recovery` field must also not be forgotten.
**Why it happens:** The original implementation explicitly omitted detail to keep MCP responses lean.
**How to avoid:** When adding `recovery` to McpError, verify that `from_result()` explicitly passes `recovery=recovery`. Run the existing test `test_from_result_error` and add a new test for recovery propagation.
**Warning signs:** McpError.recovery is always None in agent responses even when COMMON_ERROR_RECOVERY has an entry for the code.

### Pitfall 2: Recovery Field Lost Under exclude_none=True

**What goes wrong:** `model_dump(exclude_none=True)` drops `recovery=None`. This is correct behavior for fields with no recovery guidance, but means recovery ONLY appears when non-None.
**Why it happens:** The MCP response pipeline always calls `model_dump(exclude_none=True)`.
**How to avoid:** This is the desired behavior — recovery appears only when guidance exists. Write tests that assert recovery is present in the dumped dict for known-recovery codes and absent for codes without entries.

### Pitfall 3: Category "mutation" Not in Default Active Set

**What goes wrong:** The "mutation" category (archive, supersede, update_*, close_*) is missing from the default active set. Agents cannot update or close notes without activating it.
**Why it happens:** The CONTEXT.md recommendation lists "discovery, creation, query, lifecycle, session" — mutation is absent.
**How to avoid:** Treat "mutation" as a core category alongside creation. The recommended default set should be: `{"creation", "mutation", "query", "graph", "lifecycle", "session"}`. Discretion applies here.

### Pitfall 4: Plugin Categories Starting as Unknown

**What goes wrong:** Plugin-contributed ActionDefinitions use custom category strings (e.g., "sprint", "kanban"). If generate_tools() filters by active categories and the plugin category is not in the active set, all plugin tools are silently absent.
**Why it happens:** The progressive disclosure design requires plugin categories to start inactive. But if tools are silently omitted from the server, agents have no way to know they exist.
**How to avoid:** Under the simpler "all tools registered" approach (recommended above), this is a non-issue. If filtering is implemented, `discover_categories` MUST return all categories including inactive ones so agents know they exist.

### Pitfall 5: Copier unsafe= vs trust= Parameter Name Confusion

**What goes wrong:** The Python Copier API uses `unsafe=` not `trust=`. The CONTEXT.md mentions "--trust=false" as a CLI flag concept, but the implementation must use `unsafe=False`.
**Why it happens:** Documentation mismatch between CLI flag names and Python API parameter names.
**How to avoid:** The existing code already uses `unsafe=False` correctly (confirmed by inspection of workflow.py lines 340-349). The CLI flag `--force-trust` maps to `unsafe=True` in the Python call. Do not add `trust=` anywhere.

### Pitfall 6: pluggy hookspec for declare_capabilities Not firstresult

**What goes wrong:** If `declare_capabilities` is marked `firstresult=True`, only the first plugin's capabilities are collected. All plugins need to declare their own capabilities independently.
**Why it happens:** Copy-paste from other firstresult hooks.
**How to avoid:** `declare_capabilities` must NOT use `firstresult=True`. The PluginManager collects declarations from each plugin individually by iterating `self._pm.get_plugins()` and calling the hook method directly, or by using the non-firstresult hook pattern.

---

## Code Examples

Verified patterns from existing source:

### Extending Frozen Pydantic Model (default=None pattern)

```python
# Source: src/ztlctl/services/result.py — existing pattern
class ServiceError(BaseModel):
    model_config = {"frozen": True}
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)
    # Adding optional field with default — all existing sites unaffected:
    recovery: str | None = None
```

### COMMON_ERROR_RECOVERY Dict Extension

```python
# Source: src/ztlctl/mcp/response.py — existing dict, extended
COMMON_ERROR_RECOVERY: dict[str, str] = {
    # Existing 9 entries...
    "NOT_FOUND": "Verify the target ID with search(), list_items(), or get_document().",
    # New entries:
    "ALREADY_OPEN": "The session is already open. Use session_status() to inspect it or close() to end it.",
    "NO_ENTRIES": "The session has no entries. Add notes or references before closing.",
    # ... (all ~25 new codes from audit above)
}
```

### Recipe Resource Implementation Pattern

```python
# Source: src/ztlctl/mcp/resources.py — _impl + register pattern

def recipe_research_capture_impl(_vault: Any) -> dict[str, Any]:
    """Research-capture recipe: search then create and link notes."""
    return {
        "name": "research-capture",
        "description": "Capture research findings: search existing content, create synthesis notes, link evidence.",
        "steps": [
            {
                "step": 1,
                "action": "search",
                "params": {"query": "{topic}", "limit": 10},
                "description": "Search for existing content on the topic to avoid duplication.",
                "conditions": [],
            },
            {
                "step": 2,
                "action": "create_note",
                "params": {"title": "{synthesis_title}", "maturity": "seed"},
                "description": "Create a seed note to capture the synthesis.",
                "conditions": ["skip if step 1 returns a note with identical title"],
            },
            {
                "step": 3,
                "action": "reweave",
                "params": {"content_id": "{step_2.content_id}"},
                "description": "Connect the new note to related content found in step 1.",
                "conditions": [],
            },
        ],
    }
```

### Category Discovery Tool Handler

```python
# New handler for discover_categories action
def _discover_categories_handler(vault: Any) -> ServiceResult:
    from ztlctl.actions.registry import get_action_registry
    from ztlctl.mcp.generator import _DEFAULT_ACTIVE_CATEGORIES, get_active_categories

    registry = get_action_registry()
    active = get_active_categories()
    all_categories: dict[str, Any] = {}
    for action in registry.list_actions():
        cat = action.category
        if cat not in all_categories:
            all_categories[cat] = {
                "category": cat,
                "active": cat in active,
                "core": cat in _DEFAULT_ACTIVE_CATEGORIES,
                "tools": [],
            }
        all_categories[cat]["tools"].append(action.name)

    return ServiceResult(
        ok=True,
        op="discover_categories",
        data={"categories": list(all_categories.values())},
    )
```

### structlog Audit Logging Pattern

```python
# Source: existing pattern in structlog telemetry infrastructure
import structlog
log = structlog.get_logger(__name__)

# Plugin audit log entry
log.info(
    "plugin.operation",
    plugin=plugin_name,
    capability="filesystem",
    action="write",
    path=str(target_path),
)
```

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| Hand-written error recovery in docstrings | Machine-readable recovery in ServiceError.recovery | This phase implements the transition |
| All MCP tools always registered | Category-aware tool surface | Phase 6 adds category metadata (disclosure is informational in v1) |
| Plugin templates trusted by default | Plugin templates require --force-trust | Built-in templates already use unsafe=False since Phase 1 (HARD-07) |

---

## Open Questions

1. **FastMCP session identity for category state**
   - What we know: FastMCP does not expose per-session context identifiers in the current API.
   - What's unclear: Whether category state should be truly per-session (requiring session ID tracking) or shared across all concurrent MCP clients connecting to the same process.
   - Recommendation: Use module-level state (one active set per server process). In practice, ztlctl serve runs as a single-user local process. Document this limitation.

2. **discover_categories tool vs MCP resource**
   - What we know: It is listed in CONTEXT.md as an MCP tool (verb-like name, takes action).
   - What's unclear: Whether `discover_categories` should be an ActionDefinition-backed tool or a resource like `ztlctl://categories`.
   - Recommendation: Implement as ActionDefinition in the "discovery" category (consistent with discover_tools). Resources are for read-only vault state; categories are server configuration state.

3. **Capability audit log placement**
   - What we know: The post_action hookspec fires after every action and GitPlugin already logs git operations internally.
   - What's unclear: Whether audit logging should happen in the hookspec dispatch itself (in PluginManager) or be delegated to each plugin.
   - Recommendation: PluginManager._collect_contributions() adds a wrapper that logs before dispatching to the plugin handler. This ensures audit coverage without requiring each plugin to remember to log.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing, no version change) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/services/test_result.py tests/mcp/test_response.py tests/mcp/test_resources.py tests/mcp/test_generator.py tests/plugins/test_manager.py -x` |
| Full suite command | `uv run pytest` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AGNT-01 | ServiceError.recovery field present with None default | unit | `uv run pytest tests/services/test_result.py -x` | YES (extend) |
| AGNT-01 | McpError.recovery populated from COMMON_ERROR_RECOVERY | unit | `uv run pytest tests/mcp/test_response.py -x` | YES (extend) |
| AGNT-01 | All error codes have recovery entries | unit | `uv run pytest tests/mcp/test_response.py::test_all_codes_have_recovery -x` | NO - Wave 0 |
| AGNT-03 | Recipe resources return valid step-list JSON | unit | `uv run pytest tests/mcp/test_resources.py -x` | YES (extend) |
| AGNT-03 | Recipe catalog includes all three recipe URIs | unit | `uv run pytest tests/mcp/test_resources.py::test_recipe_catalog -x` | NO - Wave 0 |
| AGNT-04 | discover_categories returns all categories with active status | unit | `uv run pytest tests/mcp/test_generator.py::test_discover_categories -x` | NO - Wave 0 |
| AGNT-04 | activate_category adds category to active set | unit | `uv run pytest tests/mcp/test_generator.py::test_activate_category -x` | NO - Wave 0 |
| SECU-01 | workflow init with plugin template uses unsafe=False by default | unit | `uv run pytest tests/services/test_workflow.py -x` | YES (extend) |
| SECU-01 | --force-trust flag passes unsafe=True to plugin Copier call | unit | `uv run pytest tests/services/test_workflow.py::test_force_trust -x` | NO - Wave 0 |
| SECU-02 | declare_capabilities hookspec exists and collects from plugins | unit | `uv run pytest tests/plugins/test_manager.py::test_capability_declarations -x` | NO - Wave 0 |
| SECU-02 | Missing capability declaration logs structlog warning | unit | `uv run pytest tests/plugins/test_manager.py::test_capability_warning -x` | NO - Wave 0 |

### Sampling Rate

- **Per task commit:** `uv run pytest tests/services/test_result.py tests/mcp/test_response.py tests/mcp/test_resources.py tests/mcp/test_generator.py tests/plugins/test_manager.py tests/services/test_workflow.py -x`
- **Per wave merge:** `uv run pytest`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/mcp/test_resources.py` — extend with `test_recipe_catalog`, `test_recipe_research_capture_impl`, `test_recipe_review_triage_impl`, `test_recipe_knowledge_synthesis_impl`
- [ ] `tests/mcp/test_generator.py` — extend with `test_discover_categories`, `test_activate_category`, `test_deactivate_category`, `test_default_active_categories`
- [ ] `tests/mcp/test_response.py` — extend with `test_recovery_populated_from_common_dict`, `test_recovery_from_service_error_overrides_dict`, `test_all_codes_have_recovery`
- [ ] `tests/services/test_result.py` — extend with `test_service_error_recovery_field_default_none`, `test_service_error_with_recovery`
- [ ] `tests/services/test_workflow.py` — extend with `test_force_trust_flag`, `test_plugin_template_default_unsafe`
- [ ] `tests/plugins/test_manager.py` — extend with `test_capability_declarations`, `test_capability_warning_on_missing`, `test_capability_audit_log`

*(All Wave 0 work is extensions to existing test files — no new test modules needed)*

---

## Sources

### Primary (HIGH confidence)

- Source code inspection: `src/ztlctl/services/result.py` — ServiceError/ServiceResult frozen Pydantic models
- Source code inspection: `src/ztlctl/mcp/response.py` — COMMON_ERROR_RECOVERY dict (9 existing entries), McpResponse.from_result()
- Source code inspection: `src/ztlctl/mcp/resources.py` — resource registration pattern, _impl function pattern
- Source code inspection: `src/ztlctl/mcp/generator.py` — generate_tools(), _vault_ref module-level pattern, _make_tool_fn()
- Source code inspection: `src/ztlctl/actions/registry.py` — list_actions(category=...) filter
- Source code inspection: `src/ztlctl/actions/definitions.py` — ActionDefinition.category field
- Source code inspection: `src/ztlctl/plugins/manager.py` — discover_and_load(), _collect_contributions()
- Source code inspection: `src/ztlctl/plugins/hookspecs.py` — all hookspec definitions
- Source code inspection: `src/ztlctl/plugins/contracts.py` — all contribution dataclasses
- Source code inspection: `src/ztlctl/services/workflow.py` — _run_copy(), _run_update(), Copier unsafe=False pattern
- Grep audit: all ServiceError construction sites across 12 service files — 30+ unique error codes catalogued
- Source code inspection: `src/ztlctl/actions/_register_core.py` — all 13 categories and their action counts

### Secondary (MEDIUM confidence)

- `.planning/phases/06-agentic-integration-security/06-CONTEXT.md` — implementation decisions and locked choices
- `.planning/REQUIREMENTS.md` — AGNT-01, AGNT-03, AGNT-04, SECU-01, SECU-02 requirement descriptions

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all existing dependencies, no new packages
- Architecture: HIGH — all patterns verified against actual source code
- Pitfalls: HIGH — identified from direct code inspection (frozen model constraints, FastMCP registration model, Copier API naming)
- Error code audit: HIGH — grep-verified across all service files

**Research date:** 2026-03-20
**Valid until:** 2026-04-20 (stable codebase; re-verify if Pydantic v3 or FastMCP major version upgrade occurs)
