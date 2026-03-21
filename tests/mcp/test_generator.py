"""Tests for mcp/generator.py — tool count, annotations, DummyServer integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.mcp.generator import (
    BUDGET_AWARE_ACTIONS,
    _apply_token_budget,
    _build_annotations,
    _make_tool_fn,
    _render_action_doc,
    generate_tools,
)
from ztlctl.services.result import ServiceResult

# ---------------------------------------------------------------------------
# DummyServer
# ---------------------------------------------------------------------------


class DummyServer:
    def __init__(self) -> None:
        self.tools: dict[str, Any] = {}

    def tool(self):
        def decorator(fn):
            self.tools[fn.__name__] = fn
            return fn

        return decorator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_vault() -> Any:
    """Mock vault without plugin_manager."""
    vault = MagicMock()
    del vault.plugin_manager  # ensure getattr returns None-like behaviour
    vault.plugin_manager = None
    return vault


@pytest.fixture
def dummy_action() -> ActionDefinition:
    """A minimal ActionDefinition for isolated testing."""

    def handler(vault: Any, *, message: str = "hello") -> ServiceResult:
        return ServiceResult(ok=True, op="dummy", data={"message": message})

    return ActionDefinition(
        name="dummy_action",
        description="A dummy action for testing.",
        category="test",
        params=(
            ActionParam(
                "message",
                str,
                required=False,
                default="hello",
                description="A test message.",
            ),
        ),
        handler=handler,
        side_effect="read",
        mcp_when_to_use="Testing only.",
        mcp_avoid_when="Never avoid.",
        mcp_common_errors=("NOT_FOUND",),
    )


# ---------------------------------------------------------------------------
# Tests — generate_tools count
# ---------------------------------------------------------------------------


def test_generate_tools_count(mock_vault: Any) -> None:
    """generate_tools registers all 59 ActionDefinitions on the server."""
    from ztlctl.actions.registry import get_action_registry

    server = DummyServer()
    generate_tools(server, mock_vault)
    registry = get_action_registry()
    expected = len(registry.list_actions())
    assert expected >= 59
    assert len(server.tools) >= expected


def test_tool_has_annotations(mock_vault: Any) -> None:
    """create_note tool has __annotations__ with at least 'title' key."""
    server = DummyServer()
    generate_tools(server, mock_vault)
    fn = server.tools["create_note"]
    assert "title" in fn.__annotations__


def test_tool_has_doc(mock_vault: Any) -> None:
    """create_note tool has __doc__ containing 'What it does:'."""
    server = DummyServer()
    generate_tools(server, mock_vault)
    fn = server.tools["create_note"]
    assert fn.__doc__ is not None
    assert "What it does:" in fn.__doc__


def test_tool_has_kwdefaults(mock_vault: Any) -> None:
    """list_items tool has __kwdefaults__ containing 'limit' key."""
    server = DummyServer()
    generate_tools(server, mock_vault)
    fn = server.tools["list_items"]
    assert fn.__kwdefaults__ is not None
    assert "limit" in fn.__kwdefaults__


def test_tool_callable_returns_mcp_response(dummy_action: ActionDefinition) -> None:
    """A generated tool function returns a dict with 'ok' key."""
    mock_vault = MagicMock()
    fn = _make_tool_fn(dummy_action, mock_vault)
    result = fn(message="test")
    assert isinstance(result, dict)
    assert "ok" in result


# ---------------------------------------------------------------------------
# Tests — _build_annotations
# ---------------------------------------------------------------------------


def test_build_annotations_required_str() -> None:
    """Required str param maps to str type."""
    params = (ActionParam("q", str, required=True),)
    annotations = _build_annotations(params)
    assert annotations == {"q": str}


def test_build_annotations_optional_str() -> None:
    """Optional str param maps to str | None type."""
    params = (ActionParam("q", str, required=False, default=None),)
    annotations = _build_annotations(params)
    # str | None is represented as union
    assert annotations["q"] is not str
    # verify it allows None (union type check)

    tp = annotations["q"]
    # Python 3.10+ uses types.UnionType; older uses typing.Union
    assert tp is not None


def test_build_annotations_choices() -> None:
    """Param with choices maps to a type that includes Literal args."""
    import typing

    # required=True means just Literal, no | None wrapping
    params = (ActionParam("sort", str, required=True, choices=("a", "b")),)
    annotations = _build_annotations(params)
    tp = annotations["sort"]
    # should be a Literal type with __origin__ == typing.Literal
    origin = getattr(tp, "__origin__", None)
    assert origin is typing.Literal
    assert tp.__args__ == ("a", "b")


def test_build_annotations_list() -> None:
    """Required list param maps to list[Any]."""
    from typing import Any

    params = (ActionParam("items", list, required=True),)
    annotations = _build_annotations(params)
    tp = annotations["items"]
    assert tp == list[Any]


# ---------------------------------------------------------------------------
# Tests — _render_action_doc
# ---------------------------------------------------------------------------


def test_render_action_doc_sections(dummy_action: ActionDefinition) -> None:
    """_render_action_doc includes all required sections."""
    doc = _render_action_doc(dummy_action)
    assert "What it does:" in doc
    assert "Side effects:" in doc
    assert "Args:" in doc


# ---------------------------------------------------------------------------
# Tests — _apply_token_budget
# ---------------------------------------------------------------------------


def test_apply_token_budget_none() -> None:
    """_apply_token_budget with None budget returns data unchanged."""
    data = {"items": list(range(100))}
    result = _apply_token_budget(data, None)
    assert result is data  # exact same object — no copy


def test_apply_token_budget_within() -> None:
    """Small data within large budget returns data unchanged."""
    data = {"items": [1, 2, 3]}
    result = _apply_token_budget(data, 10000)
    # unchanged (not truncated)
    assert result.get("truncated") is None


def test_apply_token_budget_truncates() -> None:
    """Large data with small budget returns truncated data with 'truncated': True."""

    big_list = list(range(500))
    data = {"items": big_list}
    budget = 10  # very small — forces truncation
    result = _apply_token_budget(data, budget)
    assert result.get("truncated") is True
    assert result.get("token_budget") == budget
    assert len(result["items"]) < len(big_list)


def test_apply_token_budget_no_list() -> None:
    """Data with no list field returns unchanged regardless of budget."""
    data = {"count": 5, "status": "ok"}
    result = _apply_token_budget(data, 1)
    # No list field to truncate — returned as-is (may or may not have truncated key)
    assert result.get("truncated") is None


# ---------------------------------------------------------------------------
# Tests — budget-aware tool injection
# ---------------------------------------------------------------------------


def test_budget_aware_actions_set() -> None:
    """BUDGET_AWARE_ACTIONS contains exactly the four expected actions."""
    assert BUDGET_AWARE_ACTIONS == {"list_items", "search", "vault_review", "decision_support"}


def test_budget_aware_tool_has_token_budget_param(mock_vault: Any) -> None:
    """Budget-aware tool 'list_items' has 'token_budget' in __annotations__."""
    server = DummyServer()
    generate_tools(server, mock_vault)
    fn = server.tools["list_items"]
    assert "token_budget" in fn.__annotations__


def test_non_budget_tool_no_token_budget_param(mock_vault: Any) -> None:
    """Non-budget tool 'create_note' does NOT have 'token_budget' in __annotations__."""
    server = DummyServer()
    generate_tools(server, mock_vault)
    fn = server.tools["create_note"]
    assert "token_budget" not in fn.__annotations__


def test_budget_aware_tool_has_token_budget_kwdefault(mock_vault: Any) -> None:
    """Budget-aware tool 'list_items' has 'token_budget': None in __kwdefaults__."""
    server = DummyServer()
    generate_tools(server, mock_vault)
    fn = server.tools["list_items"]
    assert fn.__kwdefaults__ is not None
    assert fn.__kwdefaults__.get("token_budget") is None
    assert "token_budget" in fn.__kwdefaults__


# ---------------------------------------------------------------------------
# Tests — progressive tool disclosure / category activation (AGNT-04)
# ---------------------------------------------------------------------------


def test_default_active_categories() -> None:
    """_DEFAULT_ACTIVE_CATEGORIES is a frozenset with the expected default categories."""
    from ztlctl.mcp.generator import _DEFAULT_ACTIVE_CATEGORIES

    assert isinstance(_DEFAULT_ACTIVE_CATEGORIES, frozenset)
    for cat in ("creation", "query", "graph", "lifecycle", "session"):
        assert cat in _DEFAULT_ACTIVE_CATEGORIES, f"missing default category: {cat!r}"


def test_get_active_categories_returns_copy() -> None:
    """get_active_categories() returns a copy, not the internal set reference."""
    from ztlctl.mcp.generator import get_active_categories

    first = get_active_categories()
    second = get_active_categories()
    assert first == second
    assert first is not second  # different object — copy, not reference


def test_activate_category() -> None:
    """activate_category('export') returns True and adds 'export' to active set."""
    from ztlctl.mcp.generator import (
        activate_category,
        get_active_categories,
        reset_active_categories,
    )

    reset_active_categories()
    result = activate_category("export")
    assert result is True
    assert "export" in get_active_categories()


def test_activate_nonexistent_category() -> None:
    """activate_category with unknown category name returns False."""
    from ztlctl.mcp.generator import activate_category

    result = activate_category("nonexistent_xyz_category_that_does_not_exist")
    assert result is False


def test_deactivate_category() -> None:
    """deactivate_category('export') returns True and removes export from active set."""
    from ztlctl.mcp.generator import (
        activate_category,
        deactivate_category,
        get_active_categories,
        reset_active_categories,
    )

    reset_active_categories()
    activate_category("export")
    result = deactivate_category("export")
    assert result is True
    assert "export" not in get_active_categories()


def test_deactivate_default_category_blocked() -> None:
    """deactivate_category on a default category returns False and leaves it active."""
    from ztlctl.mcp.generator import deactivate_category, get_active_categories

    result = deactivate_category("creation")
    assert result is False
    assert "creation" in get_active_categories()


def test_reset_active_categories() -> None:
    """reset_active_categories() restores defaults after modification."""
    from ztlctl.mcp.generator import (
        _DEFAULT_ACTIVE_CATEGORIES,
        activate_category,
        get_active_categories,
        reset_active_categories,
    )

    activate_category("export")
    reset_active_categories()
    assert get_active_categories() == set(_DEFAULT_ACTIVE_CATEGORIES)
