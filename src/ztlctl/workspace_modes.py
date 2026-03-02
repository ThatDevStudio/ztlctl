"""Deprecated compatibility wrapper around Phase 1 workspace profile helpers."""

from __future__ import annotations

from typing import Literal, cast

from ztlctl.workspace_profiles import (
    legacy_client_to_profile,
    normalize_dashboard_viewer,
    profile_to_legacy_client,
)

CanonicalClient = Literal["obsidian", "none"]
CanonicalViewer = Literal["obsidian", "none"]

CLIENT_CHOICES = ("obsidian", "none")
VIEWER_CHOICES = ("obsidian", "none")


def normalize_client(value: str) -> tuple[CanonicalClient, str | None]:
    """Normalize a vault client value to the legacy compatibility surface."""
    profile, warning = legacy_client_to_profile(value)
    return cast(CanonicalClient, profile_to_legacy_client(profile)), warning


def normalize_viewer(value: str) -> tuple[CanonicalViewer, str | None]:
    """Normalize a dashboard viewer value."""
    return normalize_dashboard_viewer(value)
