"""Canonical workspace profile and dashboard viewer helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, cast

from ztlctl.plugins.contracts import WorkspaceProfileContribution

WorkspaceProfileId = Literal["obsidian", "core"]
DashboardViewer = Literal["obsidian", "none"]

PROFILE_CHOICES = ("obsidian", "core")
DASHBOARD_VIEWER_CHOICES = ("obsidian", "none")
DEFAULT_PROFILE: WorkspaceProfileId = "obsidian"

_PROFILE_ALIASES = {
    "obsidian": "obsidian",
    "core": "core",
    "none": "core",
    "vanilla": "core",
}
_LEGACY_CLIENT_VALUES = ("obsidian", "none", "vanilla", "core")
_OBSIDIAN_CSS = """\
/* ztlctl vault styling for Obsidian */
.ztlctl-seed { color: var(--text-muted); }
.ztlctl-budding { color: var(--text-normal); }
.ztlctl-evergreen { color: var(--text-accent); font-weight: bold; }
"""


def normalize_profile(value: str) -> tuple[WorkspaceProfileId, str | None]:
    """Normalize a profile id to the canonical Phase 1 surface."""
    candidate = value.strip().lower()
    mapped = _PROFILE_ALIASES.get(candidate)
    if mapped is None:
        valid = ", ".join(f"`{item}`" for item in PROFILE_CHOICES)
        msg = f"Unsupported profile: {value!r}. Valid values: {valid}."
        raise ValueError(msg)
    if candidate == "none":
        return "core", "`none` is deprecated for profile selection; use `core` instead."
    if candidate == "vanilla":
        return (
            "core",
            "`vanilla` is deprecated for profile selection; use `core` instead.",
        )
    return cast(WorkspaceProfileId, mapped), None


def normalize_dashboard_viewer(value: str) -> tuple[DashboardViewer, str | None]:
    """Normalize a dashboard viewer value."""
    candidate = value.strip().lower()
    if candidate == "vanilla":
        return "none", "`vanilla` is deprecated for dashboard viewer selection; use `none` instead."
    if candidate in DASHBOARD_VIEWER_CHOICES:
        return cast(DashboardViewer, candidate), None
    valid = ", ".join(f"`{item}`" for item in DASHBOARD_VIEWER_CHOICES)
    msg = f"Unsupported dashboard viewer: {value!r}. Valid values: {valid}."
    raise ValueError(msg)


def legacy_client_to_profile(value: str) -> tuple[WorkspaceProfileId, str | None]:
    """Map the deprecated init client surface to a canonical profile."""
    candidate = value.strip().lower()
    if candidate not in _LEGACY_CLIENT_VALUES:
        valid = ", ".join(f"`{item}`" for item in ("obsidian", "none"))
        msg = f"Unsupported client: {value!r}. Valid values: {valid}."
        raise ValueError(msg)
    profile, warning = normalize_profile(candidate)
    if candidate == "obsidian":
        return profile, None
    return profile, warning


def profile_to_legacy_client(profile: WorkspaceProfileId) -> str:
    """Return the compatibility client value for a canonical profile."""
    return "obsidian" if profile == "obsidian" else "none"


def resolve_profile_selection(
    *,
    profile: str | None,
    client: str | None = None,
    default: WorkspaceProfileId = DEFAULT_PROFILE,
) -> tuple[WorkspaceProfileId, list[str], str]:
    """Resolve canonical profile plus compatibility client and warnings."""
    warnings: list[str] = []

    if profile is not None:
        resolved, profile_warning = normalize_profile(profile)
        if profile_warning is not None:
            warnings.append(profile_warning)
        if client is not None:
            warnings.append(
                "`client` is deprecated for workspace selection and ignored when "
                "`profile` is provided."
            )
        return resolved, warnings, profile_to_legacy_client(resolved)

    if client is not None:
        warnings.append("`client` is deprecated for workspace selection; use `profile` instead.")
        resolved, client_warning = legacy_client_to_profile(client)
        if client_warning is not None:
            warnings.append(client_warning)
        return resolved, warnings, profile_to_legacy_client(resolved)

    return default, warnings, profile_to_legacy_client(default)


def _obsidian_init_scaffold(vault_root: Path) -> list[str]:
    """Write the built-in Obsidian scaffold owned by the obsidian profile."""
    snippets_dir = vault_root / ".obsidian" / "snippets"
    snippets_dir.mkdir(parents=True, exist_ok=True)
    (snippets_dir / "ztlctl.css").write_text(_OBSIDIAN_CSS, encoding="utf-8")
    return [".obsidian/snippets/ztlctl.css"]


def builtin_workspace_profiles() -> dict[str, WorkspaceProfileContribution]:
    """Return the built-in workspace profiles available in Phase 1."""
    return {
        "core": WorkspaceProfileContribution(
            profile_id="core",
            description="Minimal built-in workspace with no viewer-specific scaffold.",
            aliases=("none", "vanilla"),
            managed_paths=(),
            init_scaffold=lambda _vault_root: [],
        ),
        "obsidian": WorkspaceProfileContribution(
            profile_id="obsidian",
            description="Built-in Obsidian-compatible workspace scaffold.",
            aliases=(),
            managed_paths=(".obsidian",),
            init_scaffold=_obsidian_init_scaffold,
        ),
    }


def get_builtin_workspace_profile(profile: WorkspaceProfileId) -> WorkspaceProfileContribution:
    """Fetch one built-in workspace profile by id."""
    return builtin_workspace_profiles()[profile]
