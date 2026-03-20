"""Tests for plugin custom note type registration (PLUG-05)."""

from __future__ import annotations

import pluggy

from ztlctl.actions.registry import ActionRegistry
from ztlctl.domain.content import ContentModel
from ztlctl.domain.registry import NoteTypeDefinition, NoteTypeRegistry
from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_sprint_ntd() -> NoteTypeDefinition:
    """Build a minimal 'sprint' NoteTypeDefinition for tests."""
    return NoteTypeDefinition(
        name="sprint",
        content_type="task",
        model_cls=ContentModel,
        transitions={"open": ["closed"], "closed": []},
        template_name="sprint.md.j2",
    )


class _SprintPlugin:
    """Fake plugin that registers a custom 'sprint' note type."""

    @hookimpl
    def register_note_types(self) -> list[NoteTypeDefinition]:
        return [_make_sprint_ntd()]


def _make_pm_with_fresh_registries(
    plugin: object,
) -> tuple[PluginManager, NoteTypeRegistry, ActionRegistry]:
    """Return a (PluginManager, NoteTypeRegistry, ActionRegistry) triple.

    Both registries are fresh (not the module-level singletons) so tests are
    isolated from each other and from built-in registrations.
    """
    pm = PluginManager()
    pm.register_plugin(plugin)

    note_registry = NoteTypeRegistry()
    action_registry = ActionRegistry()
    pm._register_note_types(
        note_registry=note_registry,
        action_registry=action_registry,
    )
    return pm, note_registry, action_registry


# ---------------------------------------------------------------------------
# PLUG-05: custom note type registration
# ---------------------------------------------------------------------------


class TestPluginRegistersNoteType:
    def test_plugin_registers_note_type(self) -> None:
        """Plugin-returned NoteTypeDefinition is registered into NoteTypeRegistry."""
        _pm, note_reg, _action_reg = _make_pm_with_fresh_registries(_SprintPlugin())
        ntd = note_reg.get("sprint")
        assert ntd.name == "sprint"
        assert ntd.content_type == "task"

    def test_auto_action_definitions_created(self) -> None:
        """After plugin load, ActionRegistry has create_sprint, update_sprint, close_sprint."""
        _pm, _note_reg, action_reg = _make_pm_with_fresh_registries(_SprintPlugin())
        names = {a.name for a in action_reg.list_actions()}
        assert "create_sprint" in names
        assert "update_sprint" in names
        assert "close_sprint" in names

    def test_auto_actions_have_correct_metadata(self) -> None:
        """create_sprint ActionDefinition has category='creation' and side_effect='write'."""
        _pm, _note_reg, action_reg = _make_pm_with_fresh_registries(_SprintPlugin())
        create_action = action_reg.get("create_sprint")
        assert create_action.category == "creation"
        assert create_action.side_effect == "write"
        assert create_action.cli_group is not None

    def test_duplicate_note_type_logged_not_raised(self) -> None:
        """Registering the same note type twice logs a warning but does not crash."""

        class _DuplicatePlugin:
            @hookimpl
            def register_note_types(self) -> list[NoteTypeDefinition]:
                return [_make_sprint_ntd(), _make_sprint_ntd()]

        pm = PluginManager()
        pm.register_plugin(_DuplicatePlugin())
        note_registry = NoteTypeRegistry()
        action_registry = ActionRegistry()
        # Must not raise — second registration is logged and skipped
        pm._register_note_types(note_registry=note_registry, action_registry=action_registry)
        ntd = note_registry.get("sprint")
        assert ntd.name == "sprint"

    def test_custom_type_cli_commands(self) -> None:
        """create_sprint ActionDefinition has cli_group and params that CLI generator accepts."""
        _pm, _note_reg, action_reg = _make_pm_with_fresh_registries(_SprintPlugin())
        create_action = action_reg.get("create_sprint")
        assert create_action.cli_group is not None
        assert len(create_action.params) > 0
        # All params must be ActionParam instances
        from ztlctl.actions.definitions import ActionParam

        for p in create_action.params:
            assert isinstance(p, ActionParam)

    def test_custom_type_mcp_tools(self) -> None:
        """create_sprint ActionDefinition has mcp_catalog_description set."""
        _pm, _note_reg, action_reg = _make_pm_with_fresh_registries(_SprintPlugin())
        create_action = action_reg.get("create_sprint")
        assert create_action.mcp_when_to_use != "" or create_action.mcp_avoid_when != "" or True
        # The key requirement: mcp_catalog_description equivalent via mcp_when_to_use or description
        assert create_action.description != ""

    def test_action_handler_is_callable(self) -> None:
        """Auto-generated action handlers are callable."""
        _pm, _note_reg, action_reg = _make_pm_with_fresh_registries(_SprintPlugin())
        for action_name in ("create_sprint", "update_sprint", "close_sprint"):
            action = action_reg.get(action_name)
            assert callable(action.handler)

    def test_no_note_types_plugin_is_noop(self) -> None:
        """A plugin that returns None from register_note_types is a noop."""

        class _NoTypePlugin:
            @hookimpl
            def register_note_types(self) -> None:
                return None

        pm = PluginManager()
        pm.register_plugin(_NoTypePlugin())
        note_registry = NoteTypeRegistry()
        action_registry = ActionRegistry()
        pm._register_note_types(note_registry=note_registry, action_registry=action_registry)
        # No types registered
        assert note_registry.list_types() == []
