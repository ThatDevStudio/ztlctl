"""Tests for ActionParam and ActionDefinition frozen dataclasses."""

from __future__ import annotations

import pytest
from ztlctl.actions.definitions import ActionDefinition, ActionParam

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_DUMMY_HANDLER = lambda **kw: None  # noqa: E731


def _make_param(**kwargs: object) -> ActionParam:
    """Return a minimal ActionParam, overriding fields with *kwargs*."""
    defaults: dict[str, object] = {"name": "query", "type": str}
    defaults.update(kwargs)
    return ActionParam(**defaults)  # type: ignore[arg-type]


def _make_action(**kwargs: object) -> ActionDefinition:
    """Return a minimal ActionDefinition, overriding fields with *kwargs*."""
    defaults: dict[str, object] = {
        "name": "note.search",
        "description": "Search notes by keyword.",
        "category": "query",
        "params": (_make_param(),),
        "handler": _DUMMY_HANDLER,
        "side_effect": "read",
    }
    defaults.update(kwargs)
    return ActionDefinition(**defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# TestActionParam
# ---------------------------------------------------------------------------


class TestActionParam:
    def test_required_fields(self) -> None:
        """ActionParam can be created with name and type only."""
        param = ActionParam(name="query", type=str)
        assert param.name == "query"
        assert param.type is str

    def test_default_fields(self) -> None:
        """Optional fields have sensible defaults."""
        param = ActionParam(name="query", type=str)
        assert param.required is True
        assert param.default is None
        assert param.description == ""
        assert param.choices is None
        assert param.cli_multiple is False
        assert param.cli_is_argument is False
        assert param.cli_flag is False
        assert param.mcp_example == ""

    def test_frozen(self) -> None:
        """ActionParam is immutable (frozen dataclass)."""
        param = ActionParam(name="query", type=str)
        with pytest.raises((TypeError, AttributeError)):
            param.name = "changed"  # type: ignore[misc]

    def test_choices_tuple(self) -> None:
        """ActionParam stores choices as a tuple."""
        param = ActionParam(name="status", type=str, choices=("open", "closed"))
        assert param.choices == ("open", "closed")

    def test_cli_multiple_flag(self) -> None:
        """ActionParam with cli_multiple=True stores True."""
        param = ActionParam(name="tags", type=str, cli_multiple=True)
        assert param.cli_multiple is True

    def test_cli_is_argument(self) -> None:
        """ActionParam with cli_is_argument=True stores True."""
        param = ActionParam(name="id", type=str, cli_is_argument=True)
        assert param.cli_is_argument is True

    def test_cli_flag(self) -> None:
        """ActionParam with cli_flag=True stores True."""
        param = ActionParam(name="verbose", type=bool, cli_flag=True)
        assert param.cli_flag is True

    def test_mcp_example(self) -> None:
        """ActionParam with mcp_example stores the string."""
        param = ActionParam(name="query", type=str, mcp_example="find notes about python")
        assert param.mcp_example == "find notes about python"

    def test_not_required_with_default(self) -> None:
        """ActionParam can be optional with a default value."""
        param = ActionParam(name="limit", type=int, required=False, default=20)
        assert param.required is False
        assert param.default == 20


# ---------------------------------------------------------------------------
# TestActionDefinition
# ---------------------------------------------------------------------------


class TestActionDefinition:
    def test_required_fields(self) -> None:
        """ActionDefinition can be created with all required fields."""
        action = _make_action()
        assert action.name == "note.search"
        assert action.description == "Search notes by keyword."
        assert action.category == "query"
        assert len(action.params) == 1
        assert action.handler is _DUMMY_HANDLER
        assert action.side_effect == "read"

    def test_default_fields(self) -> None:
        """Optional fields have sensible defaults."""
        action = _make_action()
        assert action.mcp_when_to_use == ""
        assert action.mcp_avoid_when == ""
        assert action.mcp_common_errors == ()
        assert action.cli_group is None
        assert action.cli_examples == ""
        assert action.cli_interactive_params == ()
        assert action.custom_presentation is False

    def test_frozen(self) -> None:
        """ActionDefinition is immutable (frozen dataclass)."""
        action = _make_action()
        with pytest.raises((TypeError, AttributeError)):
            action.name = "changed"  # type: ignore[misc]

    def test_hashable(self) -> None:
        """ActionDefinition can be added to a set (hashable)."""
        action = _make_action()
        action_set = {action}
        assert action in action_set

    def test_custom_presentation(self) -> None:
        """ActionDefinition with custom_presentation=True stores True."""
        action = _make_action(custom_presentation=True)
        assert action.custom_presentation is True

    def test_mcp_metadata(self) -> None:
        """MCP metadata fields are stored correctly."""
        action = _make_action(
            mcp_when_to_use="when searching notes",
            mcp_avoid_when="for write operations",
            mcp_common_errors=("vault not initialized",),
        )
        assert action.mcp_when_to_use == "when searching notes"
        assert action.mcp_avoid_when == "for write operations"
        assert action.mcp_common_errors == ("vault not initialized",)

    def test_cli_metadata(self) -> None:
        """CLI metadata fields are stored correctly."""
        action = _make_action(
            cli_group="notes",
            cli_examples="ztlctl notes search python",
            cli_interactive_params=("query",),
        )
        assert action.cli_group == "notes"
        assert action.cli_examples == "ztlctl notes search python"
        assert action.cli_interactive_params == ("query",)

    def test_side_effect_write(self) -> None:
        """ActionDefinition accepts side_effect='write'."""
        action = _make_action(name="note.create", side_effect="write")
        assert action.side_effect == "write"

    def test_params_tuple(self) -> None:
        """ActionDefinition stores params as a tuple."""
        p1 = _make_param(name="query")
        p2 = _make_param(name="limit", type=int, required=False)
        action = _make_action(params=(p1, p2))
        assert len(action.params) == 2
        assert action.params[0].name == "query"
        assert action.params[1].name == "limit"
