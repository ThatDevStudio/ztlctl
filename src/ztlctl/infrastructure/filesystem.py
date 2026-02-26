"""Filesystem operations for vault content management.

INVARIANT: Files are truth. The filesystem is authoritative.
The DB is a derived index. ``ztlctl check --rebuild`` must always
be able to reconstruct the DB from files alone.

Pure parsing/rendering utilities live in :mod:`ztlctl.domain.content`
(correct dependency direction: infrastructure -> domain). This module
handles actual file I/O, path resolution, and file discovery.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ztlctl.domain.content import parse_frontmatter, render_frontmatter

# Map content type to vault-relative directory.
CONTENT_PATHS: dict[str, str] = {
    "note": "notes",
    "reference": "notes",
    "log": "ops/logs",
    "task": "ops/tasks",
}

# Directories to skip when discovering content files.
_SKIP_DIRS = frozenset({".ztlctl", ".obsidian", ".git", "self"})


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def read_content_file(path: Path) -> tuple[dict[str, Any], str]:
    """Read a markdown file, returning ``(frontmatter, body)``."""
    content = path.read_text(encoding="utf-8")
    return parse_frontmatter(content)


def write_content_file(path: Path, frontmatter: dict[str, Any], body: str) -> None:
    """Write frontmatter + body to a markdown file.

    Creates parent directories if they don't exist.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = render_frontmatter(frontmatter, body)
    path.write_text(rendered, encoding="utf-8")


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def resolve_content_path(
    vault_root: Path,
    content_type: str,
    content_id: str,
    *,
    topic: str | None = None,
) -> Path:
    """Resolve the filesystem path for a content item.

    - Notes/references: ``{vault}/notes/{topic}/{id}.md`` (topic optional)
    - Logs: ``{vault}/ops/logs/{id}.jsonl``
    - Tasks: ``{vault}/ops/tasks/{id}.md``
    """
    base_dir = CONTENT_PATHS.get(content_type)
    if base_dir is None:
        msg = f"Unknown content type: {content_type!r}"
        raise ValueError(msg)

    path = vault_root / base_dir
    if topic and content_type in ("note", "reference"):
        path = path / topic

    ext = ".jsonl" if content_type == "log" else ".md"
    result = path / f"{content_id}{ext}"

    # Guard against path traversal via crafted topic or content_id
    vault_resolved = vault_root.resolve()
    if not result.resolve().is_relative_to(vault_resolved):
        msg = f"Path escapes vault root: {result}"
        raise ValueError(msg)

    return result


def find_content_files(
    vault_root: Path,
    *,
    content_type: str | None = None,
) -> list[Path]:
    """Discover all content files in the vault.

    Walks ``notes/`` and ``ops/`` directories, skipping ``.ztlctl/``,
    ``.obsidian/``, ``.git/``, and ``self/``. Optionally filters by
    *content_type* based on :data:`CONTENT_PATHS`.
    """
    if content_type is not None:
        base_dir = CONTENT_PATHS.get(content_type)
        if base_dir is None:
            msg = f"Unknown content type: {content_type!r}"
            raise ValueError(msg)
        search_roots = [vault_root / base_dir]
    else:
        search_roots = [vault_root / "notes", vault_root / "ops"]

    results: list[Path] = []
    for root in search_roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in _SKIP_DIRS for part in path.parts):
                continue
            if path.suffix in (".md", ".jsonl"):
                results.append(path)

    return sorted(results)
