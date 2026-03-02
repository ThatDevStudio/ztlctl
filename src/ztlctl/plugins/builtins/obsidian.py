"""First-party Obsidian workspace profile plugin."""

from __future__ import annotations

from pathlib import Path

import pluggy

from ztlctl.plugins.contracts import WorkspaceProfileContribution

hookimpl = pluggy.HookimplMarker("ztlctl")

_OBSIDIAN_CSS = """\
/* ztlctl vault styling for Obsidian */
.ztlctl-seed { color: var(--text-muted); }
.ztlctl-budding { color: var(--text-normal); }
.ztlctl-evergreen { color: var(--text-accent); font-weight: bold; }
"""


def _obsidian_init_scaffold(vault_root: Path) -> list[str]:
    """Write the first-party Obsidian scaffold for a vault."""
    snippets_dir = vault_root / ".obsidian" / "snippets"
    snippets_dir.mkdir(parents=True, exist_ok=True)
    (snippets_dir / "ztlctl.css").write_text(_OBSIDIAN_CSS, encoding="utf-8")
    return [".obsidian/snippets/ztlctl.css"]


class ObsidianProfilePlugin:
    """Expose the shipped Obsidian workspace profile through the plugin surface."""

    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [
            WorkspaceProfileContribution(
                profile_id="obsidian",
                description="Built-in Obsidian-compatible workspace scaffold.",
                aliases=(),
                managed_paths=(".obsidian",),
                init_scaffold=_obsidian_init_scaffold,
            )
        ]
