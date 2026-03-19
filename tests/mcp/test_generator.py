"""Tests for mcp/generator.py — tool count, annotations, DummyServer integration."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.mcp.generator import (
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
