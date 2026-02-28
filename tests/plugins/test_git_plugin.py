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
# Tests — post_create
# ---------------------------------------------------------------------------


class TestGitPluginPostCreate:
    """Tests for the post_create hook."""

    def test_stages_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        plugin.post_create(
            content_type="note",
            content_id="N-0001",
            title="Test",
            path="notes/N-0001.md",
            tags=["test"],
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged

    def test_commits_immediately_when_not_batched(
        self, immediate_plugin: GitPlugin, git_vault: Path
    ):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        immediate_plugin.post_create(
            content_type="note",
            content_id="N-0001",
            title="Test",
            path="notes/N-0001.md",
            tags=["test"],
        )

        log = _git_log(git_vault)
        assert any("N-0001" in msg for msg in log)

    def test_skips_when_disabled(self, git_vault: Path):
        plugin = GitPlugin(
            config=GitConfig(enabled=False),
            vault_root=git_vault,
        )
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Test", encoding="utf-8")

        plugin.post_create(
            content_type="note",
            content_id="N-0001",
            title="Test",
            path="notes/N-0001.md",
            tags=[],
        )

        staged = _staged_files(git_vault)
        assert staged == []


# ---------------------------------------------------------------------------
# Tests — post_update / post_close
# ---------------------------------------------------------------------------


class TestGitPluginPostUpdate:
    """Tests for the post_update hook."""

    def test_stages_updated_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Updated", encoding="utf-8")

        plugin.post_update(
            content_type="note",
            content_id="N-0001",
            fields_changed=["title"],
            path="notes/N-0001.md",
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged


class TestGitPluginPostClose:
    """Tests for the post_close hook."""

    def test_stages_closed_file(self, plugin: GitPlugin, git_vault: Path):
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Closed", encoding="utf-8")

        plugin.post_close(
            content_type="note",
            content_id="N-0001",
            path="notes/N-0001.md",
            summary="archived",
        )

        staged = _staged_files(git_vault)
        assert "notes/N-0001.md" in staged


# ---------------------------------------------------------------------------
# Tests — session close
# ---------------------------------------------------------------------------


class TestGitPluginSessionClose:
    """Tests for the post_session_close hook."""

    def test_batch_commit_at_session_close(self, plugin: GitPlugin, git_vault: Path):
        # Stage some files first
        note = git_vault / "notes" / "N-0001.md"
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text("# Note", encoding="utf-8")
        plugin.post_create(
            content_type="note",
            content_id="N-0001",
            title="Note",
            path="notes/N-0001.md",
            tags=[],
        )

        plugin.post_session_close(
            session_id="LOG-0001",
            stats={"created": 0, "updated": 0},
        )

        log = _git_log(git_vault)
        assert any("LOG-0001" in msg for msg in log)
        assert any("1 created, 0 updated" in msg for msg in log)

    def test_session_close_skips_commit_when_nothing_staged(
        self, plugin: GitPlugin, git_vault: Path
    ):
        before = _git_log(git_vault)

        plugin.post_session_close(
            session_id="LOG-0001",
            stats={"created": 99, "updated": 99},
        )

        after = _git_log(git_vault)
        assert after == before

    def test_session_close_reports_renamed_files(self, plugin: GitPlugin, git_vault: Path):
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

        plugin.post_session_close(
            session_id="LOG-0002",
            stats={"created": 0, "updated": 0},
        )

        log = _git_log(git_vault)
        assert any("LOG-0002" in msg and "1 renamed" in msg for msg in log)

    def test_auto_push_calls_git_push(self, git_vault: Path):
        push_plugin = GitPlugin(
            config=GitConfig(auto_push=True, batch_commits=True),
            vault_root=git_vault,
        )

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(
                args=[], returncode=0, stdout="", stderr=""
            )
            push_plugin.post_session_close(
                session_id="LOG-0001",
                stats={"created": 0, "updated": 0},
            )

        # Verify git push was called
        push_calls = [c for c in mock_run.call_args_list if "push" in c.args[0]]
        assert len(push_calls) >= 1


# ---------------------------------------------------------------------------
# Tests — post_init
# ---------------------------------------------------------------------------


class TestGitPluginInit:
    """Tests for the post_init hook."""

    def test_creates_gitignore(self, tmp_path: Path):
        plugin = GitPlugin(
            config=GitConfig(auto_ignore=True),
            vault_root=tmp_path,
        )
        plugin.post_init(vault_name="test-vault", client="obsidian", tone="research-partner")

        gitignore = tmp_path / ".gitignore"
        assert gitignore.exists()
        content = gitignore.read_text(encoding="utf-8")
        assert "backups" in content

    def test_runs_git_init(self, tmp_path: Path):
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

        plugin.post_init(vault_name="test-vault", client="obsidian", tone="research-partner")

        assert (tmp_path / ".git").is_dir()

    def test_initial_commit(self, tmp_path: Path):
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
        plugin.post_init(vault_name="test-vault", client="obsidian", tone="research-partner")

        log = _git_log(tmp_path)
        assert any("test-vault" in msg for msg in log)

    def test_skips_gitignore_when_auto_ignore_off(self, tmp_path: Path):
        plugin = GitPlugin(
            config=GitConfig(auto_ignore=False),
            vault_root=tmp_path,
        )
        plugin.post_init(vault_name="test-vault", client="obsidian", tone="research-partner")

        gitignore = tmp_path / ".gitignore"
        assert not gitignore.exists()


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
            plugin.post_create(
                content_type="note",
                content_id="N-0001",
                title="Test",
                path="notes/N-0001.md",
                tags=[],
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
        plugin.post_create(
            content_type="note",
            content_id="N-0001",
            title="Test",
            path="notes/N-0001.md",
            tags=[],
        )

    def test_no_vault_root_is_noop(self):
        """Plugin with no vault_root should silently skip all operations."""
        plugin = GitPlugin(config=GitConfig(enabled=True), vault_root=None)
        plugin.post_create(
            content_type="note",
            content_id="N-0001",
            title="Test",
            path="notes/N-0001.md",
            tags=[],
        )
        # No error raised
