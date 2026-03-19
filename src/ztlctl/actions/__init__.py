"""ztlctl actions package — ActionParam, ActionDefinition, ActionRegistry."""

from ztlctl.actions._register_core import _register_core_actions
from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.actions.registry import ActionRegistry, get_action_registry

_register_core_actions()

__all__ = ["ActionDefinition", "ActionParam", "ActionRegistry", "get_action_registry"]
