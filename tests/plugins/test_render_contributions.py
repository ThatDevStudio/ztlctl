"""Tests for RenderContribution and register_render_contributions hookspec (PLUG-06)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pluggy
import pytest

from ztlctl.plugins.contracts import RenderContribution
from ztlctl.plugins.hookspecs import ZtlctlHookSpec
from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _rich_fmt(data: dict[str, Any]) -> str:
    return f"[bold]{data.get('title', '')}[/bold]"


def _mcp_fmt(data: dict[str, Any]) -> dict[str, Any]:
    return {"formatted": True, "title": data.get("title", "")}


# ---------------------------------------------------------------------------
# RenderContribution dataclass
# ---------------------------------------------------------------------------


class TestRenderContributionDataclass:
    def test_render_contribution_frozen(self) -> None:
        """RenderContribution is immutable (frozen dataclass)."""
        rc = RenderContribution(
            note_type="sprint",
            rich_formatter=_rich_fmt,
            mcp_formatter=_mcp_fmt,
        )
        with pytest.raises((AttributeError, TypeError)):
            rc.note_type = "changed"  # type: ignore[misc]

    def test_rich_formatter_called(self) -> None:
        """rich_formatter is callable and returns a string."""
        mock_formatter = MagicMock(return_value="[bold]Sprint[/bold]")
        rc = RenderContribution(
            note_type="sprint",
            rich_formatter=mock_formatter,
            mcp_formatter=_mcp_fmt,
        )
        result = rc.rich_formatter({"title": "Sprint"})
        mock_formatter.assert_called_once_with({"title": "Sprint"})
        assert result == "[bold]Sprint[/bold]"

    def test_mcp_formatter_called(self) -> None:
        """mcp_formatter is callable and returns a dict."""
        mock_formatter = MagicMock(return_value={"formatted": True})
        rc = RenderContribution(
            note_type="sprint",
            rich_formatter=_rich_fmt,
            mcp_formatter=mock_formatter,
        )
        result = rc.mcp_formatter({"title": "Sprint"})
        mock_formatter.assert_called_once_with({"title": "Sprint"})
        assert result == {"formatted": True}

    def test_render_contribution_stores_note_type(self) -> None:
        """RenderContribution stores note_type correctly."""
        rc = RenderContribution(
            note_type="sprint",
            rich_formatter=_rich_fmt,
            mcp_formatter=_mcp_fmt,
        )
        assert rc.note_type == "sprint"


# ---------------------------------------------------------------------------
# register_render_contributions hookspec + PluginManager.render_contributions()
# ---------------------------------------------------------------------------


def _make_loaded_pm(plugin: object) -> PluginManager:
    """Return a PluginManager with plugin registered and _loaded=True."""
    pm = PluginManager()
    pm.register_plugin(plugin)
    pm._loaded = True
    return pm


class TestRenderContributionsCollection:
    def test_collection_from_plugin(self) -> None:
        """render_contributions() returns RenderContribution from plugin."""

        class _SprintRenderPlugin:
            @hookimpl
            def register_render_contributions(self) -> list[RenderContribution]:
                return [
                    RenderContribution(
                        note_type="sprint",
                        rich_formatter=_rich_fmt,
                        mcp_formatter=_mcp_fmt,
                    )
                ]

        pm = _make_loaded_pm(_SprintRenderPlugin())
        contributions = pm.render_contributions()
        assert len(contributions) == 1
        assert contributions[0].note_type == "sprint"

    def test_duplicate_render_contribution_skipped(self) -> None:
        """Two plugins returning same note_type: second is skipped with warning."""

        class _Plugin1:
            @hookimpl
            def register_render_contributions(self) -> list[RenderContribution]:
                return [
                    RenderContribution(
                        note_type="sprint",
                        rich_formatter=_rich_fmt,
                        mcp_formatter=_mcp_fmt,
                    )
                ]

        class _Plugin2:
            @hookimpl
            def register_render_contributions(self) -> list[RenderContribution]:
                return [
                    RenderContribution(
                        note_type="sprint",
                        rich_formatter=lambda d: "alt",
                        mcp_formatter=lambda d: {},
                    )
                ]

        pm = PluginManager()
        pm.register_plugin(_Plugin1())
        pm.register_plugin(_Plugin2())
        pm._loaded = True
        contributions = pm.render_contributions()
        # Only one "sprint" entry — duplicate skipped
        sprint_contribs = [c for c in contributions if c.note_type == "sprint"]
        assert len(sprint_contribs) == 1

    def test_empty_when_no_plugins(self) -> None:
        """render_contributions() returns empty list when no plugins registered."""
        pm = PluginManager()
        pm._loaded = True
        contributions = pm.render_contributions()
        assert contributions == []

    def test_hookspec_registered(self) -> None:
        """register_render_contributions hookspec exists on ZtlctlHookSpec."""
        assert hasattr(ZtlctlHookSpec, "register_render_contributions")

    def test_render_contributions_not_loaded_returns_empty(self) -> None:
        """render_contributions() returns empty list when not loaded."""

        class _Plugin:
            @hookimpl
            def register_render_contributions(self) -> list[RenderContribution]:
                return [
                    RenderContribution(
                        note_type="sprint",
                        rich_formatter=_rich_fmt,
                        mcp_formatter=_mcp_fmt,
                    )
                ]

        pm = PluginManager()
        pm.register_plugin(_Plugin())
        # _loaded is False by default
        assert pm.render_contributions() == []
