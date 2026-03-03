"""Tests for workspace ownership boundaries."""

from pathlib import Path

from ztlctl.workspace_ownership import (
    CORE_MANAGED_ROOTS,
    HUMAN_MANAGED_ROOT_HINTS,
    classify_workspace_path,
)


def test_core_managed_roots_are_explicit() -> None:
    assert CORE_MANAGED_ROOTS == ("ztlctl.toml", ".ztlctl", "self", "notes", "ops")


def test_human_managed_root_hints_include_garden() -> None:
    assert HUMAN_MANAGED_ROOT_HINTS == ("garden",)


def test_classify_core_managed_paths() -> None:
    assert classify_workspace_path(Path("notes/topic/ztl_abc12345.md")) == "core"
    assert classify_workspace_path(Path("ops/tasks/TASK-0001.md")) == "core"
    assert classify_workspace_path(Path(".ztlctl/workflow/profile.md")) == "core"


def test_classify_profile_managed_paths() -> None:
    assert (
        classify_workspace_path(
            Path(".obsidian/workspace.json"),
            profile_managed_paths=(".obsidian",),
        )
        == "profile"
    )


def test_classify_human_managed_paths() -> None:
    assert classify_workspace_path(Path("garden/notes/seed.md")) == "human"
    assert (
        classify_workspace_path(
            Path("garden/library/book.md"),
            profile_managed_paths=(".obsidian",),
        )
        == "human"
    )


def test_classify_unclassified_paths() -> None:
    assert classify_workspace_path(Path("scratch/tmp.md")) == "unclassified"
