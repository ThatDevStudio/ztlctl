"""Tests for GitPlugin — subprocess-based git operations on lifecycle hooks."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from ztlctl.config.models import GitConfig
from ztlctl.plugins.builtins.git import GitPlugin

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def git_vault(tmp_path: Path) -> Path:
    """Temporary vault with an initialized git repo."""
    subprocess.run(
        ["git", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    # Create initial commit so HEAD exists
    marker = tmp_path / ".keep"
    marker.write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        capture_output=True,
        check=True,
    )
    return tmp_path


@pytest.fixture
def plugin(git_vault: Path) -> GitPlugin:
    """GitPlugin with batch_commits=True (default) and a real git repo."""
    return GitPlugin(config=GitConfig(batch_commits=True, auto_push=False), vault_root=git_vault)


@pytest.fixture
def immediate_plugin(git_vault: Path) -> GitPlugin:
    """GitPlugin with batch_commits=False (immediate commit mode)."""
    return GitPlugin(
        config=GitConfig(batch_commits=False, auto_push=False),
        vault_root=git_vault,
    )


def _make_ok_result(**data: object) -> object:
    """Return a mock ServiceResult-like object with ok=True."""

    class _Result:
        ok = True

        def __init__(self, d: dict) -> None:
            self.data = d

    return _Result(dict(data))


def _make_failed_result() -> object:
    """Return a mock ServiceResult-like object with ok=False."""

    class _Result:
        ok = False
        data: dict[str, object]  # type: ignore[assignment]

        def __init__(self) -> None:
            self.data = {}

    return _Result()


def _git_log(cwd: Path) -> list[str]:
    """Get commit messages from git log."""
    result = subprocess.run(
        ["git", "log", "--oneline", "--format=%s"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()


def _staged_files(cwd: Path) -> list[str]:
    """Get list of staged file paths."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()


# ---------------------------------------------------------------------------
# Tests — PLUGIN_API_VERSION
# ---------------------------------------------------------------------------


def test_plugin_api_version():
    """GitPlugin must declare PLUGIN_API_VERSION = 1."""
    assert GitPlugin.PLUGIN_API_VERSION == 1


# ---------------------------------------------------------------------------
# Tests — post_action: create actions
# ---------------------------------------------------------------------------


class TestGitPluginPostActionCreate:
    """Tests for post_action with create action names."""

    def test_post_action_create_note_stages_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        result = _make_ok_result(path="notes/N-0001.md")
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": ["test"],
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged

    def test_post_action_create_note_commits_immediately_when_not_batched(
        self, immediate_plugin: GitPlugin, git_vault: Path
    ):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        result = _make_ok_result(path="notes/N-0001.md")
        immediate_plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": ["test"],
            },
            result=result,
        )

        log = _git_log(git_vault)
        assert any("N-0001" in msg for msg in log)

    def test_post_action_create_reference_stages_file(self, plugin: GitPlugin, git_vault: Path):
        ref = git_vault / "notes" / "R-0001.md"
        ref.parent.mkdir(parents=True, exist_ok=True)
        ref.write_text("# Ref", encoding="utf-8")

        result = _make_ok_result(path="notes/R-0001.md")
        plugin.post_action(
            action_name="create_reference",
            kwargs={
                "content_type": "reference",
                "content_id": "R-0001",
                "title": "Ref",
                "path": "notes/R-0001.md",
                "tags": [],
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert "notes/R-0001.md" in staged

    def test_post_action_create_task_stages_file(self, plugin: GitPlugin, git_vault: Path):
        task = git_vault / "ops" / "tasks" / "TASK-0001.md"
        task.parent.mkdir(parents=True, exist_ok=True)
        task.write_text("# Task", encoding="utf-8")

        result = _make_ok_result(path="ops/tasks/TASK-0001.md")
        plugin.post_action(
            action_name="create_task",
            kwargs={
                "content_type": "task",
                "content_id": "TASK-0001",
                "title": "Task",
                "path": "ops/tasks/TASK-0001.md",
                "tags": [],
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert "ops/tasks/TASK-0001.md" in staged

    def test_post_action_skips_when_disabled(self, git_vault: Path):
        plugin = GitPlugin(config=GitConfig(enabled=False), vault_root=git_vault)
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        result = _make_ok_result(path="notes/N-0001.md")
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert staged == []

    def test_post_action_skips_failed_result(self, plugin: GitPlugin, git_vault: Path):
        """post_action should not stage/commit when result.ok is False."""
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        result = _make_failed_result()
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert staged == []

    def test_post_action_none_result_proceeds(self, plugin: GitPlugin, git_vault: Path):
        """result=None (EventBus bridge path) should proceed with git operations."""
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            result=None,
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged


# ---------------------------------------------------------------------------
# Tests — post_action: update action
# ---------------------------------------------------------------------------


class TestGitPluginPostActionUpdate:
    """Tests for post_action with update action name."""

    def test_post_action_update_stages_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Updated", encoding="utf-8")

        result = _make_ok_result(path="notes/N-0001.md")
        plugin.post_action(
            action_name="update",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "fields_changed": ["title"],
                "path": "notes/N-0001.md",
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged


# ---------------------------------------------------------------------------
# Tests — post_action: close/archive actions
# ---------------------------------------------------------------------------


class TestGitPluginPostActionClose:
    """Tests for post_action with close/archive action names."""

    def test_post_action_close_stages_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Closed", encoding="utf-8")

        result = _make_ok_result(path="notes/N-0001.md")
        plugin.post_action(
            action_name="close",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "path": "notes/N-0001.md",
                "summary": "archived",
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged

    def test_post_action_archive_stages_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Archived", encoding="utf-8")

        result = _make_ok_result(path="notes/N-0001.md")
        plugin.post_action(
            action_name="archive",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "path": "notes/N-0001.md",
                "summary": "done",
            },
            result=result,
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged


# ---------------------------------------------------------------------------
# Tests — session close
# ---------------------------------------------------------------------------


class TestGitPluginSessionClose:
    """Tests for post_action with session_close action name."""

    def test_post_action_session_close_batch_commit(self, plugin: GitPlugin, git_vault: Path):
        # Stage some files first
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Note", encoding="utf-8")
        result = _make_ok_result(path="notes/N-0001.md")
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Note",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            result=result,
        )

        plugin.post_action(
            action_name="session_close",
            kwargs={"session_id": "LOG-0001", "stats": {"created": 0, "updated": 0}},
            result=None,
        )

        log = _git_log(git_vault)
        assert any("LOG-0001" in msg for msg in log)
        assert any("1 created, 0 updated" in msg for msg in log)

    def test_post_action_session_close_skips_commit_when_nothing_staged(
        self, plugin: GitPlugin, git_vault: Path
    ):
        before = _git_log(git_vault)

        plugin.post_action(
            action_name="session_close",
            kwargs={"session_id": "LOG-0001", "stats": {"created": 99, "updated": 99}},
            result=None,
        )

        after = _git_log(git_vault)
        assert after == before

    def test_post_action_session_close_reports_renamed_files(
        self, plugin: GitPlugin, git_vault: Path
    ):
        tracked = git_vault / "notes" / "N-0001.md"
        tracked.parent.mkdir(parents=True, exist_ok=True)
        tracked.write_text("# Renamed", encoding="utf-8")
        subprocess.run(
            ["git", "add", "notes/N-0001.md"],
            cwd=git_vault,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "track note"],
            cwd=git_vault,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "mv", "notes/N-0001.md", "notes/N-0002.md"],
            cwd=git_vault,
            capture_output=True,
            check=True,
        )

        plugin.post_action(
            action_name="session_close",
            kwargs={"session_id": "LOG-0002", "stats": {"created": 0, "updated": 0}},
            result=None,
        )

        log = _git_log(git_vault)
        assert any("LOG-0002" in msg and "1 renamed" in msg for msg in log)

    def test_post_action_auto_push_calls_git_push(self, git_vault: Path):
        push_plugin = GitPlugin(
            config=GitConfig(auto_push=True, batch_commits=True),
            vault_root=git_vault,
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            push_plugin.post_action(
                action_name="session_close",
                kwargs={"session_id": "LOG-0001", "stats": {"created": 0, "updated": 0}},
                result=None,
            )

        # Verify git push was called
        push_calls = [c for c in mock_run.call_args_list if "push" in c.args[0]]
        assert len(push_calls) >= 1


# ---------------------------------------------------------------------------
# Tests — post_action: init action
# ---------------------------------------------------------------------------


class TestGitPluginPostActionInit:
    """Tests for post_action with init action name."""

    def test_post_action_init_creates_gitignore(self, tmp_path: Path):
        plugin = GitPlugin(
            config=GitConfig(auto_ignore=True),
            vault_root=tmp_path,
        )
        plugin.post_action(
            action_name="init",
            kwargs={"vault_name": "test-vault", "client": "obsidian", "tone": "research-partner"},
            result=None,
        )

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text(encoding="utf-8")
        assert "backups" in content

    def test_post_action_init_runs_git_init(self, tmp_path: Path):
        plugin = GitPlugin(
            config=GitConfig(auto_ignore=True),
            vault_root=tmp_path,
        )

        # Configure git user for the test
        subprocess.run(
            ["git", "config", "--global", "user.email", "test@test.com"],
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "--global", "user.name", "Test"],
            capture_output=True,
        )

        plugin.post_action(
            action_name="init",
            kwargs={"vault_name": "test-vault", "client": "obsidian", "tone": "research-partner"},
            result=None,
        )

        assert (tmp_path / ".git").is_dir()

    def test_post_action_init_initial_commit(self, tmp_path: Path):
        # Set up git config
        subprocess.run(
            ["git", "init"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        plugin = GitPlugin(
            config=GitConfig(auto_ignore=True),
            vault_root=tmp_path,
        )
        plugin.post_action(
            action_name="init",
            kwargs={"vault_name": "test-vault", "client": "obsidian", "tone": "research-partner"},
            result=None,
        )

        log = _git_log(tmp_path)
        assert any("test-vault" in msg for msg in log)

    def test_post_action_init_skips_gitignore_when_auto_ignore_off(self, tmp_path: Path):
        plugin = GitPlugin(
            config=GitConfig(auto_ignore=False),
            vault_root=tmp_path,
        )
        plugin.post_action(
            action_name="init",
            kwargs={"vault_name": "test-vault", "client": "obsidian", "tone": "research-partner"},
            result=None,
        )

        gitignore = tmp_path / ".gitignore"
        assert not gitignore.exists()


# ---------------------------------------------------------------------------
# Tests — post_action: no-op actions
# ---------------------------------------------------------------------------


class TestGitPluginNoOpActions:
    """Tests for post_action with no-op action names (reweave, session_start, check)."""

    def test_post_action_reweave_is_noop(self, plugin: GitPlugin, git_vault: Path):
        """reweave action should not stage or commit."""
        before = _git_log(git_vault)
        plugin.post_action(
            action_name="reweave",
            kwargs={"source_id": "N-0001", "affected_ids": [], "links_added": 3},
            result=None,
        )
        after = _git_log(git_vault)
        assert after == before

    def test_post_action_session_start_is_noop(self, plugin: GitPlugin, git_vault: Path):
        """session_start action should not stage or commit."""
        before = _git_log(git_vault)
        plugin.post_action(
            action_name="session_start",
            kwargs={"session_id": "LOG-0001"},
            result=None,
        )
        after = _git_log(git_vault)
        assert after == before

    def test_post_action_check_is_noop(self, plugin: GitPlugin, git_vault: Path):
        """check action should not stage or commit."""
        before = _git_log(git_vault)
        plugin.post_action(
            action_name="check",
            kwargs={"issues_found": 2, "issues_fixed": 1},
            result=None,
        )
        after = _git_log(git_vault)
        assert after == before


# ---------------------------------------------------------------------------
# Tests — batch vs immediate mode
# ---------------------------------------------------------------------------


class TestGitPluginCommitModes:
    """Tests that distinguish batch mode vs immediate mode behavior."""

    def test_batch_mode_defers_commit(self, plugin: GitPlugin, git_vault: Path):
        """Batch mode stages on post_action create but does NOT commit until session close."""
        note = git_vault / "notes" / "N-0099.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Batch Note", encoding="utf-8")

        commits_before = _git_log(git_vault)

        result = _make_ok_result(path="notes/N-0099.md")
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0099",
                "title": "Batch Note",
                "path": "notes/N-0099.md",
                "tags": [],
            },
            result=result,
        )

        # File is staged but no new commit yet
        staged = _staged_files(git_vault)
        assert "notes/N-0099.md" in staged
        commits_after = _git_log(git_vault)
        assert len(commits_after) == len(commits_before), (
            "Batch mode should not commit on post_action create"
        )

    def test_immediate_mode_commits_per_event(self, immediate_plugin: GitPlugin, git_vault: Path):
        """Immediate mode commits after every post_action create."""
        note = git_vault / "notes" / "N-0098.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Immediate Note", encoding="utf-8")

        commits_before = _git_log(git_vault)

        result = _make_ok_result(path="notes/N-0098.md")
        immediate_plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0098",
                "title": "Immediate Note",
                "path": "notes/N-0098.md",
                "tags": [],
            },
            result=result,
        )

        commits_after = _git_log(git_vault)
        assert len(commits_after) == len(commits_before) + 1, (
            "Immediate mode should commit on each post_action create"
        )
        assert any("N-0098" in msg for msg in commits_after)


# ---------------------------------------------------------------------------
# Tests — error safety
# ---------------------------------------------------------------------------


class TestGitPluginErrors:
    """Tests that git failures don't propagate."""

    def test_missing_git_binary_does_not_raise(self, tmp_path: Path):
        plugin = GitPlugin(
            config=GitConfig(enabled=True),
            vault_root=tmp_path,
        )
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            # Should not raise
            plugin.post_action(
                action_name="create_note",
                kwargs={
                    "content_type": "note",
                    "content_id": "N-0001",
                    "title": "Test",
                    "path": "notes/N-0001.md",
                    "tags": [],
                },
                result=None,
            )

    def test_not_a_git_repo_does_not_raise(self, tmp_path: Path):
        """Operations on a non-git directory should silently fail."""
        plugin = GitPlugin(
            config=GitConfig(enabled=True, batch_commits=False),
            vault_root=tmp_path,
        )
        note = tmp_path / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        # Should not raise even though there's no git repo
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            result=None,
        )

    def test_no_vault_root_is_noop(self):
        """Plugin with no vault_root should silently skip all operations."""
        plugin = GitPlugin(config=GitConfig(enabled=True), vault_root=None)
        plugin.post_action(
            action_name="create_note",
            kwargs={
                "content_type": "note",
                "content_id": "N-0001",
                "title": "Test",
                "path": "notes/N-0001.md",
                "tags": [],
            },
            result=None,
        )
        # No error raised


# ---------------------------------------------------------------------------
# Tests — _sanitize_for_commit
# ---------------------------------------------------------------------------


def test_sanitize_for_commit_strips_newlines():
    """_sanitize_for_commit removes characters that could break git commit messages."""
    from ztlctl.plugins.builtins.git import _sanitize_for_commit

    assert _sanitize_for_commit("hello\nworld") == "hello world"
    assert _sanitize_for_commit("hello\rworld") == "hello world"
    assert _sanitize_for_commit("hello\0world") == "helloworld"
    assert _sanitize_for_commit("clean text") == "clean text"
