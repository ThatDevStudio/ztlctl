"""Built-in Git plugin for automatic version control.

Hooks into lifecycle events to stage, commit, and push changes.
Batch mode (default): stage on each operation, commit once at session close.
(DESIGN.md Section 15)
"""

from __future__ import annotations

import pluggy

hookimpl = pluggy.HookimplMarker("ztlctl")


class GitPlugin:
    """Git integration plugin."""

    @hookimpl
    def post_create(
        self,
        content_type: str,
        content_id: str,
        title: str,
        path: str,
        tags: list[str],
    ) -> None:
        """Stage newly created files."""
        # Implementation deferred to plugin system feature

    @hookimpl
    def post_session_close(
        self,
        session_id: str,
        stats: dict[str, object],
    ) -> None:
        """Commit staged changes at session close."""
        # Implementation deferred to plugin system feature
