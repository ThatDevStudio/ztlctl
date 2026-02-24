"""Config file discovery and loading.

Walk-up finder locates ztlctl.toml, similar to how git finds .git/.
Supports ZTLCTL_CONFIG env var and --config CLI flag overrides.
"""

from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

from ztlctl.config.models import ZtlConfig

CONFIG_FILENAME = "ztlctl.toml"
CONFIG_ENV_VAR = "ZTLCTL_CONFIG"


def find_config(start: Path | None = None) -> Path | None:
    """Walk up from *start* (default: cwd) looking for ztlctl.toml.

    Returns the path to the config file, or None if not found.
    Checks ZTLCTL_CONFIG env var first.
    """
    env_path = os.environ.get(CONFIG_ENV_VAR)
    if env_path:
        p = Path(env_path)
        if p.is_file():
            return p
        return None

    current = (start or Path.cwd()).resolve()
    while True:
        candidate = current / CONFIG_FILENAME
        if candidate.is_file():
            return candidate
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def load_config(path: Path | None = None, cwd: Path | None = None) -> ZtlConfig:
    """Load and validate config from a TOML file.

    If *path* is None, uses find_config(*cwd*) to discover the file.
    Returns default ZtlConfig if no file is found.
    """
    if path is None:
        path = find_config(cwd)

    if path is None:
        return ZtlConfig()

    raw = path.read_text(encoding="utf-8")
    data: dict[str, Any] = tomllib.loads(raw)
    return ZtlConfig.model_validate(data)
