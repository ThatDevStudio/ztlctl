"""MCP tool generator — ActionRegistry-driven tool registration.

Replaces hand-written ``tools.py`` with auto-generated MCP tools derived
from ActionDefinitions.  ``generate_tools()`` iterates the registry and
calls ``server.tool()`` for each action, producing correct
``__annotations__``, ``__kwdefaults__``, and ``__doc__`` without needing
the mcp package at import time.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.actions.registry import get_action_registry
from ztlctl.mcp.response import COMMON_ERROR_RECOVERY, McpResponse

# ---------------------------------------------------------------------------
# Module-level vault reference (server-scoped, set once per create_server call)
# ---------------------------------------------------------------------------

_vault_ref: Any = None


def set_vault(vault: Any) -> None:
    """Set the module-level vault reference."""
    global _vault_ref
    _vault_ref = vault


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

    The produced function has:
    - ``__name__`` == ``action.name``
    - ``__doc__`` == rendered docstring
    - ``__annotations__`` == mapped from action.params
    - ``__kwdefaults__`` == defaults for optional params (or None if none)

    Note: ``functools.wraps`` is intentionally NOT used — it would overwrite
    the dynamically set ``__annotations__`` breaking ``inspect.signature()``.
    """

    def tool_fn(**kwargs: Any) -> dict[str, Any]:
        result = action.handler(vault, **kwargs)
        return McpResponse.from_result(result).model_dump(exclude_none=True)

    tool_fn.__name__ = action.name
    tool_fn.__doc__ = _render_action_doc(action)
    tool_fn.__annotations__ = {**_build_annotations(action.params), "return": dict}
    defaults = _build_defaults(action.params)
    tool_fn.__kwdefaults__ = defaults if defaults else None
    return tool_fn


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
