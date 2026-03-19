"""Tests for ActionRegistry and get_action_registry."""

from __future__ import annotations

import pytest
from ztlctl.actions.registry import ActionRegistry, get_action_registry

from ztlctl.actions.definitions import ActionDefinition, ActionParam

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_DUMMY_HANDLER = lambda **kw: None  # noqa: E731


def _make_param(name: str = "query", type_: type = str) -> ActionParam:
    """Return a minimal ActionParam."""
    return ActionParam(name=name, type=type_)


def _make_action(
    name: str = "note.search",
    category: str = "query",
    side_effect: str = "read",
    custom_presentation: bool = False,
) -> ActionDefinition:
    """Return a minimal ActionDefinition with the given fields."""
    return ActionDefinition(
        name=name,
        description=f"Description for {name}.",
        category=category,
        params=(_make_param(),),
        handler=_DUMMY_HANDLER,
        side_effect=side_effect,  # type: ignore[arg-type]
        custom_presentation=custom_presentation,
    )


# ---------------------------------------------------------------------------
# TestActionRegistry
# ---------------------------------------------------------------------------


class TestActionRegistry:
    def test_register_and_get(self) -> None:
        """register() stores ActionDefinition; get() retrieves it by name."""
        registry = ActionRegistry()
        action = _make_action()
        registry.register(action)
        assert registry.get("note.search") is action

    def test_duplicate_raises(self) -> None:
        """Registering the same name twice raises ValueError."""
        registry = ActionRegistry()
        action = _make_action()
        registry.register(action)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(action)

    def test_get_missing_raises(self) -> None:
        """get() raises KeyError for an unregistered name."""
        registry = ActionRegistry()
        with pytest.raises(KeyError, match="No action registered"):
            registry.get("nonexistent")

    def test_list_actions_all(self) -> None:
        """list_actions() with no filters returns all registered actions."""
        registry = ActionRegistry()
        a1 = _make_action(name="note.search", category="query", side_effect="read")
        a2 = _make_action(name="note.create", category="create", side_effect="write")
        registry.register(a1)
        registry.register(a2)
        all_actions = registry.list_actions()
        assert len(all_actions) == 2
        names = {a.name for a in all_actions}
        assert names == {"note.search", "note.create"}

    def test_list_actions_by_category(self) -> None:
        """list_actions(category=...) returns only actions in that category."""
        registry = ActionRegistry()
        a1 = _make_action(name="note.search", category="query")
        a2 = _make_action(name="note.list", category="query")
        a3 = _make_action(name="note.create", category="create", side_effect="write")
        registry.register(a1)
        registry.register(a2)
        registry.register(a3)
        query_actions = registry.list_actions(category="query")
        assert len(query_actions) == 2
        names = {a.name for a in query_actions}
        assert names == {"note.search", "note.list"}

    def test_list_actions_by_side_effect(self) -> None:
        """list_actions(side_effect=...) filters by read/write."""
        registry = ActionRegistry()
        a1 = _make_action(name="note.search", side_effect="read")
        a2 = _make_action(name="note.create", category="create", side_effect="write")
        a3 = _make_action(name="note.get", category="query", side_effect="read")
        registry.register(a1)
        registry.register(a2)
        registry.register(a3)
        read_actions = registry.list_actions(side_effect="read")
        assert len(read_actions) == 2
        write_actions = registry.list_actions(side_effect="write")
        assert len(write_actions) == 1
        assert write_actions[0].name == "note.create"

    def test_list_actions_by_custom_presentation(self) -> None:
        """list_actions(custom_presentation=True) returns only custom_presentation actions."""
        registry = ActionRegistry()
        a1 = _make_action(name="note.search", custom_presentation=False)
        a2 = _make_action(name="note.special", custom_presentation=True)
        registry.register(a1)
        registry.register(a2)
        custom_actions = registry.list_actions(custom_presentation=True)
        assert len(custom_actions) == 1
        assert custom_actions[0].name == "note.special"
        standard_actions = registry.list_actions(custom_presentation=False)
        assert len(standard_actions) == 1
        assert standard_actions[0].name == "note.search"

    def test_list_actions_combined_filters(self) -> None:
        """list_actions() with multiple filters combines them (AND logic)."""
        registry = ActionRegistry()
        a1 = _make_action(name="note.search", category="query", side_effect="read")
        a2 = _make_action(name="note.create", category="create", side_effect="write")
        a3 = _make_action(
            name="note.analyze", category="query", side_effect="read", custom_presentation=True
        )
        registry.register(a1)
        registry.register(a2)
        registry.register(a3)
        result = registry.list_actions(
            category="query", side_effect="read", custom_presentation=True
        )
        assert len(result) == 1
        assert result[0].name == "note.analyze"

    def test_empty_registry(self) -> None:
        """list_actions() on empty registry returns empty list."""
        registry = ActionRegistry()
        assert registry.list_actions() == []


# ---------------------------------------------------------------------------
# TestGetActionRegistry
# ---------------------------------------------------------------------------


class TestGetActionRegistry:
    def test_returns_singleton(self) -> None:
        """get_action_registry() returns the same instance on repeated calls."""
        r1 = get_action_registry()
        r2 = get_action_registry()
        assert r1 is r2
