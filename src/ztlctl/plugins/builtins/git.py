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


def _sanitize_for_commit(text: str) -> str:
    """Remove newlines and null bytes from user-supplied text for commit messages."""
    return text.replace("\n", " ").replace("\r", " ").replace("\0", "")


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

    Implements the stable post_action hookspec (PLUG-02). The 8 per-event
    hookimpls (post_create, post_update, etc.) have been removed; all routing
    is done inside post_action via action_name filtering.
    """

    PLUGIN_API_VERSION = 1

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
    # Security — capability declaration (SECU-02)
    # ------------------------------------------------------------------

    @hookimpl
    def declare_capabilities(self) -> set[str]:
        """Declare that this plugin uses git operations."""
        return {"git", "filesystem"}

    # ------------------------------------------------------------------
    # Lifecycle hook — single post_action replaces 8 per-event methods
    # ------------------------------------------------------------------

    @hookimpl
    def post_action(
        self,
        action_name: str,
        kwargs: dict[str, Any],
        result: Any,
    ) -> None:
        """Route lifecycle events to git operations via action_name filtering.

        Handles: create_note, create_reference, create_task, update,
        close, archive, session_close, init.

        No-ops: reweave, session_start, check, check_rebuild, and any unknown
        action names.

        ``result=None`` (EventBus bridge path) is treated as a pass-through.
        An explicit ``result.ok=False`` skips all git operations.
        """
        if not self._enabled:
            return

        # Guard: skip if result indicates failure. None = pass-through.
        # Result may be a ServiceResult object or a dict (from ActionEvent serialization).
        if result is not None:
            ok = result.get("ok") if isinstance(result, dict) else getattr(result, "ok", True)
            if not ok:
                return

        if action_name in {"create_note", "create_reference", "create_task"}:
            self._handle_create(action_name, kwargs)
        elif action_name == "update":
            self._handle_update(kwargs)
        elif action_name in {"close", "archive"}:
            self._handle_close(kwargs)
        elif action_name in {"reweave", "session_start", "check", "check_rebuild"}:
            pass  # No-op
        elif action_name == "session_close":
            self._handle_session_close(kwargs)
        elif action_name == "init":
            self._handle_init(kwargs)
        # Unknown action names are silently ignored

    # ------------------------------------------------------------------
    # Action-specific handlers
    # ------------------------------------------------------------------

    def _handle_create(self, action_name: str, kwargs: dict[str, Any]) -> None:
        """Stage newly created files. Commit immediately if not batched."""
        path = kwargs.get("path", ".")
        self._git_add(path)
        if not self._config.batch_commits:
            content_type = kwargs.get("content_type", "note")
            content_id = kwargs.get("content_id", "") or kwargs.get("id", "")
            title = kwargs.get("title", "")
            self._git_commit(
                f"feat: create {content_type} {_sanitize_for_commit(content_id)}"
                f" — {_sanitize_for_commit(title)}"
            )

    def _handle_update(self, kwargs: dict[str, Any]) -> None:
        """Stage updated files. Commit immediately if not batched."""
        path = kwargs.get("path", ".")
        self._git_add(path)
        if not self._config.batch_commits:
            content_id = kwargs.get("content_id", "") or kwargs.get("id", "")
            fields_changed = kwargs.get("fields_changed", [])
            fields = ", ".join(fields_changed)
            self._git_commit(f"docs: update {_sanitize_for_commit(content_id)} ({fields})")

    def _handle_close(self, kwargs: dict[str, Any]) -> None:
        """Stage closed/archived files. Commit immediately if not batched."""
        path = kwargs.get("path", ".")
        self._git_add(path)
        if not self._config.batch_commits:
            content_id = kwargs.get("content_id", "") or kwargs.get("id", "")
            summary = kwargs.get("summary", "")
            self._git_commit(
                f"docs: close {_sanitize_for_commit(content_id)} — {_sanitize_for_commit(summary)}"
            )

    def _handle_session_close(self, kwargs: dict[str, Any]) -> None:
        """Commit all staged changes at session close. Optionally push."""
        if self._config.batch_commits:
            summary = self._git_staged_summary()
            if summary is not None and summary["has_staged"]:
                session_id = kwargs.get("session_id", "")
                parts = [
                    f"{summary['created']} created",
                    f"{summary['updated']} updated",
                ]
                if summary["renamed"] > 0:
                    parts.append(f"{summary['renamed']} renamed")
                self._git_commit(f"docs: session {session_id} — {', '.join(parts)}")
        if self._config.auto_push:
            self._git_push()

    def _handle_init(self, kwargs: dict[str, Any]) -> None:
        """Initialize git repo in new vault. Create .gitignore and initial commit."""
        if self._config.auto_ignore:
            self._write_gitignore()
        self._git_init()
        self._git_add(".")
        vault_name = kwargs.get("vault_name", "vault")
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
