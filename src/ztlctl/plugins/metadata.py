"""Plugin marketplace metadata helpers.

Reads ``[tool.ztlctl-plugin]`` sections from pyproject.toml files for future
plugin discoverability. Plugin authors include this section in their
``pyproject.toml`` to declare compatibility and capabilities.

Example ``pyproject.toml`` section::

    [tool.ztlctl-plugin]
    name = "my-sprint-plugin"
    version = "1.0.0"
    author = "Acme Corp"
    capabilities = ["register_note_types"]
    ztlctl_api_version = 1
    description = "Adds sprint note type to ztlctl"
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from ztlctl.plugins.contracts import PluginMetadata

logger = logging.getLogger(__name__)


def read_plugin_metadata(pyproject_path: Path) -> PluginMetadata | None:
    """Read ``[tool.ztlctl-plugin]`` from a pyproject.toml file.

    Args:
        pyproject_path: Absolute or relative path to a ``pyproject.toml`` file.

    Returns:
        A :class:`~ztlctl.plugins.contracts.PluginMetadata` instance if the
        section is present and valid, otherwise ``None``.

    Logging:
        A warning is logged if the file cannot be read, contains invalid TOML,
        or is missing required fields. The function never raises.
    """
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        logger.warning("Failed to read %s", pyproject_path, exc_info=True)
        return None

    section: dict[str, Any] | None = data.get("tool", {}).get("ztlctl-plugin")
    if section is None:
        return None

    try:
        return PluginMetadata(
            name=section["name"],
            version=section["version"],
            author=section["author"],
            capabilities=tuple(section.get("capabilities", ())),
            ztlctl_api_version=section["ztlctl_api_version"],
            description=section.get("description", ""),
        )
    except (KeyError, TypeError) as exc:
        logger.warning(
            "Invalid [tool.ztlctl-plugin] in %s: %s",
            pyproject_path,
            exc,
        )
        return None
