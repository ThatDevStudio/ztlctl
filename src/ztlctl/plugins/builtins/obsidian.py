"""First-party Obsidian workspace profile plugin."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

import pluggy

from ztlctl.plugins.contracts import (
    VaultInitContext,
    VaultInitInstruction,
    VaultInitStepContribution,
    VaultInitStepResult,
    WorkspaceProfileContribution,
)

hookimpl = pluggy.HookimplMarker("ztlctl")

_COMMUNITY_PLUGIN_IDS = (
    "dataview",
    "templater-obsidian",
    "folder-notes",
    "omnisearch",
    "obsidian-book-search-plugin",
)

_CORE_PLUGIN_STATES = {
    "file-explorer": True,
    "global-search": False,
    "switcher": False,
    "graph": True,
    "backlink": True,
    "outgoing-link": True,
    "tag-pane": True,
    "page-preview": True,
    "daily-notes": False,
    "templates": True,
    "note-composer": False,
    "command-palette": True,
    "slash-command": False,
    "editor-status": False,
    "markdown-importer": False,
    "zk-prefixer": False,
    "random-note": False,
    "outline": True,
    "word-count": False,
    "slides": False,
    "audio-recorder": False,
    "workspaces": False,
    "file-recovery": False,
    "publish": False,
    "sync": False,
    "canvas": True,
    "footnotes": False,
    "properties": True,
    "bookmarks": True,
    "bases": False,
    "webviewer": False,
}

_ZTLCTL_CSS = """\
/* ztlctl vault styling for Obsidian */
.ztlctl-seed { color: var(--text-muted); }
.ztlctl-budding { color: var(--text-normal); }
.ztlctl-evergreen { color: var(--text-accent); font-weight: 700; }
"""

_GARDEN_LAYERS_CSS = """\
/* Human garden layer styling */
.garden-note {
  border-left: 3px solid var(--color-green);
  padding-left: 0.9rem;
}

.seed {
  color: var(--text-muted);
}

.budding {
  color: var(--text-normal);
  border-left-color: var(--color-yellow);
}

.evergreen {
  color: var(--text-accent);
  border-left-color: var(--color-green);
}

.grove-note {
  border-left: 3px solid var(--color-cyan);
  padding-left: 0.9rem;
}

.book-note {
  border-left: 3px solid var(--color-orange);
  padding-left: 0.9rem;
}

.machine-note {
  border-left: 3px solid var(--text-faint);
  padding-left: 0.9rem;
}
"""


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _obsidian_instructions() -> tuple[VaultInitInstruction, ...]:
    return (
        VaultInitInstruction(
            instruction_id="obsidian.install_plugins",
            title="Install the curated Obsidian plugins",
            body=(
                "Open Obsidian, trust the vault, then go to Settings -> Community plugins -> "
                "Browse and install the plugins that this starter kit preconfigures."
            ),
            items=(
                "Dataview (id: dataview) for structured note queries and future garden dashboards.",
                "Templater (id: templater-obsidian) so the starter templates can stamp dates "
                "and metadata.",
                "Folder notes (id: folder-notes) for grove and library folder overviews.",
                "Omnisearch (id: omnisearch) for faster full-vault retrieval.",
                "Book Search (id: obsidian-book-search-plugin) for creating "
                "garden/library book notes from metadata.",
            ),
            kind="install",
        ),
        VaultInitInstruction(
            instruction_id="obsidian.enable_plugins",
            title="Enable the installed plugins",
            body=(
                "After installation, enable each plugin so Obsidian picks up the scaffolded "
                "configuration already written into .obsidian/."
            ),
            items=(
                "If the vault was already open in Obsidian, reload the app or reopen the vault "
                "after enabling them.",
                "The starter kit writes plugin config files for Folder notes, Omnisearch, and "
                "Book Search.",
            ),
            kind="manual",
        ),
        VaultInitInstruction(
            instruction_id="obsidian.verify_defaults",
            title="Verify the Obsidian workspace defaults",
            body="The starter kit expects a few Obsidian defaults to be active on first use.",
            items=(
                "New notes should default to garden/notes.",
                "Attachments should default to garden/attachments.",
                "Core Templates should point at garden/templates.",
                "CSS snippets ztlctl and garden-layers should both be enabled.",
                "Graph view should show distinct groups for notes, ops/tasks, ops/logs, "
                "garden/notes, garden/groves, and garden/library.",
            ),
            kind="verify",
        ),
    )


def _render_instruction_section(instructions: tuple[VaultInitInstruction, ...]) -> str:
    lines = ["## First Open in Obsidian", ""]
    for instruction in instructions:
        lines.append(f"### {instruction.title}")
        lines.append("")
        lines.append(instruction.body)
        lines.append("")
        for item in instruction.items:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _garden_readme() -> str:
    instructions = _render_instruction_section(_obsidian_instructions())
    return dedent(
        f"""\
        # Garden Workspace

        This profile creates a hybrid workspace:

        - `notes/` and `ops/` are the machine/core layer that ztlctl indexes and mutates.
        - `.obsidian/` is profile-managed starter-kit configuration.
        - `garden/` is the human-owned enrichment layer scaffolded for Obsidian use.

        ## Garden Directories

        - `garden/notes/` holds developing notes that begin at `seed` and can mature to
          `budding` and `evergreen`.
        - `garden/groves/` holds overview notes that organize a patch of related garden work.
        - `garden/library/` holds book notes and source-oriented reading notes.
        - `garden/canvases/` holds canvases and spatial working areas.
        - `garden/templates/` holds the templates used by Obsidian Templates and Templater.
        - `garden/attachments/` is the default attachment target for the Obsidian starter kit.

        ## Ownership

        - `.obsidian/` is profile-managed and may be replaced by future profile update flows.
        - `garden/` is scaffolded by the profile once, then treated as human-managed content.
        - ztlctl still indexes only `notes/` and `ops/` by default.

        ## Maturity Vocabulary

        - `seed`: an early note worth keeping but not yet integrated
        - `budding`: a note with structure, evidence, or emerging links
        - `evergreen`: a stable note that is broadly reusable

        {instructions}"""
    )


def _note_template() -> str:
    return dedent(
        """\
        ---
        title: <% tp.file.title %>
        aliases: []
        cssclasses: [garden-note, seed]
        tags: []
        growth: seed
        planted: <% tp.date.now("YYYY-MM-DD") %>
        tended: <% tp.date.now("YYYY-MM-DD") %>
        ---

        ## Prompt

        What idea or observation is worth preserving here?

        ## Notes

        -

        ## Connections

        -
        """
    )


def _grove_template() -> str:
    return dedent(
        """\
        ---
        title: <% tp.file.title %>
        aliases: []
        cssclasses: [grove-note]
        tags: []
        planted: <% tp.date.now("YYYY-MM-DD") %>
        tended: <% tp.date.now("YYYY-MM-DD") %>
        ---

        ## Scope

        What part of the garden does this grove organize?

        ## Notes in This Grove

        -

        ## Open Questions

        -
        """
    )


def _book_template() -> str:
    return dedent(
        """\
        ---
        title: "{{title}}"
        author: "{{author}}"
        isbn: "{{isbn}}"
        published: "{{publishDate}}"
        cover: "{{thumbnail}}"
        cssclasses: [book-note]
        tags: []
        ---

        ## Why This Matters

        -

        ## Summary

        -

        ## Highlights

        -

        ## Connections

        -
        """
    )


def _folder_notes_config() -> dict[str, object]:
    return {
        "syncFolderName": True,
        "hideFolderNote": True,
        "folderNoteName": "{{folder_name}}",
        "newFolderNoteName": "{{folder_name}}",
        "storageLocation": "insideFolder",
        "supportedFileTypes": ["md", "canvas", "base"],
        "ignoreAttachmentFolder": True,
        "autoCreate": False,
        "syncMove": True,
        "syncDelete": False,
    }


def _book_search_config() -> dict[str, object]:
    return {
        "folder": "garden/library",
        "fileNameFormat": "",
        "frontmatter": "",
        "content": "",
        "useDefaultFrontmatter": True,
        "defaultFrontmatterKeyType": "Camel Case",
        "templateFile": "garden/templates/book.md",
        "serviceProvider": "google",
        "localePreference": "default",
        "apiKey": "",
        "openPageOnCompletion": True,
        "showCoverImageInSearch": False,
        "enableCoverImageSave": False,
        "enableCoverImageEdgeCurl": True,
        "coverImagePath": "",
        "askForLocale": True,
    }


def _omnisearch_config() -> dict[str, object]:
    return {
        "useCache": True,
        "hideExcluded": False,
        "recencyBoost": "0",
        "showExcerpt": True,
        "ribbonIcon": True,
        "httpApiEnabled": False,
        "showPreviousQueryResults": True,
        "maxEmbeds": 5,
        "renderLineReturnInExcerpts": True,
        "highlight": True,
        "simpleSearch": False,
    }


def _graph_config() -> dict[str, object]:
    return {
        "collapse-filter": False,
        "search": "-path:garden/templates -path:.ztlctl -path:self",
        "showTags": True,
        "showAttachments": False,
        "hideUnresolved": False,
        "showOrphans": True,
        "collapse-color-groups": False,
        "colorGroups": [
            {"query": "path:notes", "color": {"a": 1, "rgb": 5025616}},
            {"query": "path:ops/tasks", "color": {"a": 1, "rgb": 14563684}},
            {"query": "path:ops/logs", "color": {"a": 1, "rgb": 8947848}},
            {"query": "path:garden/notes", "color": {"a": 1, "rgb": 9139988}},
            {"query": "path:garden/groves", "color": {"a": 1, "rgb": 4504796}},
            {"query": "path:garden/library", "color": {"a": 1, "rgb": 14524637}},
        ],
        "collapse-display": True,
        "showArrow": True,
        "textFadeMultiplier": 0,
        "nodeSizeMultiplier": 1,
        "lineSizeMultiplier": 1,
        "collapse-forces": True,
        "centerStrength": 0.5,
        "repelStrength": 20,
        "linkStrength": 1,
        "linkDistance": 30,
    }


def _obsidian_scaffold(context: VaultInitContext) -> VaultInitStepResult:
    files_created: list[str] = []
    vault_root = context.vault_root

    json_files: dict[str, object] = {
        ".obsidian/app.json": {
            "alwaysUpdateLinks": False,
            "newFileLocation": "folder",
            "newFileFolderPath": "garden/notes",
            "attachmentFolderPath": "garden/attachments",
            "promptDelete": True,
            "showUnsupportedFiles": False,
            "defaultViewMode": "source",
            "livePreview": False,
        },
        ".obsidian/appearance.json": {
            "accentColor": "",
            "cssTheme": "",
            "enabledCssSnippets": ["ztlctl", "garden-layers"],
        },
        ".obsidian/core-plugins.json": _CORE_PLUGIN_STATES,
        ".obsidian/community-plugins.json": list(_COMMUNITY_PLUGIN_IDS),
        ".obsidian/templates.json": {"folder": "garden/templates"},
        ".obsidian/graph.json": _graph_config(),
        ".obsidian/plugins/folder-notes/data.json": _folder_notes_config(),
        ".obsidian/plugins/obsidian-book-search-plugin/data.json": _book_search_config(),
        ".obsidian/plugins/omnisearch/data.json": _omnisearch_config(),
    }
    text_files = {
        ".obsidian/snippets/ztlctl.css": _ZTLCTL_CSS,
        ".obsidian/snippets/garden-layers.css": _GARDEN_LAYERS_CSS,
        "garden/README.md": _garden_readme(),
        "garden/templates/note.md": _note_template(),
        "garden/templates/grove.md": _grove_template(),
        "garden/templates/book.md": _book_template(),
        "garden/notes/.gitkeep": "",
        "garden/groves/.gitkeep": "",
        "garden/library/.gitkeep": "",
        "garden/canvases/.gitkeep": "",
        "garden/attachments/.gitkeep": "",
    }

    for rel_path, payload in json_files.items():
        _write_json(vault_root / rel_path, payload)
        files_created.append(rel_path)

    for rel_path, content in text_files.items():
        _write_text(vault_root / rel_path, content)
        files_created.append(rel_path)

    return VaultInitStepResult(files_created=tuple(files_created))


def _obsidian_plugin_install_guidance(_context: VaultInitContext) -> VaultInitStepResult:
    return VaultInitStepResult(instructions=_obsidian_instructions())


class ObsidianProfilePlugin:
    """Expose the shipped Obsidian workspace profile through the plugin surface."""

    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [
            WorkspaceProfileContribution(
                profile_id="obsidian",
                description="First-party Obsidian starter workspace.",
                aliases=(),
                managed_paths=(".obsidian",),
            )
        ]

    @hookimpl
    def register_vault_init_steps(self) -> list[VaultInitStepContribution]:
        return [
            VaultInitStepContribution(
                step_id="obsidian_scaffold",
                description="Write the first-party Obsidian starter kit scaffold.",
                run=_obsidian_scaffold,
                order=100,
                profiles=("obsidian",),
            ),
            VaultInitStepContribution(
                step_id="obsidian_plugin_install_guidance",
                description="Emit post-init Obsidian plugin installation guidance.",
                run=_obsidian_plugin_install_guidance,
                order=200,
                profiles=("obsidian",),
            ),
        ]
