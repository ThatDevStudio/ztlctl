# Phase 3: MCP Surface Generation - Research

**Researched:** 2026-03-19
**Domain:** FastMCP tool generation, ActionRegistry-driven MCP surface, Pydantic response models, token-budget truncation
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Tool generation strategy:**
- Runtime generation at server startup — iterate the ActionRegistry and call `server.tool()` for each ActionDefinition. No static codegen step. Matches the existing `_register_tool()` pattern but driven by registry data instead of a hand-written function list.
- All 59 ActionDefinitions become MCP tools — including the 5 `custom_presentation` actions (batch, init wizard, serve, workflow init/update). Thin wrappers call the handler directly. No parity gaps.
- Context/dependency injection for Vault — NOT closure binding. Vault lives on a context object (server-level or module-level) set once during `create_server()`. Generated tools access it via accessor rather than closing over it.

**Migration and cleanup:**
- Delete and replace `mcp/tools.py` entirely — `_TOOL_CATALOG`, 29 `_impl` functions, and `register_tools()` are all redundant. Clean break, no zombie code.
- Pydantic-based MCP response schema — introduce Pydantic models for MCP response structure instead of raw dicts. ServiceResult gains MCP serialization capability via a base class method or static function. Replaces `_to_mcp_response()` and `COMMON_ERROR_RECOVERY` dict.
- Single registration path via registry primitive — ActionRegistry exposes a registration mechanism (decorator or base class) that both built-in controllers AND plugins use identically. No separate `mcp_tool_contributions` path.

**Testing approach:**
- Both controller unit tests AND DummyServer integration tests. MCP generation tests verify the generator produces correct tool registrations. DummyServer integration tests verify end-to-end tool execution through the generated layer. Replaces existing `_impl` function tests.

### Claude's Discretion

- **DI implementation details** — whether to use FastMCP's built-in lifespan/dependency injection or a simpler module-level context pattern. Research FastMCP capabilities and pick the best fit for the single-vault-per-server reality.
- **Pydantic response model shape** — exact field structure, inheritance hierarchy, whether to extend ServiceResult or create a separate MCP response model. Key constraint: Pydantic models for all schema definitions, with a method to convert to MCP-friendly output.
- **Registration primitive design** — decorator vs base class vs hybrid. Must work for both built-in `_register_core_actions()` and future plugin registrations. Can evolve further in Phase 5.
- **Token-budget implementation** — how truncation works for high-volume tools (list, search, vault_review, topic_packet). Per-tool opt-in vs universal, budget parameter naming, truncation strategy (AGNT-02).
- **Generator module organization** — file naming and module structure for the new MCP generation code.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ACTN-03 | Auto-generated MCP tools from ActionDefinitions — replaces hand-written register_tools() (~280 lines in current `register_tools()`; ~1498 total in tools.py); produces FastMCP tool registrations with JSON schema, catalog metadata, and side-effect annotations | Generator iterates `get_action_registry().list_actions()`, builds wrapper functions with correct Python type annotations from `ActionParam.type`, sets `__doc__` via `_render_tool_doc()` analog, calls `server.tool()(fn)` — confirmed working pattern from existing code |
| AGNT-02 | Token-budget-aware MCP responses — extend existing `topic_packet` / `context` budget parameter pattern to `list_items`, `search`, `vault_review`, and `decision_support` high-volume tools | Token budget is already a service-level concept (QueryService.topic_packet, SessionService.context both accept `budget: int`). For list/search/vault_review: add `token_budget` param to ActionDefinition + controller + service; generator passes it through; response serializer truncates data dict items to fit budget estimate |
| PLUG-04 | Complete MCP tool parity with CLI — archive, extract, supersede, upgrade, check, init, workflow commands all have MCP tool equivalents (achieved by construction via ActionRegistry) | All 59 ActionDefinitions are already registered in Phase 2. Generator produces tools for ALL of them including the 5 `custom_presentation=True` ones. Parity is automatic — no gap analysis needed. |
</phase_requirements>

## Summary

Phase 3 replaces 1498 lines of hand-written `mcp/tools.py` with a generator module that iterates the ActionRegistry singleton and produces FastMCP tool registrations at server startup. The key insight is that the existing `_register_tool()` pattern in tools.py already demonstrates the correct FastMCP API — `server.tool()(fn)` where `fn` has Python type annotations that drive JSON schema generation and a `__doc__` that becomes the tool description. The generator simply automates what was previously manual.

The three non-trivial design problems are: (1) building a wrapper function with correct Python type annotations from `ActionParam.type` at runtime (Python's `inspect` and `types.FunctionType` won't help here — the solution is a closure factory that builds a typed `**kwargs` wrapper and delegates to the handler); (2) introducing Pydantic response models to replace the raw-dict `_to_mcp_response()` pattern; and (3) adding token-budget truncation to high-volume tools (`list_items`, `search`, `vault_review`, `decision_support`) where the service currently returns unbounded result sets.

The Vault dependency injection decision should use a simple module-level context object set once in `create_server()`. FastMCP's `Depends()` injection is designed for request-scoped dependencies (per-tool-call factories), not server-scoped singletons — a module-level vault accessor is simpler and matches the single-vault-per-server model.

**Primary recommendation:** Implement a `mcp/generator.py` module with `generate_tools(server, vault)` that replaces `register_tools()`. The generator reads from `get_action_registry()`, builds wrapper functions via a closure factory (`_make_tool_fn(action, vault)`), sets `__doc__` from ActionDefinition metadata, and calls `server.tool()(fn)`. Pydantic response models live in `mcp/response.py`. Token-budget support is added to the four high-volume ActionDefinitions and their controller/service methods.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp (FastMCP) | >=1.0 (project dep) | MCP server framework | Already in use; `server.tool()(fn)` pattern confirmed working in existing code |
| pydantic | >=2.0 (project dep) | Response model schema | Already project dependency; ServiceResult is already Pydantic |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `types` stdlib | stdlib | `FunctionType` — not needed; closure factory pattern is simpler | Skip; use closures instead |
| Python `functools` stdlib | stdlib | `wraps()` to propagate `__name__` and `__doc__` | Use in `_make_tool_fn()` to preserve function identity |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Module-level vault accessor | FastMCP `Depends()` injection | `Depends()` creates a new factory call per tool invocation — works but adds unnecessary indirection for a server-scoped singleton; module-level accessor is simpler |
| Closure factory per action | Static file code generation | Codegen creates a build step and drift risk; runtime generation from registry is the locked decision |
| Separate `McpResponse` Pydantic model | Add `.to_mcp()` method on `ServiceResult` | ServiceResult is frozen — can't add methods without subclassing; a separate `McpResponse` model with a `from_result(result)` classmethod is cleaner |

**No new packages to install** — all dependencies already exist.

## Architecture Patterns

### Recommended Project Structure
```
src/ztlctl/mcp/
├── __init__.py          # (unchanged)
├── server.py            # calls generate_tools() instead of register_tools()
├── generator.py         # NEW: generate_tools(server, vault), _make_tool_fn()
├── response.py          # NEW: McpResponse Pydantic model, from_result()
├── resources.py         # (unchanged, out of scope)
└── prompts.py           # (unchanged, out of scope)

src/ztlctl/actions/
├── __init__.py          # (unchanged — exposes get_action_registry())
├── definitions.py       # (unchanged)
├── registry.py          # (unchanged — may add decorator helper in Claude's discretion)
└── _register_core.py    # add token_budget param to list_items, search, vault_review, decision_support
```

### Pattern 1: Tool Generator — Closure Factory

The central pattern. For each ActionDefinition, build a wrapper function that (a) injects vault, (b) has correct Python parameter names and defaults, (c) has `__doc__` from ActionDefinition metadata.

FastMCP derives JSON schema from function parameter **names and defaults only** — not runtime types — so the closure approach works even though `ActionParam.type` is not used to annotate the generated closure. The existing registration confirms this: `server.tool()(fn)` where `fn` has explicit Python annotations produces correct schema.

**Key constraint from CONTEXT.md:** The generator produces tool functions with correct type annotations so FastMCP can derive JSON schema from Python signatures. This means the wrapper functions must carry real `__annotations__`, not just `**kwargs`.

The current `register_tools()` achieves this by defining inner functions with full signatures (e.g., `def create_note(title: str, subtype: str | None = None, ...) -> dict[str, Any]`). The generator must replicate this — not by introspection, but by building wrappers that carry the type information from `ActionParam`.

**Practical approach:** Use `exec()` to build a function with the exact signature string derived from `ActionParam` descriptors, or use a Pydantic model as input schema (FastMCP supports Pydantic models as tool input). The Pydantic model approach aligns with the locked decision and avoids `exec()`.

```python
# Source: existing mcp/tools.py _register_tool() + FastMCP docs
# Pattern: closure factory with __name__, __doc__, and __annotations__ set

def _make_tool_fn(action: ActionDefinition, vault: Any) -> Callable[..., dict[str, Any]]:
    """Build a vault-bound wrapper function for one ActionDefinition."""

    def tool_fn(**kwargs: Any) -> dict[str, Any]:
        result = action.handler(vault, **kwargs)
        return McpResponse.from_result(result).model_dump(exclude_none=True)

    tool_fn.__name__ = action.name
    tool_fn.__doc__ = _render_action_doc(action)
    # Annotations built from ActionParam descriptors
    tool_fn.__annotations__ = _build_annotations(action.params)
    # Defaults injected via __defaults__ / __kwdefaults__
    return tool_fn
```

The `_build_annotations` and defaults injection approach is how the existing code works — the inner functions in `register_tools()` carry explicit Python annotations. For the generator, building `__annotations__` and `__kwdefaults__` dicts programmatically achieves the same result.

**Alternative — Pydantic input model per action:**
```python
# Derive input model from ActionParams — aligns with Pydantic-for-schema locked decision
InputModel = _build_input_model(action)  # dynamically created Pydantic model

def tool_fn(params: InputModel) -> dict[str, Any]:  # FastMCP handles model schema
    result = action.handler(vault, **params.model_dump(exclude_none=True))
    return McpResponse.from_result(result).model_dump(exclude_none=True)
```

**Recommendation:** Use the `__annotations__` + `__kwdefaults__` approach first (it's proven in the codebase). Reserve Pydantic input models for a future iteration — the locked decision says "Pydantic models for all schema definitions" but the generator's internal mechanism is Claude's discretion.

### Pattern 2: McpResponse Pydantic Model

Replaces the raw-dict `_to_mcp_response()` function with a typed model:

```python
# src/ztlctl/mcp/response.py
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

class McpError(BaseModel):
    model_config = {"frozen": True}
    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)

class McpResponse(BaseModel):
    model_config = {"frozen": True}
    ok: bool
    op: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: McpError | None = None

    @classmethod
    def from_result(cls, result: ServiceResult) -> "McpResponse":
        return cls(
            ok=result.ok,
            op=result.op,
            data=result.data,
            warnings=result.warnings,
            error=McpError(
                code=result.error.code,
                message=result.error.message,
            ) if result.error else None,
        )
```

`model_dump(exclude_none=True)` on this model produces the same output as the current `_to_mcp_response()`. The difference: schema is Pydantic-derived, field validation is enforced, the model is testable in isolation.

### Pattern 3: Token-Budget Truncation for High-Volume Tools

The existing `topic_packet` and `session.context` already pass `budget: int` through to `ContextAssembler`. The four tools needing budget support (`list_items`, `search`, `vault_review`, `decision_support`) currently return unbounded result lists.

**Approach:** Add `token_budget: int | None = None` parameter at the MCP generator layer. The generator wraps the handler call in a budget-aware truncator that estimates token count from the serialized response and trims `data["items"]` or equivalent list field until within budget.

This keeps budget enforcement in the MCP layer (not the service layer), since token counting is an MCP concern. The controllers/services remain unchanged for these tools.

```python
# In generator.py
def _apply_token_budget(data: dict[str, Any], budget: int | None) -> dict[str, Any]:
    """Trim list-valued data fields to approximate token budget."""
    if budget is None:
        return data
    # Estimate: 1 token ~ 4 chars. Each item serialized.
    import json
    serialized = json.dumps(data)
    if len(serialized) // 4 <= budget:
        return data
    # Find the primary list field and truncate
    for key, value in data.items():
        if isinstance(value, list) and value:
            # Binary search or linear trim
            while len(json.dumps(data)) // 4 > budget and data[key]:
                data = {**data, key: data[key][:-1]}
            return {**data, "truncated": True, "token_budget": budget}
    return data
```

This is a simple, correct-enough approach. The existing `topic_packet` uses `ContextAssembler` which does sophisticated budget-aware assembly at the service level — that pattern should be noted as the gold standard for future iterations.

### Pattern 4: Registration Primitive for Plugins

The locked decision requires a shared registration mechanism for both built-in and plugin ActionDefinitions. The simplest form that works now and evolves in Phase 5:

```python
# In actions/registry.py — add a decorator helper
def action(
    name: str,
    *,
    registry: ActionRegistry | None = None,
) -> Callable[[ActionDefinition], ActionDefinition]:
    """Decorator that registers an ActionDefinition into the registry."""
    target = registry or get_action_registry()
    def decorator(defn: ActionDefinition) -> ActionDefinition:
        target.register(defn)
        return defn
    return decorator
```

Plugin authors call `get_action_registry().register(defn)` directly (already documented in registry.py docstring). The decorator wraps that for ergonomics. Phase 5 will add hookspec deprecation and migrate `mcp_tool_contributions` to this path.

### Pattern 5: `discover_tools` and `describe_tool` Migration

These two tools currently read from `_TOOL_CATALOG` (TypedDict-based). After migration, they read from `get_action_registry().list_actions()`. The data is equivalent — ActionDefinition carries all the same fields. The generator registers them like any other action (they're in `_register_core.py` already).

### Anti-Patterns to Avoid

- **Keeping any `_impl` functions:** They are redundant once controllers handle orchestration. Delete entirely.
- **Keeping `_TOOL_CATALOG`:** Redundant — ActionDefinitions are the catalog now. Delete entirely.
- **Using `exec()` for function signature generation:** The closure + `__annotations__` approach is simpler and avoids security concerns.
- **Adding budget logic to service methods:** Token budget is an MCP-layer concern. Keep services return unbounded; truncate in the generator wrapper.
- **Closure binding of vault:** The locked decision says accessor pattern, not closure. A module-level `_vault_context` dict or a simple module-level variable set in `create_server()` is the correct pattern.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON schema from Python types | Custom type-to-schema mapper | FastMCP's built-in schema generation from type annotations | FastMCP already handles `str`, `int`, `bool`, `list[str]`, `dict`, `Optional[T]`, Literal choices |
| Tool docstring format | Custom doc builder from scratch | Adapt existing `_render_tool_doc()` pattern from tools.py | The existing function already produces the right format — port it to read from ActionDefinition instead of ToolCatalogEntry |
| Token estimation | Token-counting library | Character-count heuristic (1 token ~ 4 chars) for truncation | Sufficient for budget-aware truncation; no need for tiktoken |
| Response validation | Custom schema validator | Pydantic's built-in validation on McpResponse | McpResponse.from_result() validates as part of construction |

**Key insight:** FastMCP's value is that Python function signatures ARE the tool schema. The generator's job is to produce function objects with the right signatures — FastMCP handles the rest.

## Common Pitfalls

### Pitfall 1: `__annotations__` Must Be on the Exact Function Object FastMCP Inspects

**What goes wrong:** Setting `__annotations__` on a function after definition doesn't always propagate if FastMCP uses `inspect.signature()` which reads `__annotations__` from `__wrapped__` if `functools.wraps` was used.
**Why it happens:** `functools.wraps` copies `__wrapped__`, which makes `inspect.signature()` follow the chain to the original function's signature.
**How to avoid:** Either (a) do NOT use `functools.wraps` in `_make_tool_fn`, just set `__name__`, `__doc__`, `__annotations__` directly; or (b) set `__signature__` explicitly using `inspect.Signature`. The existing codebase uses option (a) successfully in `_plugin_tool_wrapper`.
**Warning signs:** FastMCP registers the tool but the parameter schema shows `**kwargs` instead of named parameters.

### Pitfall 2: `ActionParam.type = list` vs `list[str]`

**What goes wrong:** `ActionParam.type` stores the bare Python type (e.g., `list`, `dict`), not a generic alias like `list[str]`. FastMCP may produce `array` schema without item type information.
**Why it happens:** `ActionParam` was designed for CLI rendering; generic aliases weren't needed. `list` → `list[Any]` is a lossless annotation for MCP schema purposes (agents pass JSON arrays, FastMCP validates element types if specified).
**How to avoid:** In `_build_annotations()`, map `list` → `list[Any]`, `dict` → `dict[str, Any]`. For params with `choices`, build a `Literal[...]` type annotation for proper enum schema.
**Warning signs:** Parity test shows MCP tool schema accepts invalid types.

### Pitfall 3: `choices` Must Map to `Literal` Annotation for Enum Schema

**What goes wrong:** An `ActionParam` with `choices=("read", "write")` but type annotation `str` produces a plain string schema — MCP clients won't know the valid values.
**Why it happens:** FastMCP derives enum constraints from `Literal[...]` types, not from external metadata.
**How to avoid:** In `_build_annotations()`, if `param.choices` is set, use `Literal[*param.choices]` (Python 3.11+) or `Literal["a", "b"]` built dynamically. Example:
```python
from typing import Literal, get_args
choices_type = Literal[tuple(param.choices)]  # works in 3.11+
# For 3.10: use __args__ trick or just use str and document choices in docstring
```
Since the project uses Python 3.13, `Literal[*choices]` syntax works.
**Warning signs:** MCP client tool schema shows `"type": "string"` instead of `"enum": [...]` for choice parameters.

### Pitfall 4: Plugin `mcp_tool_contributions` Hookspec Must Be Deprecated Gracefully

**What goes wrong:** Deleting `tools.py` removes the code that calls `plugin_manager.mcp_tool_contributions(...)`. If the GitPlugin or ObsidianPlugin contributes tools via this hookspec, they silently stop working.
**Why it happens:** Built-in plugins may use `mcp_tool_contributions` (check `ztlctl/plugins/builtins/` before deletion).
**How to avoid:** Before deleting `register_tools()`, grep for `mcp_tool_contributions` implementations in all plugins. Migrate any plugin tool contributions to `get_action_registry().register()` calls, or keep a compatibility shim in `generator.py` that calls `mcp_tool_contributions` and processes contributions.
**Warning signs:** Plugin tools disappear from `discover_tools` output after migration.

### Pitfall 5: `server.tool()(fn)` Returns the Decorated Function — Don't Lose It

**What goes wrong:** `server.tool()` returns a decorator. Calling `server.tool()(fn)` mutates the server's tool registry as a side effect. The return value is the decorated function — it can be discarded. But if FastMCP changes to require storing the return value (rare), tools won't be registered.
**Why it happens:** The existing code already uses `server.tool()(fn)` without capturing the return. This is confirmed correct per existing tests.
**How to avoid:** No action needed — existing pattern is correct.

### Pitfall 6: Frozen `ServiceResult` Cannot Be Passed Directly as `McpResponse`

**What goes wrong:** Attempting to use `ServiceResult` directly as MCP response (since both are Pydantic) fails because `ServiceResult.meta` contains telemetry data that should NOT be forwarded to MCP clients.
**Why it happens:** Meta field contains internal performance spans, not agent-useful data.
**How to avoid:** Always go through `McpResponse.from_result()` which explicitly selects `ok`, `op`, `data`, `warnings`, `error` — and drops `meta`.

## Code Examples

### Generator Entrypoint

```python
# src/ztlctl/mcp/generator.py (NEW FILE)
# Source: adapted from existing mcp/tools.py _register_tool() pattern

from __future__ import annotations
from typing import Any
from ztlctl.actions.registry import get_action_registry
from ztlctl.mcp.response import McpResponse

_vault_ref: Any = None  # module-level server-scoped accessor

def set_vault(vault: Any) -> None:
    """Set the server-scoped vault. Called once from create_server()."""
    global _vault_ref
    _vault_ref = vault

def generate_tools(server: Any, vault: Any) -> None:
    """Register all ActionDefinition-backed MCP tools on the FastMCP server."""
    set_vault(vault)
    registry = get_action_registry()
    for action in registry.list_actions():
        fn = _make_tool_fn(action, vault)
        server.tool()(fn)
    _register_plugin_tools(server, vault)

def _register_plugin_tools(server: Any, vault: Any) -> None:
    """Compatibility shim: register plugin mcp_tool_contributions."""
    plugin_manager = getattr(vault, "plugin_manager", None)
    if plugin_manager is None:
        return
    reserved = {a.name for a in get_action_registry().list_actions()}
    for contribution in plugin_manager.mcp_tool_contributions(reserved_names=reserved):
        # Future: plugins migrate to registry.register(); for now keep shim
        fn = _make_plugin_tool_fn(vault, contribution)
        server.tool()(fn)
```

### Tool Function Builder

```python
# Source: adapted from existing register_tools() inner function pattern + _plugin_tool_wrapper

def _make_tool_fn(action: ActionDefinition, vault: Any) -> Callable[..., dict[str, Any]]:
    """Build a vault-bound, annotated wrapper function for one ActionDefinition."""
    annotations = _build_annotations(action.params)
    defaults = _build_defaults(action.params)

    def tool_fn(**kwargs: Any) -> dict[str, Any]:
        result = action.handler(vault, **kwargs)
        return McpResponse.from_result(result).model_dump(exclude_none=True)

    tool_fn.__name__ = action.name
    tool_fn.__doc__ = _render_action_doc(action)
    tool_fn.__annotations__ = {**annotations, "return": dict}
    tool_fn.__kwdefaults__ = defaults
    return tool_fn
```

### Annotation Builder from ActionParams

```python
def _build_annotations(params: tuple[ActionParam, ...]) -> dict[str, Any]:
    """Build __annotations__ dict from ActionParam descriptors."""
    annotations: dict[str, Any] = {}
    for param in params:
        if param.choices:
            # Build Literal type for enum schema
            from typing import Literal
            annotations[param.name] = Literal[tuple(param.choices)]  # type: ignore[misc]
        elif param.type is list:
            annotations[param.name] = list[Any] if param.required else list[Any] | None
        elif param.type is dict:
            annotations[param.name] = dict[str, Any] if param.required else dict[str, Any] | None
        else:
            annotations[param.name] = param.type if param.required else param.type | None
    return annotations

def _build_defaults(params: tuple[ActionParam, ...]) -> dict[str, Any]:
    """Build __kwdefaults__ dict for optional params."""
    return {p.name: p.default for p in params if not p.required}
```

### Doc Renderer from ActionDefinition

```python
# Adapted from _render_tool_doc() in tools.py
def _render_action_doc(action: ActionDefinition) -> str:
    lines = [
        f"What it does: {action.description}",
        f"When to use: {action.mcp_when_to_use}" if action.mcp_when_to_use else "",
        f"Avoid when: {action.mcp_avoid_when}" if action.mcp_avoid_when else "",
        f"Side effects: {'write. Mutates vault state.' if action.side_effect == 'write' else 'read. Does not mutate vault state.'}",
    ]
    if action.params:
        lines.append("Args:")
        for p in action.params:
            if p.description:
                lines.append(f"- {p.name}: {p.description}")
    if action.mcp_common_errors:
        lines.append("Common errors:")
        for code in action.mcp_common_errors:
            recovery = COMMON_ERROR_RECOVERY.get(code, code)
            lines.append(f"- {code}: {recovery}")
    return "\n".join(line for line in lines if line)
```

### Token-Budget Wrapper for High-Volume Tools

```python
# In generator.py — applied at make_tool_fn time for budget-aware actions
BUDGET_AWARE_ACTIONS = frozenset({"list_items", "search", "vault_review", "decision_support"})

def _make_budget_aware_tool_fn(action: ActionDefinition, vault: Any) -> Callable[..., dict[str, Any]]:
    """Variant of _make_tool_fn that adds token_budget param."""
    # ... same as _make_tool_fn but adds token_budget: int | None = None to annotations + kwdefaults
    # And wraps result data through _apply_token_budget(data, token_budget)
    pass
```

### Updated `create_server()` Integration Point

```python
# src/ztlctl/mcp/server.py — minimal change
from ztlctl.mcp.generator import generate_tools  # replaces: from ztlctl.mcp.tools import register_tools

# In create_server():
generate_tools(server, vault)  # replaces: register_tools(server, vault)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hand-written `_impl` functions + `_TOOL_CATALOG` TypedDict | ActionDefinition-driven generator | Phase 3 | Eliminates ~1498 lines; parity is structural not incidental |
| Raw dict MCP responses via `_to_mcp_response()` | Pydantic `McpResponse` model | Phase 3 | Schema validation, no meta leakage, testable in isolation |
| Plugin tools via `mcp_tool_contributions` hookspec | ActionRegistry.register() path (unified) | Phase 3 (compatibility shim) → Phase 5 (full migration) | Single registration path; hookspec deprecated but not removed until Phase 5 |
| Token budget only on topic_packet/context | Token budget on all high-volume tools | Phase 3 | AGNT-02 compliance |

**Deprecated/outdated after this phase:**
- `mcp/tools.py` entirely — deleted, replaced by `mcp/generator.py` + `mcp/response.py`
- `_TOOL_CATALOG` and `ToolCatalogEntry` TypedDict — replaced by ActionDefinition
- `COMMON_ERROR_RECOVERY` dict in tools.py — moved to `mcp/response.py` or a shared constants module
- `_to_mcp_response()` function — replaced by `McpResponse.from_result()`
- `_impl` functions (29 of them) — replaced by controller handlers
- `register_tools()` — replaced by `generate_tools()`
- `tool_catalog()` function — replaced by `get_action_registry().list_actions()`

## Open Questions

1. **`discover_tools` and `describe_tool` behavior after migration**
   - What we know: These tools currently read from `_TOOL_CATALOG` + plugin contributions. After migration they read from `get_action_registry().list_actions()`. The data is equivalent.
   - What's unclear: `discover_tools` groups by category and returns `name/description/side_effect`. The ActionDefinition has all these fields. `describe_tool` returns `args_guidance` which in the old model was a flat `dict[str, str]` — in ActionDefinition it's per-param `ActionParam.description`. The generator for these tools must reconstruct `args_guidance` format from ActionParams.
   - Recommendation: In `_render_action_doc()` and the `describe_tool` tool implementation, derive `args_guidance` from `{p.name: p.description for p in action.params}` — equivalent to the old format.

2. **Built-in plugin tool contributions**
   - What we know: `hookspecs.py` defines `mcp_tool_contributions`. The existing `register_tools()` calls `plugin_manager.mcp_tool_contributions(reserved_names=...)`.
   - What's unclear: Whether the built-in GitPlugin or ObsidianPlugin implement `mcp_tool_contributions`. If they do, deleting `tools.py` without a shim drops those tools.
   - Recommendation: Grep `ztlctl/plugins/builtins/` for `mcp_tool_contributions` implementations before deletion. Add the compatibility shim in `generator.py` to preserve behavior. File a TODO for Phase 5 to migrate these to `registry.register()`.

3. **`ActionParam.type = int` for `reweave_id` (int, not str)**
   - What we know: `ActionParam.type` can be `int`, `float`, `bool`, `str`, `list`, `dict`. The annotation builder handles all of these.
   - What's unclear: FastMCP's JSON schema for `int` parameters — does it coerce string inputs from MCP protocol? JSON integers map to Python ints correctly in the protocol.
   - Recommendation: No special handling needed. Standard JSON protocol handles int types correctly.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `uv run pytest tests/mcp/ -x -q` |
| Full suite command | `uv run pytest -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ACTN-03 | Generator produces MCP tool for every registered ActionDefinition | integration | `uv run pytest tests/mcp/test_generator.py -x` | Wave 0 |
| ACTN-03 | Generated tools call handler and return McpResponse-shaped dict | integration (DummyServer) | `uv run pytest tests/mcp/test_generator.py::TestDummyServerGeneration -x` | Wave 0 |
| ACTN-03 | `server.py` calls `generate_tools` not `register_tools` | unit | `uv run pytest tests/mcp/test_server.py -x` | exists (needs update) |
| ACTN-03 | McpResponse.from_result() produces correct shape from ServiceResult | unit | `uv run pytest tests/mcp/test_response.py -x` | Wave 0 |
| AGNT-02 | `list_items` / `search` / `vault_review` / `decision_support` accept `token_budget` and truncate | integration | `uv run pytest tests/mcp/test_generator.py::TestTokenBudget -x` | Wave 0 |
| PLUG-04 | All 59 ActionDefinitions produce registered MCP tools (parity test) | integration | `uv run pytest tests/mcp/test_parity.py -x` | Wave 0 |
| PLUG-04 | Previously-missing tools (archive, supersede, upgrade, check, init, workflow) are discoverable | integration | `uv run pytest tests/mcp/test_parity.py::TestParityCompleteness -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/mcp/ tests/actions/ -x -q`
- **Per wave merge:** `uv run pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/mcp/test_generator.py` — covers ACTN-03 generator unit + DummyServer integration
- [ ] `tests/mcp/test_response.py` — covers McpResponse model (unit)
- [ ] `tests/mcp/test_parity.py` — covers PLUG-04 CLI/MCP parity assertion (all 59 tools present)
- [ ] `tests/mcp/test_tools.py` — MUST be deleted (imports `_impl` functions that will not exist)
- [ ] `tests/mcp/test_tools_impl.py` — MUST be deleted (same reason)

## Sources

### Primary (HIGH confidence)
- Existing `src/ztlctl/mcp/tools.py` — `_register_tool()` pattern, `server.tool()(fn)` call, `__doc__` injection, `_plugin_tool_wrapper` `__name__` assignment; all confirmed working in existing test suite
- Existing `src/ztlctl/actions/definitions.py` — ActionParam and ActionDefinition fields; all metadata needed for generator is present
- Existing `src/ztlctl/actions/_register_core.py` — 59 ActionDefinitions, confirmed custom_presentation flags on batch/init_vault/workflow actions
- Existing `src/ztlctl/services/result.py` — ServiceResult structure; McpResponse shape is directly derived from this
- `tests/mcp/test_tools.py` — DummyServer test pattern confirmed; these tests will be replaced

### Secondary (MEDIUM confidence)
- [FastMCP Tools documentation](https://gofastmcp.com/servers/tools) — `server.tool()(fn)` decorator usage, `__name__`/`__doc__` override, `add_tool()` method
- [FastMCP Tool System (DeepWiki)](https://deepwiki.com/modelcontextprotocol/python-sdk/2.2-tool-system) — Tool.from_function() internal flow, annotation-to-schema mapping

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new packages; all tools already in use
- Architecture: HIGH — generator pattern proven by existing `_register_tool()` code; pitfalls identified from existing code
- Pitfalls: HIGH — all identified pitfalls are grounded in existing code patterns (functools.wraps behavior, ActionParam.type bare types, choices-to-Literal mapping)
- Token budget: MEDIUM — approach is reasonable but exact truncation logic is Claude's discretion; service-level budget (topic_packet pattern) is the proven gold standard

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (FastMCP API is stable; MCP spec changes unlikely to affect tool registration in 30 days)
