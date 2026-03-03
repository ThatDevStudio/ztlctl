"""Workspace ownership boundaries for core, profile-scaffold, and human-managed paths."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

WorkspaceOwnership = Literal["core", "profile", "human", "unclassified"]

CORE_MANAGED_ROOTS = (
    "ztlctl.toml",
    ".ztlctl",
    "self",
    "notes",
    "ops",
)
HUMAN_MANAGED_ROOT_HINTS = ("garden",)


def classify_workspace_path(
    path: str | Path,
    *,
    profile_managed_paths: tuple[str, ...] = (),
) -> WorkspaceOwnership:
    """Classify a vault-relative path by ownership boundary.

    ``profile_managed_paths`` names the roots scaffolded by the selected
    workspace profile during init. The classification is used for workspace
    boundary reporting; it does not imply later validation or overwrite
    authority.
    """
    candidate = Path(path)
    parts = candidate.parts
    if not parts:
        return "unclassified"

    head = parts[0]
    if head in CORE_MANAGED_ROOTS:
        return "core"
    if head in profile_managed_paths:
        return "profile"
    if head in HUMAN_MANAGED_ROOT_HINTS:
        return "human"
    return "unclassified"
