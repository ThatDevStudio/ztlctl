"""Extension layer — plugin system via pluggy.

Discovery: entry_points (pip-installed) via pluggy setuptools entrypoints.
INVARIANT: Plugin failures are warnings, never errors.
"""

from ztlctl.plugins.event_bus import EventBus
from ztlctl.plugins.manager import PluginManager

# ---------------------------------------------------------------------------
# Plugin API versioning (PLUG-01)
# ---------------------------------------------------------------------------

#: Current host-side plugin API version. Plugins declare their own
#: ``PLUGIN_API_VERSION`` attribute to signal compatibility.
PLUGIN_API_VERSION: int = 1

#: Number of API versions below the current version that are still
#: supported (with a deprecation warning). Older versions are rejected.
_COMPATIBILITY_WINDOW: int = 2


class PluginLoadError(Exception):
    """Raised when a plugin declares an incompatible API version."""


def check_plugin_api_version(plugin: object, plugin_name: str) -> list[str]:
    """Check a plugin's declared API version against the host.

    Returns:
        A list of warning strings (may be empty) if the plugin is compatible.

    Raises:
        PluginLoadError: If the plugin requires a newer API version than the
            host provides, or if its declared version is below the
            compatibility window.
    """
    declared = getattr(plugin, "PLUGIN_API_VERSION", None)

    # No version attribute — legacy plugin, load without warning.
    if declared is None:
        return []

    # Plugin requires a version the host doesn't yet support.
    if declared > PLUGIN_API_VERSION:
        raise PluginLoadError(
            f"Plugin '{plugin_name}' requires API version {declared} but "
            f"host provides {PLUGIN_API_VERSION}. Please upgrade ztlctl."
        )

    min_supported = PLUGIN_API_VERSION - _COMPATIBILITY_WINDOW

    # Plugin is too old — outside the compatibility window.
    if declared <= min_supported:
        raise PluginLoadError(
            f"Plugin '{plugin_name}' declares API version {declared} which is "
            f"no longer supported (min: {min_supported + 1}). "
            f"Please update the plugin."
        )

    # Plugin is within the window but not the current version — warn.
    if declared < PLUGIN_API_VERSION:
        return [
            f"Plugin '{plugin_name}' declares API version {declared}; "
            f"consider updating to {PLUGIN_API_VERSION} for full support."
        ]

    # Exact match — fully compatible.
    return []


__all__ = [
    "PLUGIN_API_VERSION",
    "_COMPATIBILITY_WINDOW",
    "EventBus",
    "PluginLoadError",
    "PluginManager",
    "check_plugin_api_version",
]
