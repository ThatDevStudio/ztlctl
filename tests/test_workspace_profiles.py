"""Tests for workspace profile discovery and resolution."""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.workspace_profiles import (
    CORE_PROFILE_ID,
    UnknownWorkspaceProfileError,
    discover_workspace_profiles,
    profile_to_legacy_client,
    resolve_workspace_profile,
)

_LOCAL_PROFILE_PLUGIN = """\
import pluggy

from ztlctl.plugins.contracts import WorkspaceProfileContribution

hookimpl = pluggy.HookimplMarker("ztlctl")


class LocalProfilePlugin:
    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [
            WorkspaceProfileContribution(
                profile_id="local-profile",
                description="Local profile.",
                aliases=("local-alias",),
            )
        ]
"""

_CONFLICTING_ALIAS_PLUGIN = """\
import pluggy

from ztlctl.plugins.contracts import WorkspaceProfileContribution

hookimpl = pluggy.HookimplMarker("ztlctl")


class ConflictingAliasPlugin:
    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [
            WorkspaceProfileContribution(
                profile_id="other-profile",
                description="Other profile.",
                aliases=("local-alias",),
            )
        ]
"""


def test_discover_workspace_profiles_collects_local_plugins(tmp_path: Path) -> None:
    (tmp_path / "local_profile.py").write_text(_LOCAL_PROFILE_PLUGIN, encoding="utf-8")

    registry = discover_workspace_profiles(local_dir=tmp_path, include_entrypoints=False)

    assert registry.ordered_ids() == [CORE_PROFILE_ID, "local-profile"]
    assert registry.aliases["local-alias"] == "local-profile"


def test_discover_workspace_profiles_warns_on_alias_conflict(tmp_path: Path) -> None:
    (tmp_path / "local_profile.py").write_text(_LOCAL_PROFILE_PLUGIN, encoding="utf-8")
    (tmp_path / "conflict.py").write_text(_CONFLICTING_ALIAS_PLUGIN, encoding="utf-8")

    registry = discover_workspace_profiles(local_dir=tmp_path, include_entrypoints=False)

    assert registry.aliases["local-alias"] == "local-profile"
    assert any("already resolves to `local-profile`" in warning for warning in registry.warnings)


def test_resolve_workspace_profile_accepts_core_aliases(tmp_path: Path) -> None:
    registry = discover_workspace_profiles(local_dir=tmp_path, include_entrypoints=False)

    profile, warning = resolve_workspace_profile("none", registry)

    assert profile == "core"
    assert warning is not None


def test_resolve_workspace_profile_raises_for_unknown_profile(tmp_path: Path) -> None:
    registry = discover_workspace_profiles(local_dir=tmp_path, include_entrypoints=False)

    with pytest.raises(UnknownWorkspaceProfileError) as exc_info:
        resolve_workspace_profile("missing-profile", registry)

    assert exc_info.value.requested_profile == "missing-profile"
    assert exc_info.value.available_profiles == ["core"]


def test_non_obsidian_profiles_map_to_legacy_client_none() -> None:
    assert profile_to_legacy_client("obsidian") == "obsidian"
    assert profile_to_legacy_client("custom-profile") == "none"
