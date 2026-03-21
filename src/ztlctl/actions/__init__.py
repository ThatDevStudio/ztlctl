"""ztlctl actions package — ActionParam, ActionDefinition, ActionRegistry."""

from ztlctl.actions._admin import _register_admin_actions
from ztlctl.actions._check import _register_check_actions
from ztlctl.actions._creation import _register_creation_actions
from ztlctl.actions._export import _register_export_actions
from ztlctl.actions._graph import _register_graph_actions
from ztlctl.actions._ingest import _register_ingest_actions
from ztlctl.actions._lifecycle import _register_lifecycle_actions
from ztlctl.actions._query import _register_query_actions
from ztlctl.actions._session import _register_session_actions
from ztlctl.actions.definitions import ActionDefinition, ActionParam
from ztlctl.actions.registry import ActionRegistry, get_action_registry

_register_creation_actions()
_register_query_actions()
_register_graph_actions()
_register_lifecycle_actions()
_register_session_actions()
_register_check_actions()
_register_ingest_actions()
_register_export_actions()
_register_admin_actions()

__all__ = ["ActionDefinition", "ActionParam", "ActionRegistry", "get_action_registry"]
