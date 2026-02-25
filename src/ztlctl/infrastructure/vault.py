"""Vault — repository pattern with ACID transaction coordination.

The Vault is the single dependency injected into every service. It owns
the database engine, graph engine, and filesystem operations. The
:meth:`transaction` context manager coordinates DB + file + graph writes
so that if any fail, they all roll back:

- **DB**: Native SQLAlchemy ``engine.begin()`` with auto-commit/rollback.
- **Files**: Compensation-based — newly created files are deleted, modified
  files are restored from backup, on rollback.
- **Graph**: Cache is invalidated on transaction end (success or failure).
  The graph is lazy-rebuilt from DB on next access.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.domain.content import parse_frontmatter, render_frontmatter
from ztlctl.infrastructure.database.engine import init_database
from ztlctl.infrastructure.filesystem import find_content_files, resolve_content_path
from ztlctl.infrastructure.graph.engine import GraphEngine

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy import Connection
    from sqlalchemy.engine import Engine

    from ztlctl.config.settings import ZtlSettings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# File operation tracking for compensation-based rollback
# ---------------------------------------------------------------------------


@dataclass
class _FileOp:
    """A tracked file write within a vault transaction."""

    path: Path
    backup: str | None  # original content for updates, None for creates

    def rollback(self) -> None:
        """Undo this file operation (best-effort)."""
        try:
            if self.backup is not None:
                self.path.write_text(self.backup, encoding="utf-8")
            else:
                self.path.unlink(missing_ok=True)
        except OSError:
            logger.warning("Failed to rollback file operation: %s", self.path)


# ---------------------------------------------------------------------------
# VaultTransaction — yielded to callers within transaction()
# ---------------------------------------------------------------------------


@dataclass
class VaultTransaction:
    """Active transaction context with DB connection and tracked file I/O.

    All file writes must go through :meth:`write_file` so the Vault can
    compensate on rollback. Direct filesystem writes bypass the safety net.
    """

    conn: Connection
    _vault: Vault
    _file_ops: list[_FileOp] = field(default_factory=list, repr=False)

    def write_file(self, path: Path, content: str) -> None:
        """Write *content* to *path*, tracking for rollback.

        If the file already exists, its current content is backed up.
        Parent directories are created as needed.
        """
        backup: str | None = None
        if path.exists():
            backup = path.read_text(encoding="utf-8")

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self._file_ops.append(_FileOp(path=path, backup=backup))

    def write_content(self, path: Path, frontmatter: dict[str, Any], body: str) -> None:
        """Render frontmatter + body and write to *path* (tracked)."""
        rendered = render_frontmatter(frontmatter, body)
        self.write_file(path, rendered)

    def read_file(self, path: Path) -> str:
        """Read raw file content (no tracking needed for reads)."""
        return path.read_text(encoding="utf-8")

    def read_content(self, path: Path) -> tuple[dict[str, Any], str]:
        """Read and parse a markdown content file."""
        raw = self.read_file(path)
        return parse_frontmatter(raw)

    def resolve_path(
        self,
        content_type: str,
        content_id: str,
        *,
        topic: str | None = None,
    ) -> Path:
        """Resolve the vault path for a content item."""
        return resolve_content_path(self._vault.root, content_type, content_id, topic=topic)


# ---------------------------------------------------------------------------
# Vault — the repository
# ---------------------------------------------------------------------------


class Vault:
    """Repository encapsulating database, filesystem, and graph access.

    Constructed once at CLI startup from :class:`ZtlSettings` and stored
    in ``click.Context.obj``.  Services receive the Vault via their
    :class:`BaseService` constructor.
    """

    def __init__(self, settings: ZtlSettings) -> None:
        self._settings = settings
        self._engine: Engine = init_database(self.root)
        self._graph = GraphEngine(self._engine)

    @property
    def root(self) -> Path:
        """The vault root directory."""
        return self._settings.vault_root

    @property
    def engine(self) -> Engine:
        """The underlying SQLAlchemy engine (for direct access when needed)."""
        return self._engine

    @property
    def graph(self) -> GraphEngine:
        """The graph engine (lazy-built from DB edges)."""
        return self._graph

    @property
    def settings(self) -> ZtlSettings:
        """The resolved settings for this vault."""
        return self._settings

    def find_content(self, *, content_type: str | None = None) -> list[Path]:
        """Discover content files in the vault."""
        return find_content_files(self.root, content_type=content_type)

    @contextmanager
    def transaction(self) -> Iterator[VaultTransaction]:
        """Coordinated transaction across DB, files, and graph.

        **ACID guarantees:**

        - DB writes use native SQLAlchemy transaction (auto-commit on
          success, auto-rollback on exception).
        - File writes are tracked for compensation — on failure, created
          files are deleted and modified files are restored from backup.
          Rollback is best-effort per file to avoid masking the original error.
        - Graph cache is invalidated on transaction end (success or
          failure) so the next access rebuilds from committed DB state.

        **Warning:** Do not access ``vault.graph`` within a transaction
        block — the graph is built from committed DB state and will not
        reflect pending writes.  Access the graph only *after* the
        transaction succeeds.

        Usage::

            with vault.transaction() as txn:
                txn.conn.execute(insert(nodes).values(...))
                txn.write_content(path, frontmatter, body)
                # Both commit on success, both roll back on failure.
        """
        file_ops: list[_FileOp] = []
        with self._engine.begin() as conn:
            txn = VaultTransaction(conn=conn, _vault=self, _file_ops=file_ops)
            try:
                yield txn
                # If we reach here, caller's block succeeded.
                # engine.begin() will commit when exiting normally.
            except BaseException:
                # Compensate file writes before DB rollback.
                for op in reversed(file_ops):
                    op.rollback()
                raise
            finally:
                self._graph.invalidate()
