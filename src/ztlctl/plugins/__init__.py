"""Extension layer — plugin system via pluggy.

Discovery: entry_points (pip-installed) via pluggy setuptools entrypoints.
INVARIANT: Plugin failures are warnings, never errors.
"""

from ztlctl.plugins._version import (
    _COMPATIBILITY_WINDOW,
    PLUGIN_API_VERSION,
    PluginLoadError,
    check_plugin_api_version,
)
from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.manager import PluginManager

__all__ = [
    "PLUGIN_API_VERSION",
    "_COMPATIBILITY_WINDOW",
    "EventBus",
    "PluginLoadError",
    "PluginManager",
    "check_plugin_api_version",
]
