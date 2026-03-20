"""MCP tool generator — ActionRegistry-driven tool registration.

Replaces hand-written ``tools.py`` with auto-generated MCP tools derived
from ActionDefinitions.  ``generate_tools()`` iterates the registry and
calls ``server.tool()`` for each action, producing correct
``__annotations__``, ``__kwdefaults__``, and ``__doc__`` without needing
the mcp package at import time.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, Literal

from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.actions.registry import get_action_registry
from ztlctl.mcp.response import COMMON_ERROR_RECOVERY, McpResponse

# ---------------------------------------------------------------------------
# Token-budget support
# ---------------------------------------------------------------------------

#: Actions whose responses may contain large lists and benefit from truncation.
BUDGET_AWARE_ACTIONS: frozenset[str] = frozenset(
    {"list_items", "search", "vault_review", "decision_support"}
)


def _apply_token_budget(data: dict[str, Any], budget: int | None) -> dict[str, Any]:
    """Truncate *data* so its serialised size fits within *budget* tokens.

    - If *budget* is ``None``, return *data* unchanged.
    - Estimates token count as ``len(json.dumps(data)) // 4``.
    - If the estimate already fits, return *data* unchanged.
    - Otherwise, find the first list-valued field and iteratively remove
      trailing elements until the payload fits or the list is empty.
    - Adds ``"truncated": True`` and ``"token_budget": budget`` to the
      returned dict when truncation was applied.
    """
    if budget is None:
        return data

    serialized = json.dumps(data)
    if len(serialized) // 4 <= budget:
        return data

    # Find first non-empty list field to truncate
    list_key: str | None = None
    for key, val in data.items():
        if isinstance(val, list) and len(val) > 0:
            list_key = key
            break

    if list_key is None:
        # No list field to truncate — return unchanged
        return data

    truncated = {**data, list_key: list(data[list_key])}
    while truncated[list_key] and len(json.dumps(truncated)) // 4 > budget:
        truncated[list_key] = truncated[list_key][:-1]

    truncated["truncated"] = True
    truncated["token_budget"] = budget
    return truncated


# ---------------------------------------------------------------------------
# Module-level vault reference (server-scoped, set once per create_server call)
# ---------------------------------------------------------------------------

_vault_ref: Any = None


def set_vault(vault: Any) -> None:
    """Set the module-level vault reference."""
    global _vault_ref
    _vault_ref = vault


# ---------------------------------------------------------------------------
# Progressive tool disclosure — category activation state (AGNT-04)
# ---------------------------------------------------------------------------

#: Default categories active at session start (core CRUD operations).
_DEFAULT_ACTIVE_CATEGORIES: frozenset[str] = frozenset(
    {"creation", "mutation", "query", "graph", "lifecycle", "session"}
)

#: Session-scoped active category set (one server process = one MCP session).
_active_categories: set[str] = set(_DEFAULT_ACTIVE_CATEGORIES)


def _get_all_categories() -> set[str]:
    """Return all known category strings from the ActionRegistry."""
    return {a.category for a in get_action_registry().list_actions()}


def get_active_categories() -> set[str]:
    """Return a copy of the currently active categories."""
    return set(_active_categories)


def activate_category(category: str) -> bool:
    """Add *category* to active set.

    Returns True if the category exists in the registry and was added.
    Returns False if the category is not a known category name.
    """
    all_cats = _get_all_categories()
    if category not in all_cats:
        return False
    _active_categories.add(category)
    return True


def deactivate_category(category: str) -> bool:
    """Remove *category* from the active set.

    Returns False if the category is a default (core) category — those
    cannot be deactivated.  Returns False if the category is not currently
    active.  Returns True on successful removal.
    """
    if category in _DEFAULT_ACTIVE_CATEGORIES:
        return False
    if category not in _active_categories:
        return False
    _active_categories.discard(category)
    return True


def reset_active_categories() -> None:
    """Reset the active category set to its defaults."""
    _active_categories.clear()
    _active_categories.update(_DEFAULT_ACTIVE_CATEGORIES)


# ---------------------------------------------------------------------------
# Annotation helpers
# ---------------------------------------------------------------------------


def _build_annotations(params: tuple[ActionParam, ...]) -> dict[str, Any]:
    """Build a ``__annotations__`` dict from ActionParam descriptors.

    - Choices -> ``Literal[...]``
    - list type -> ``list[Any]`` (required) or ``list[Any] | None`` (optional)
    - dict type -> ``dict[str, Any]`` (required) or ``dict[str, Any] | None``
    - Otherwise -> ``param.type`` (required) or ``param.type | None`` (optional)
    """
    annotations: dict[str, Any] = {}
    for p in params:
        if p.choices is not None:
            # Literal type for enum-style choices
            tp = Literal[tuple(p.choices)]  # type: ignore[valid-type]
            if not p.required:
                tp = tp | None  # type: ignore[assignment]
        elif p.type is list:
            tp = list[Any] if p.required else list[Any] | None  # type: ignore[assignment]
        elif p.type is dict:
            tp = dict[str, Any] if p.required else dict[str, Any] | None  # type: ignore[assignment]
        else:
            tp = p.type if p.required else p.type | None  # type: ignore[assignment, operator]
        annotations[p.name] = tp
    return annotations


def _build_defaults(params: tuple[ActionParam, ...]) -> dict[str, Any]:
    """Build a ``__kwdefaults__`` dict from optional ActionParam descriptors."""
    return {p.name: p.default for p in params if not p.required}


# ---------------------------------------------------------------------------
# Docstring renderer
# ---------------------------------------------------------------------------


def _render_action_doc(action: ActionDefinition) -> str:
    """Build a generated MCP tool docstring from an ActionDefinition."""
    lines: list[str] = []
    lines.append(f"What it does: {action.description}")
    if action.mcp_when_to_use:
        lines.append(f"When to use: {action.mcp_when_to_use}")
    if action.mcp_avoid_when:
        lines.append(f"Avoid when: {action.mcp_avoid_when}")
    if action.side_effect == "write":
        lines.append("Side effects: write. Mutates vault state.")
    else:
        lines.append("Side effects: read. Does not mutate vault state.")
    params_with_desc = [p for p in action.params if p.description]
    if params_with_desc:
        lines.append("Args:")
        for p in params_with_desc:
            lines.append(f"- {p.name}: {p.description}")
    if action.mcp_common_errors:
        lines.append("Common errors:")
        for code in action.mcp_common_errors:
            recovery = COMMON_ERROR_RECOVERY.get(code)
            if recovery is None:
                lines.append(f"- {code}")
            else:
                lines.append(f"- {code}: {recovery}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Tool function factory
# ---------------------------------------------------------------------------


def _make_tool_fn(
    action: ActionDefinition,
    vault: Any,
) -> Callable[..., dict[str, Any]]:
    """Create a decorated tool function for an ActionDefinition.

    The produced function has an explicit signature with named parameters
    (not ``**kwargs``) so that ``inspect.signature()`` — which FastMCP uses
    to build its Pydantic input model — sees real parameter names and types.

    For actions in ``BUDGET_AWARE_ACTIONS``, an additional ``token_budget``
    keyword-only parameter (``int | None``, default ``None``) is injected.
    """
    is_budget_aware = action.name in BUDGET_AWARE_ACTIONS
    annotations = {**_build_annotations(action.params), "return": dict}
    defaults = _build_defaults(action.params)

    if is_budget_aware:
        annotations["token_budget"] = int | None
        defaults["token_budget"] = None

    # Build an explicit parameter list so inspect.signature() sees named
    # params (not **kwargs).  FastMCP uses inspect to build Pydantic models.
    # Required params are positional; optional params are keyword-only
    # (after ``*``) so __kwdefaults__ provides their defaults correctly.
    required_params = [p.name for p in action.params if p.required]
    optional_params = [p.name for p in action.params if not p.required]
    if is_budget_aware:
        optional_params.append("token_budget")

    if optional_params:
        param_str = ", ".join([*required_params, "*", *optional_params])
    else:
        param_str = ", ".join(required_params)

    handler_params = [p.name for p in action.params]
    kw_pass = ", ".join(f"{n}={n}" for n in handler_params)

    if is_budget_aware:
        fn_body = (
            f"def _fn({param_str}):\n"
            f"    result = _handler(_vault, {kw_pass})\n"
            f"    response = _McpResponse.from_result(result).model_dump(exclude_none=True)\n"
            f"    response['data'] = _budget_fn(response.get('data', {{}}), token_budget)\n"
            f"    return response\n"
        )
    else:
        fn_body = (
            f"def _fn({param_str}):\n"
            f"    result = _handler(_vault, {kw_pass})\n"
            f"    return _McpResponse.from_result(result).model_dump(exclude_none=True)\n"
        )

    local_ns: dict[str, Any] = {
        "_handler": action.handler,
        "_vault": vault,
        "_McpResponse": McpResponse,
        "_budget_fn": _apply_token_budget,
    }
    exec(fn_body, local_ns)
    tool_fn = local_ns["_fn"]

    tool_fn.__name__ = action.name
    tool_fn.__qualname__ = action.name
    tool_fn.__doc__ = _render_action_doc(action)
    tool_fn.__annotations__ = annotations
    tool_fn.__kwdefaults__ = defaults if defaults else None
    return tool_fn  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# Plugin tool shim
# ---------------------------------------------------------------------------


def _register_plugin_tools(server: Any, vault: Any) -> None:
    """Register plugin-contributed MCP tools (compatibility shim).

    No built-in plugins implement ``mcp_tool_contributions`` — this shim
    exists for future plugin support only.
    """
    plugin_manager = getattr(vault, "plugin_manager", None)
    if plugin_manager is None:
        return
    reserved = {a.name for a in get_action_registry().list_actions()}
    for contribution in plugin_manager.mcp_tool_contributions(reserved_names=reserved):

        def _make_plugin_wrapper(_contribution: Any, _vault: Any) -> Callable[..., dict[str, Any]]:
            def wrapped(**kwargs: Any) -> dict[str, Any]:
                return _contribution.handler(_vault, **kwargs)  # type: ignore[no-any-return]

            wrapped.__name__ = _contribution.name
            return wrapped

        server.tool()(_make_plugin_wrapper(contribution, vault))


# ---------------------------------------------------------------------------
# Catalog compatibility shim
# ---------------------------------------------------------------------------
#
# ``tool_catalog()`` and ``common_error_recovery()`` provide the same
# TypedDict-shaped data that the old ``mcp/tools.py`` exported.  Callers
# that consumed the old module (resources.py, prompts.py, catalogs.py,
# test_prompts.py) can import from here without behavioural change.


def _action_to_catalog_entry(action: ActionDefinition) -> dict[str, Any]:
    """Convert an ActionDefinition to a legacy ToolCatalogEntry-shaped dict."""
    return {
        "name": action.name,
        "category": action.category,
        "description": action.description,
        "when_to_use": action.mcp_when_to_use,
        "avoid_when": action.mcp_avoid_when,
        "side_effect": action.side_effect,
        "common_errors": action.mcp_common_errors,
        "args_guidance": {p.name: p.description for p in action.params if p.description},
    }


def tool_catalog(vault: Any = None) -> tuple[dict[str, Any], ...]:
    """Return the MCP tool catalog as TypedDict-shaped dicts.

    Compatibility shim — replaces ``mcp/tools.tool_catalog()``.
    Plugin contributions are included when *vault* provides a
    ``plugin_manager`` with ``mcp_tool_contributions()``.
    """
    registry = get_action_registry()
    entries = [_action_to_catalog_entry(a) for a in registry.list_actions()]

    plugin_manager = getattr(vault, "plugin_manager", None) if vault is not None else None
    if plugin_manager is not None:
        reserved = {a.name for a in registry.list_actions()}
        for contribution in plugin_manager.mcp_tool_contributions(reserved_names=reserved):
            entries.append(contribution.catalog_entry)

    return tuple(entries)


def common_error_recovery() -> dict[str, str]:
    """Return shared recovery guidance for MCP-exposed error codes.

    Compatibility shim — replaces ``mcp/tools.common_error_recovery()``.
    """
    return dict(COMMON_ERROR_RECOVERY)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def generate_tools(server: Any, vault: Any) -> None:
    """Register all ActionRegistry-driven MCP tools on *server*.

    Iterates ``get_action_registry().list_actions()``, creates a tool
    function for each via ``_make_tool_fn()``, and registers it with
    ``server.tool()(fn)``.  Also calls ``_register_plugin_tools()`` for
    compatibility with future plugin contributions.
    """
    set_vault(vault)
    registry = get_action_registry()
    for action in registry.list_actions():
        fn = _make_tool_fn(action, vault)
        server.tool()(fn)
    _register_plugin_tools(server, vault)
