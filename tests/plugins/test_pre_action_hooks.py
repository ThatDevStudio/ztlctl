"""Tests for pre_action/post_action hookspecs and ActionRejection (PLUG-02)."""

from __future__ import annotations

from typing import Any

import pluggy
import pytest

from ztlctl.plugins.contracts import ActionRejection
from ztlctl.plugins.hookspecs import ZtlctlHookSpec

hookimpl = pluggy.HookimplMarker("ztlctl")


def _make_pm() -> pluggy.PluginManager:
    """Create a fresh pluggy PluginManager with the ztlctl hookspecs."""
    pm = pluggy.PluginManager("ztlctl")
    pm.add_hookspecs(ZtlctlHookSpec)
    return pm


class TestActionRejection:
    def test_action_rejection_frozen(self) -> None:
        """ActionRejection is immutable (frozen dataclass)."""
        rejection = ActionRejection(reason="blocked")
        with pytest.raises((AttributeError, TypeError)):
            rejection.reason = "modified"  # type: ignore[misc]

    def test_action_rejection_defaults(self) -> None:
        """ActionRejection has correct defaults."""
        rejection = ActionRejection(reason="blocked")
        assert rejection.reason == "blocked"
        assert rejection.code == "plugin_rejected"
        assert rejection.detail == {}

    def test_action_rejection_custom(self) -> None:
        """ActionRejection accepts custom code and detail."""
        rejection = ActionRejection(
            reason="quota exceeded",
            code="rate_limit",
            detail={"limit": 100, "current": 101},
        )
        assert rejection.reason == "quota exceeded"
        assert rejection.code == "rate_limit"
        assert rejection.detail == {"limit": 100, "current": 101}


class TestPreActionHookspec:
    def test_rejection_aborts_action(self) -> None:
        """A plugin returning ActionRejection causes firstresult to return it."""
        pm = _make_pm()

        class RejectingPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                return ActionRejection(reason="blocked by test")

        pm.register(RejectingPlugin())
        result = pm.hook.pre_action(action_name="create", kwargs={"title": "test"})
        assert isinstance(result, ActionRejection)
        assert result.reason == "blocked by test"

    def test_modified_kwargs_used(self) -> None:
        """A plugin returning a dict causes firstresult to return that dict."""
        pm = _make_pm()

        class ModifyingPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                modified = dict(kwargs)
                modified["query"] = "modified"
                return modified

        pm.register(ModifyingPlugin())
        result = pm.hook.pre_action(action_name="search", kwargs={"query": "original"})
        assert isinstance(result, dict)
        assert result["query"] == "modified"

    def test_none_return_passthrough(self) -> None:
        """A plugin returning None allows firstresult to pass through (no result)."""
        pm = _make_pm()

        class PassthroughPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                return None

        pm.register(PassthroughPlugin())
        result = pm.hook.pre_action(action_name="create", kwargs={})
        # firstresult with all None returns None
        assert result is None

    def test_no_plugins_returns_none(self) -> None:
        """With no plugins registered, pre_action returns None (firstresult default)."""
        pm = _make_pm()
        result = pm.hook.pre_action(action_name="create", kwargs={"title": "test"})
        assert result is None

    def test_first_non_none_wins(self) -> None:
        """First plugin returning non-None wins; later plugins are not called."""
        pm = _make_pm()
        calls: list[str] = []

        class FirstPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                calls.append("first")
                return ActionRejection(reason="first wins")

        class SecondPlugin:
            @hookimpl
            def pre_action(self, action_name: str, kwargs: dict[str, Any]) -> Any:
                calls.append("second")
                return ActionRejection(reason="second (should not win)")

        pm.register(FirstPlugin())
        pm.register(SecondPlugin())
        result = pm.hook.pre_action(action_name="create", kwargs={})
        assert isinstance(result, ActionRejection)
        # With firstresult, pluggy calls plugins in LIFO order and stops at first non-None
        assert result.reason in ("first wins", "second (should not win)")
        # Only one plugin should have been called
        assert len(calls) == 1


class TestPostActionHookspec:
    def test_post_action_fires(self) -> None:
        """post_action fires after action execution with correct args."""
        pm = _make_pm()
        fired: list[dict[str, Any]] = []

        class ObservingPlugin:
            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                fired.append({"action_name": action_name, "kwargs": kwargs, "result": result})

        pm.register(ObservingPlugin())
        mock_result = object()
        pm.hook.post_action(
            action_name="create",
            kwargs={"title": "test"},
            result=mock_result,
        )

        assert len(fired) == 1
        assert fired[0]["action_name"] == "create"
        assert fired[0]["kwargs"] == {"title": "test"}
        assert fired[0]["result"] is mock_result

    def test_post_action_no_return_value(self) -> None:
        """post_action collects None return values (no firstresult)."""
        pm = _make_pm()

        class SilentPlugin:
            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                pass

        pm.register(SilentPlugin())
        results = pm.hook.post_action(action_name="create", kwargs={}, result=None)
        # Non-firstresult hooks return a list (of None values)
        assert isinstance(results, list)

    def test_multiple_post_action_plugins_all_fire(self) -> None:
        """Multiple plugins each receive post_action calls."""
        pm = _make_pm()
        counts: list[int] = [0]

        class PluginA:
            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                counts[0] += 1

        class PluginB:
            @hookimpl
            def post_action(self, action_name: str, kwargs: dict[str, Any], result: Any) -> None:
                counts[0] += 1

        pm.register(PluginA())
        pm.register(PluginB())
        pm.hook.post_action(action_name="create", kwargs={}, result=None)
        assert counts[0] == 2
