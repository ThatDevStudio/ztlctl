"""ActionRegistry and module-level singleton accessor.

ActionRegistry stores ActionDefinitions and enforces name-uniqueness on
registration.  The module-level singleton ``_REGISTRY`` is the shared
registry for all built-in and plugin-contributed actions.

Use ``get_action_registry()`` to access the singleton.
Plugin authors register actions via ``get_action_registry().register()``.
"""

from __future__ import annotations

from typing import Literal

from ztlctl.actions.definitions import ActionDefinition

# ---------------------------------------------------------------------------
# ActionRegistry
# ---------------------------------------------------------------------------


class ActionRegistry:
    """Registry of all ActionDefinitions (built-in + plugin-contributed).

    Thread safety: registrations are expected to happen at module-load time
    only — no locking is performed.
    """

    def __init__(self) -> None:
        self._actions: dict[str, ActionDefinition] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(self, action: ActionDefinition) -> None:
        """Register *action*.

        Raises
        ------
        ValueError
            If an action with the same name is already registered.
        """
        if action.name in self._actions:
            msg = f"Action {action.name!r} is already registered"
            raise ValueError(msg)
        self._actions[action.name] = action

    def get(self, name: str) -> ActionDefinition:
        """Return the ActionDefinition for *name*.

        Raises
        ------
        KeyError
            If no action is registered under *name*.
        """
        try:
            return self._actions[name]
        except KeyError:
            msg = f"No action registered for name={name!r}"
            raise KeyError(msg) from None

    def list_actions(
        self,
        *,
        category: str | None = None,
        side_effect: Literal["read", "write"] | None = None,
        custom_presentation: bool | None = None,
    ) -> list[ActionDefinition]:
        """Return a filtered list of registered actions.

        All provided filters are combined with AND logic.  Omit a
        parameter to skip that filter.
        """
        actions = list(self._actions.values())
        if category is not None:
            actions = [a for a in actions if a.category == category]
        if side_effect is not None:
            actions = [a for a in actions if a.side_effect == side_effect]
        if custom_presentation is not None:
            actions = [a for a in actions if a.custom_presentation == custom_presentation]
        return actions


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_REGISTRY = ActionRegistry()


def get_action_registry() -> ActionRegistry:
    """Return the module-level ActionRegistry singleton."""
    return _REGISTRY
