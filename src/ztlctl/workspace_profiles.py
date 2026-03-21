"""Workspace profile discovery, resolution, and compatibility helpers."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from ztlctl.plugins.contracts import WorkspaceProfileContribution

type WorkspaceProfileId = str
DashboardViewer = Literal["obsidian", "none"]

CORE_PROFILE_ID = "core"
OBSIDIAN_PROFILE_ID = "obsidian"
DEFAULT_PROFILE: WorkspaceProfileId = CORE_PROFILE_ID
DEFAULT_LEGACY_CLIENT_FOR_NON_OBSIDIAN = "none"
DASHBOARD_VIEWER_CHOICES = ("obsidian", "none")

_PROFILE_ALIAS_MAP = {
    "none": CORE_PROFILE_ID,
    "vanilla": CORE_PROFILE_ID,
}
_LEGACY_CLIENT_VALUES = {
    OBSIDIAN_PROFILE_ID,
    DEFAULT_LEGACY_CLIENT_FOR_NON_OBSIDIAN,
    "vanilla",
    CORE_PROFILE_ID,
}


@dataclass
class WorkspaceProfileRegistry:
    """Resolved runtime registry for installed workspace profiles."""

    profiles: dict[str, WorkspaceProfileContribution]
    aliases: dict[str, str]
    warnings: list[str] = field(default_factory=list)

    def ordered_ids(self) -> list[str]:
        """Return canonical profile ids in stable UX order."""
        preferred = [CORE_PROFILE_ID, OBSIDIAN_PROFILE_ID]
        ordered: list[str] = [item for item in preferred if item in self.profiles]
        ordered.extend(sorted(item for item in self.profiles if item not in ordered))
        return ordered


class UnknownWorkspaceProfileError(ValueError):
    """Raised when a requested profile is not installed in the active registry."""

    def __init__(self, requested_profile: str, available_profiles: list[str]) -> None:
        self.requested_profile = requested_profile
        self.available_profiles = available_profiles
        available = ", ".join(f"`{item}`" for item in available_profiles)
        super().__init__(
            f"Workspace profile {requested_profile!r} is not installed. "
            f"Installed profiles: {available}."
        )


def _normalize_token(value: str) -> str:
    """Normalize a profile-like token for comparisons and persistence."""
    return value.strip().lower()


def core_workspace_profile() -> WorkspaceProfileContribution:
    """Return the always-available core fallback workspace profile."""
    return WorkspaceProfileContribution(
        profile_id=CORE_PROFILE_ID,
        description="Minimal core-managed workspace with no profile scaffold.",
        aliases=("none", "vanilla"),
        managed_paths=(),
        init_scaffold=lambda _vault_root: [],
    )


def normalize_profile(value: str) -> tuple[WorkspaceProfileId, str | None]:
    """Normalize compatibility aliases while preserving arbitrary profile ids."""
    candidate = _normalize_token(value)
    if not candidate:
        msg = "Workspace profile cannot be empty."
        raise ValueError(msg)
    mapped = _PROFILE_ALIAS_MAP.get(candidate)
    if mapped == CORE_PROFILE_ID and candidate == "none":
        return CORE_PROFILE_ID, "`none` is deprecated for profile selection; use `core` instead."
    if mapped == CORE_PROFILE_ID and candidate == "vanilla":
        return (
            CORE_PROFILE_ID,
            "`vanilla` is deprecated for profile selection; use `core` instead.",
        )
    return candidate, None


def normalize_dashboard_viewer(value: str) -> tuple[DashboardViewer, str | None]:
    """Normalize a dashboard viewer value."""
    candidate = _normalize_token(value)
    if candidate == "vanilla":
        return (
            "none",
            "`vanilla` is deprecated for dashboard viewer selection; use `none` instead.",
        )
    if candidate == "obsidian":
        return "obsidian", None
    if candidate == "none":
        return "none", None
    valid = ", ".join(f"`{item}`" for item in DASHBOARD_VIEWER_CHOICES)
    msg = f"Unsupported dashboard viewer: {value!r}. Valid values: {valid}."
    raise ValueError(msg)


def legacy_client_to_profile(value: str) -> tuple[WorkspaceProfileId, str | None]:
    """Map the deprecated client surface to a canonical profile id."""
    candidate = _normalize_token(value)
    if candidate not in _LEGACY_CLIENT_VALUES:
        valid = ", ".join(f"`{item}`" for item in ("obsidian", "none"))
        msg = f"Unsupported client: {value!r}. Valid values: {valid}."
        raise ValueError(msg)
    if candidate == OBSIDIAN_PROFILE_ID:
        return OBSIDIAN_PROFILE_ID, None
    if candidate == CORE_PROFILE_ID:
        return CORE_PROFILE_ID, "`core` is deprecated for client selection; use `none` instead."
    if candidate == "vanilla":
        return (
            CORE_PROFILE_ID,
            "`vanilla` is deprecated for client selection; use `none` instead.",
        )
    return CORE_PROFILE_ID, None


def profile_to_legacy_client(profile: WorkspaceProfileId) -> str:
    """Return the compatibility client value for a canonical profile."""
    return OBSIDIAN_PROFILE_ID if profile == OBSIDIAN_PROFILE_ID else "none"


def _normalize_contribution(
    contribution: WorkspaceProfileContribution,
) -> WorkspaceProfileContribution | None:
    """Normalize a profile contribution for registry insertion."""
    profile_id = _normalize_token(contribution.profile_id)
    if not profile_id:
        return None
    normalized_aliases: list[str] = []
    for item in contribution.aliases:
        alias = _normalize_token(item)
        if alias:
            normalized_aliases.append(alias)
    return replace(contribution, profile_id=profile_id, aliases=tuple(normalized_aliases))


def discover_workspace_profiles(
    *,
    local_dir: Path | None,
    include_entrypoints: bool = True,
) -> WorkspaceProfileRegistry:
    """Discover installed workspace profiles from plugins plus the core fallback."""
    registry = WorkspaceProfileRegistry(
        profiles={CORE_PROFILE_ID: core_workspace_profile()},
        aliases={"none": CORE_PROFILE_ID, "vanilla": CORE_PROFILE_ID},
    )

    from ztlctl.plugins.runtime import get_plugin_manager

    plugin_manager = get_plugin_manager(
        local_dir=local_dir,
        include_entrypoints=include_entrypoints,
    )
    contributions = plugin_manager.workspace_profile_contributions(reserved_names={CORE_PROFILE_ID})

    for contribution in contributions:
        normalized = _normalize_contribution(contribution)
        if normalized is None:
            registry.warnings.append("Skipping plugin workspace profile with an empty id.")
            continue

        profile_id = normalized.profile_id
        if profile_id in registry.profiles:
            registry.warnings.append(
                f"Skipping duplicate workspace profile `{profile_id}` from plugin discovery."
            )
            continue

        registry.profiles[profile_id] = normalized
        for alias in normalized.aliases:
            if alias == profile_id:
                continue
            if alias in registry.profiles:
                registry.warnings.append(
                    f"Skipping alias `{alias}` for workspace profile `{profile_id}` because it "
                    "conflicts with an installed profile id."
                )
                continue
            existing = registry.aliases.get(alias)
            if existing is not None and existing != profile_id:
                registry.warnings.append(
                    f"Skipping alias `{alias}` for workspace profile `{profile_id}` because it "
                    f"already resolves to `{existing}`."
                )
                continue
            registry.aliases[alias] = profile_id

    return registry


def discover_init_profiles() -> WorkspaceProfileRegistry:
    """Discover profiles available during init (entry-point plugins only)."""
    return discover_workspace_profiles(local_dir=None, include_entrypoints=True)


def discover_vault_profiles(vault_root: Path) -> WorkspaceProfileRegistry:
    """Discover profiles for an existing vault (entry points plus local plugins)."""
    return discover_workspace_profiles(
        local_dir=vault_root / ".ztlctl" / "plugins",
        include_entrypoints=True,
    )


def resolve_workspace_profile(
    value: str,
    registry: WorkspaceProfileRegistry,
) -> tuple[WorkspaceProfileId, str | None]:
    """Resolve a user-provided profile value against the discovered registry."""
    candidate, warning = normalize_profile(value)
    resolved = registry.aliases.get(candidate, candidate)
    if resolved in registry.profiles:
        return resolved, warning
    raise UnknownWorkspaceProfileError(value, registry.ordered_ids())


def resolve_profile_selection(
    *,
    profile: str | None,
    client: str | None = None,
    registry: WorkspaceProfileRegistry,
    default: WorkspaceProfileId = DEFAULT_PROFILE,
) -> tuple[WorkspaceProfileId, list[str], str]:
    """Resolve canonical profile plus compatibility client and warnings."""
    warnings = list(registry.warnings)

    if profile is not None:
        resolved, profile_warning = resolve_workspace_profile(profile, registry)
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
        raw_profile, client_warning = legacy_client_to_profile(client)
        if client_warning is not None:
            warnings.append(client_warning)
        resolved, profile_warning = resolve_workspace_profile(raw_profile, registry)
        if profile_warning is not None:
            warnings.append(profile_warning)
        return resolved, warnings, profile_to_legacy_client(resolved)

    if default not in registry.profiles:
        available = ", ".join(f"`{item}`" for item in registry.ordered_ids())
        msg = (
            f"Default workspace profile {default!r} is not installed. "
            f"Installed profiles: {available}."
        )
        raise ValueError(msg)
    return default, warnings, profile_to_legacy_client(default)
