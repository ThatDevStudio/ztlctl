"""Extension layer — plugin system via pluggy.

Discovery: entry_points (pip-installed) via pluggy setuptools entrypoints.
INVARIANT: Plugin failures are warnings, never errors.
"""

from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.manager import PluginManager

__all__ = ["EventBus", "PluginManager"]
