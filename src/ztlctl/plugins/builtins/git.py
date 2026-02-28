"""Built-in Git plugin for automatic version control.

Hooks into lifecycle events to stage, commit, and push changes.
Batch mode (default): stage on each operation, commit once at session close.
Immediate mode: commit after every operation.

All git subprocess calls are wrapped in try/except so a missing git binary
or non-repo directory never interrupts normal vault operations.
(DESIGN.md Section 15)
"""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

import pluggy

from ztlctl.config.models import GitConfig

hookimpl = pluggy.HookimplMarker("ztlctl")

logger = logging.getLogger(__name__)

# Standard .gitignore content for ztlctl vaults
_GITIGNORE_CONTENT = """\
# ztlctl vault gitignore
.ztlctl/backups/
*.db-journal
"""


class GitPlugin:
    """Git integration plugin.

    Stages files on lifecycle events. In batch mode (default), commits
    only at session close. In immediate mode, commits after each operation.
    """

    def __init__(
        self,
        config: GitConfig | None = None,
        vault_root: Path | None = None,
    ) -> None:
        self._config = config or GitConfig()
        self._vault_root = vault_root

    @property
    def _enabled(self) -> bool:
        return self._config.enabled and self._vault_root is not None

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        """Stage newly created files. Commit immediately if not batched."""
        if not self._enabled:
            return
        self._git_add(path)
        if not self._config.batch_commits:
            self._git_commit(f"feat: create {content_type} {content_id} — {title}")

    @hookimpl
    def post_update(
        self,
        content_type: str,
        content_id: str,
        fields_changed: list[str],
        path: str,
    ) -> None:
        """Stage updated files. Commit immediately if not batched."""
        if not self._enabled:
            return
        self._git_add(path)
        if not self._config.batch_commits:
            fields = ", ".join(fields_changed)
            self._git_commit(f"docs: update {content_id} ({fields})")

    @hookimpl
    def post_close(
        self,
        content_type: str,
        content_id: str,
        path: str,
        summary: str,
    ) -> None:
        """Stage closed/archived files. Commit immediately if not batched."""
        if not self._enabled:
            return
        self._git_add(path)
        if not self._config.batch_commits:
            self._git_commit(f"docs: close {content_id} — {summary}")

    @hookimpl
    def post_reweave(
        self,
        source_id: str,
        affected_ids: list[str],
        links_added: int,
    ) -> None:
        """No-op — frontmatter changes are committed at session close."""

    @hookimpl
    def post_session_start(self, session_id: str) -> None:
        """No-op — sessions don't need a git operation on start."""

    @hookimpl
    def post_session_close(
        self,
        session_id: str,
        stats: dict[str, Any],
    ) -> None:
        """Commit all staged changes at session close. Optionally push."""
        if not self._enabled:
            return
        if self._config.batch_commits:
            summary = self._git_staged_summary()
            if summary is not None and summary["has_staged"]:
                parts = [
                    f"{summary['created']} created",
                    f"{summary['updated']} updated",
                ]
                if summary["renamed"] > 0:
                    parts.append(f"{summary['renamed']} renamed")
                self._git_commit(f"docs: session {session_id} — {', '.join(parts)}")
        if self._config.auto_push:
            self._git_push()

    @hookimpl
    def post_check(
        self,
        issues_found: int,
        issues_fixed: int,
    ) -> None:
        """No-op — integrity checks don't modify tracked files."""

    @hookimpl
    def post_init(
        self,
        vault_name: str,
        client: str,
        tone: str,
    ) -> None:
        """Initialize git repo in new vault. Create .gitignore and initial commit."""
        if not self._enabled:
            return
        if self._config.auto_ignore:
            self._write_gitignore()
        self._git_init()
        self._git_add(".")
        self._git_commit(f"feat: initialize vault '{vault_name}'")

    # ------------------------------------------------------------------
    # Git subprocess helpers
    # ------------------------------------------------------------------

    def _run_git(self, *args: str) -> subprocess.CompletedProcess[str]:
        """Run a git command in the vault root. Raises on failure."""
        assert self._vault_root is not None
        return subprocess.run(
            ["git", *args],
            cwd=self._vault_root,
            capture_output=True,
            text=True,
            check=True,
        )

    def _git_add(self, path: str) -> None:
        """Stage a file (or '.' for all)."""
        try:
            self._run_git("add", path)
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.debug("git add failed: %s", exc)

    def _git_commit(self, message: str) -> None:
        """Commit staged changes. No-op if nothing staged."""
        try:
            # Check if there are staged changes first
            result = self._run_git("diff", "--cached", "--quiet")
            # Exit code 0 means no staged changes
            if result.returncode == 0:
                return
        except subprocess.CalledProcessError:
            # Exit code 1 means there ARE staged changes — proceed to commit
            pass
        except OSError as exc:
            logger.debug("git diff --cached failed: %s", exc)
            return

        try:
            self._run_git("commit", "-m", message)
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.debug("git commit failed: %s", exc)

    def _git_staged_summary(self) -> dict[str, int | bool] | None:
        """Summarize staged changes from git diff metadata."""
        try:
            result = self._run_git("diff", "--cached", "--name-status")
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.debug("git diff --cached --name-status failed: %s", exc)
            return None

        summary: dict[str, int | bool] = {
            "has_staged": False,
            "created": 0,
            "updated": 0,
            "renamed": 0,
        }
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            summary["has_staged"] = True
            status = line.split("\t", 1)[0][:1]
            if status in {"A", "C"}:
                summary["created"] += 1
            elif status == "M":
                summary["updated"] += 1
            elif status == "R":
                summary["renamed"] += 1
        return summary

    def _git_push(self) -> None:
        """Push to remote."""
        try:
            self._run_git("push")
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.debug("git push failed: %s", exc)

    def _git_init(self) -> None:
        """Initialize a git repository."""
        try:
            self._run_git("init")
        except (OSError, subprocess.CalledProcessError) as exc:
            logger.debug("git init failed: %s", exc)

    def _write_gitignore(self) -> None:
        """Write a .gitignore file if one doesn't exist."""
        assert self._vault_root is not None
        gitignore = self._vault_root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(_GITIGNORE_CONTENT, encoding="utf-8")
