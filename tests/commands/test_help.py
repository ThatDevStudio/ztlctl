"""Parametrized help tests for all CLI commands.

Consolidates ~52 individual help tests into a single parametrized test,
reducing duplication while preserving coverage of help output content.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from ztlctl.cli import cli

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
    (["export", "markdown", "--help"], ["--output"]),
    (["export", "indexes", "--help"], ["--output"]),
    (["export", "graph", "--help"], ["--format", "--output"]),
    # -- check --
    (["check", "--help"], ["--fix", "--rebuild", "--rollback", "--level"]),
    # -- reweave --
    (["reweave", "--help"], ["Reweave links", "--undo-id", "--auto-link-related"]),
    # -- update --
    (["update", "--help"], ["--title", "--status", "--tags", "--topic", "--body", "--maturity"]),
    # -- archive --
    (["archive", "--help"], ["CONTENT_ID"]),
    # -- supersede --
    (["supersede", "--help"], ["OLD_ID", "NEW_ID"]),
    # -- init --
    (["init", "--help"], ["--name", "--client", "--tone", "--topics", "--no-workflow"]),
    # -- garden --
    (["garden", "--help"], ["seed"]),
    (["garden", "seed", "--help"], ["--tags", "--topic"]),
    # -- vector group --
    (["vector", "--help"], ["status", "reindex"]),
    (["vector", "status", "--help"], []),
    (["vector", "reindex", "--help"], []),
    # -- serve --
    (["serve", "--help"], ["MCP server"]),
    # -- extract --
    (["extract", "--help"], ["SESSION_ID", "--title"]),
    # -- upgrade --
    (["upgrade", "--help"], ["--check"]),
    # -- agent group --
    (["agent", "--help"], ["session", "regenerate"]),
    (["agent", "regenerate", "--help"], ["Re-render"]),
    (["agent", "session", "--help"], ["start", "close", "reopen"]),
    # -- agent session subcommands --
    (["agent", "session", "cost", "--help"], []),
    (["agent", "session", "log", "--help"], []),
    (["agent", "context", "--help"], []),
    (["agent", "brief", "--help"], []),
    # -- agent help surfaces --
    (["agent", "--help"], ["context", "brief", "session"]),
    (["agent", "session", "--help"], ["start", "close", "reopen", "cost", "log"]),
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
