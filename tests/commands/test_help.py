"""Parametrized help tests for all CLI commands.

Consolidates ~52 individual help tests into a single parametrized test,
reducing duplication while preserving coverage of help output content.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli
from ztlctl.plugins.contracts import WorkspaceProfileContribution
from ztlctl.workspace_profiles import WorkspaceProfileRegistry, core_workspace_profile

# (CLI args, expected keywords in output)
HELP_COMMANDS: list[tuple[list[str], list[str]]] = [
    # -- create group --
    (["create", "--help"], ["note", "reference", "task"]),
    (["create", "note", "--help"], ["--subtype", "--tags"]),
    (["create", "reference", "--help"], ["--url", "--subtype"]),
    (["create", "task", "--help"], ["--priority", "--impact", "--effort"]),
    (["create", "batch", "--help"], ["FILE", "--partial"]),
    # -- query group --
    (["query", "--help"], ["search", "get", "list", "work-queue", "decision-support"]),
    (["query", "search", "--help"], ["--type", "--tag", "--rank-by", "--space"]),
    (["query", "get", "--help"], ["CONTENT_ID"]),
    (["query", "list", "--help"], ["--type", "--status", "--sort", "--space"]),
    (["query", "list", "--help"], ["--subtype", "--maturity", "--since", "--include-archived"]),
    (["query", "work-queue", "--help"], ["--space"]),
    (["query", "decision-support", "--help"], ["--topic", "--space"]),
    # -- graph group --
    (["graph", "--help"], ["related", "themes", "rank", "path", "gaps", "bridges"]),
    (["graph", "related", "--help"], ["CONTENT_ID", "--depth", "--top"]),
    (["graph", "themes", "--help"], []),
    (["graph", "rank", "--help"], ["--top"]),
    (["graph", "path", "--help"], ["SOURCE_ID", "TARGET_ID"]),
    (["graph", "gaps", "--help"], ["--top"]),
    (["graph", "bridges", "--help"], ["--top"]),
    # -- export group --
    (["export", "--help"], ["markdown", "indexes", "graph"]),
    (["export", "markdown", "--help"], ["OUTPUT_DIR"]),
    (["export", "indexes", "--help"], ["OUTPUT_DIR"]),
    (["export", "graph", "--help"], ["--format"]),
    # -- workflow group --
    (["workflow", "--help"], ["init", "update", "export", "validate"]),
    (
        ["workflow", "init", "--help"],
        ["--source-control", "--profile", "--viewer", "--workflow", "--skill-set"],
    ),
    (
        ["workflow", "update", "--help"],
        ["--source-control", "--profile", "--viewer", "--workflow", "--skill-set"],
    ),
    (["workflow", "export", "--help"], ["--client"]),
    (["workflow", "validate", "--help"], ["--client"]),
    # -- check group --
    (["check", "--help"], ["check", "fix", "rebuild", "rollback"]),
    (["check", "check", "--help"], ["--min-severity"]),
    (["check", "fix", "--help"], ["--level"]),
    (["check", "rebuild", "--help"], []),
    (["check", "rollback", "--help"], []),
    # -- reweave group --
    (["reweave", "--help"], ["run", "prune", "undo"]),
    (["reweave", "run", "--help"], ["--dry-run", "--content-id"]),
    (["reweave", "prune", "--help"], ["--dry-run"]),
    (["reweave", "undo", "--help"], ["--reweave-id"]),
    # -- update --
    (["update", "--help"], ["--title", "--status", "--tags", "--topic", "--body", "--maturity"]),
    # -- archive --
    (["archive", "--help"], ["CONTENT_ID"]),
    # -- supersede --
    (["supersede", "--help"], ["OLD_ID", "NEW_ID"]),
    # -- init group --
    (
        ["init", "--help"],
        ["--name", "--profile", "--client", "--tone", "--topics", "--no-workflow"],
    ),
    (["init", "regenerate", "--help"], ["Re-render"]),
    # -- garden --
    (["garden", "--help"], ["seed"]),
    (["garden", "seed", "--help"], ["--tags", "--topic"]),
    # -- vector group --
    (["vector", "--help"], ["reindex"]),
    (["vector", "reindex", "--help"], []),
    # -- serve --
    (["serve", "--help"], ["MCP server"]),
    # -- session group --
    (["session", "--help"], ["start", "close", "reopen", "context", "brief"]),
    (["session", "start", "--help"], ["TOPIC"]),
    (["session", "close", "--help"], ["--summary"]),
    (["session", "reopen", "--help"], ["SESSION_ID"]),
    (["session", "cost", "--help"], []),
    (["session", "log", "--help"], []),
    (["session", "context", "--help"], []),
    (["session", "brief", "--help"], []),
    (["session", "extract", "--help"], ["SESSION_ID"]),
    # -- upgrade group --
    (["upgrade", "--help"], ["apply", "check", "stamp"]),
    (["upgrade", "apply", "--help"], []),
    (["upgrade", "check", "--help"], []),
]


def _help_id(args_keywords: tuple[list[str], list[str]]) -> str:
    """Generate a readable test ID from args."""
    args, _ = args_keywords
    # Remove --help, join remaining with underscore
    return "_".join(a for a in args if a != "--help")


@pytest.mark.parametrize(
    "args,expected_keywords",
    HELP_COMMANDS,
    ids=[_help_id(item) for item in HELP_COMMANDS],
)
def test_command_help(cli_runner: CliRunner, args: list[str], expected_keywords: list[str]) -> None:
    result = cli_runner.invoke(cli, args)
    assert result.exit_code == 0
    for kw in expected_keywords:
        assert kw in result.output, f"Expected '{kw}' in help output for {args}"


def test_init_help_lists_installed_profiles(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = WorkspaceProfileRegistry(
        profiles={
            "core": core_workspace_profile(),
            "obsidian": WorkspaceProfileContribution(
                profile_id="obsidian",
                description="Obsidian",
            ),
            "custom-profile": WorkspaceProfileContribution(
                profile_id="custom-profile",
                description="Custom",
            ),
        },
        aliases={"none": "core", "vanilla": "core"},
    )
    monkeypatch.setattr("ztlctl.workspace_profiles.discover_init_profiles", lambda: registry)

    result = cli_runner.invoke(cli, ["init", "--help"])

    assert result.exit_code == 0
    assert "Installed now: core, obsidian, custom-profile." in result.output


def test_workflow_help_lists_installed_profiles(
    cli_runner: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry = WorkspaceProfileRegistry(
        profiles={
            "core": core_workspace_profile(),
            "local-profile": WorkspaceProfileContribution(
                profile_id="local-profile",
                description="Local",
            ),
        },
        aliases={"none": "core", "vanilla": "core"},
    )
    monkeypatch.setattr("ztlctl.workspace_profiles.discover_vault_profiles", lambda _root: registry)

    result = cli_runner.invoke(cli, ["workflow", "init", "--help"])

    assert result.exit_code == 0
    assert "Installed" in result.output
    assert "now: core, local-profile." in result.output
