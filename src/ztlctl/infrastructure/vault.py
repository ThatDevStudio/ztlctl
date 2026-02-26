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

from sqlalchemy import insert, select, text

from ztlctl.domain.content import parse_frontmatter, render_frontmatter
from ztlctl.domain.links import extract_frontmatter_links, extract_wikilinks
from ztlctl.domain.tags import parse_tag_parts
from ztlctl.infrastructure.database.engine import init_database
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, tags_registry
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

    # ------------------------------------------------------------------
    # Indexing helpers — consolidated data-access patterns
    # ------------------------------------------------------------------

    def upsert_fts(self, node_id: str, title: str, body: str) -> None:
        """Insert or replace FTS5 index entry (DELETE + INSERT pattern).

        FTS5 virtual tables don't support UPDATE, so we delete any
        existing row first, then insert the new one.
        """
        self.conn.execute(
            text("DELETE FROM nodes_fts WHERE id = :id"),
            {"id": node_id},
        )
        self.conn.execute(
            text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
            {"id": node_id, "title": title, "body": body},
        )

    def delete_fts(self, node_id: str) -> None:
        """Remove FTS5 index entry for a node."""
        self.conn.execute(
            text("DELETE FROM nodes_fts WHERE id = :id"),
            {"id": node_id},
        )

    def clear_fts(self) -> None:
        """Remove all FTS5 entries (for rebuild)."""
        self.conn.execute(text("DELETE FROM nodes_fts"))

    def index_tags(self, node_id: str, tag_list: list[str], today: str) -> int:
        """Register tags and link them to a node. Returns count indexed."""
        count = 0
        for tag in tag_list:
            domain, scope = parse_tag_parts(tag)

            existing = self.conn.execute(
                select(tags_registry.c.tag).where(tags_registry.c.tag == tag)
            ).first()
            if existing is None:
                self.conn.execute(
                    insert(tags_registry).values(
                        tag=tag,
                        domain=domain,
                        scope=scope,
                        created=today,
                    )
                )

            self.conn.execute(insert(node_tags).values(node_id=node_id, tag=tag))
            count += 1
        return count

    def insert_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: str,
        source_layer: str,
        today: str,
        *,
        weight: float = 1.0,
        check_duplicate: bool = False,
        check_target_exists: bool = False,
    ) -> bool:
        """Insert an edge, optionally checking duplicates/target existence.

        Returns True if the edge was inserted, False if skipped.
        """
        if check_target_exists:
            target = self.conn.execute(select(nodes.c.id).where(nodes.c.id == target_id)).first()
            if target is None:
                return False

        if check_duplicate:
            existing = self.conn.execute(
                select(edges.c.source_id).where(
                    edges.c.source_id == source_id,
                    edges.c.target_id == target_id,
                    edges.c.edge_type == edge_type,
                )
            ).first()
            if existing is not None:
                return False

        self.conn.execute(
            insert(edges).values(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                source_layer=source_layer,
                weight=weight,
                created=today,
            )
        )
        return True

    def resolve_wikilink(self, raw: str) -> str | None:
        """Resolve a wikilink target to a node ID.

        Resolution order (DESIGN.md Section 3):
        1. Exact title match
        2. Alias match (JSON array in nodes.aliases via json_each)
        3. Direct ID match
        """
        # 1. Title match
        row = self.conn.execute(select(nodes.c.id).where(nodes.c.title == raw)).first()
        if row is not None:
            return str(row.id)

        # 2. Alias match (JSON array in nodes.aliases)
        alias_row = self.conn.execute(
            text(
                "SELECT nodes.id FROM nodes, json_each(nodes.aliases) WHERE json_each.value = :raw"
            ),
            {"raw": raw},
        ).first()
        if alias_row is not None:
            return str(alias_row.id)

        # 3. Direct ID match (covers [[ztl_abc12345]] style)
        row = self.conn.execute(select(nodes.c.id).where(nodes.c.id == raw)).first()
        if row is not None:
            return str(row.id)

        return None

    def index_links(
        self,
        source_id: str,
        fm_links: dict[str, list[str]],
        body: str,
        today: str,
    ) -> int:
        """Index frontmatter links + body wikilinks for a node.

        Returns total edge count created.
        """
        count = 0

        # Frontmatter typed links
        for link in extract_frontmatter_links(fm_links):
            if self.insert_edge(
                source_id,
                link.target_id,
                link.edge_type,
                "frontmatter",
                today,
                check_target_exists=True,
            ):
                count += 1

        # Body wikilinks
        for wlink in extract_wikilinks(body):
            resolved_id = self.resolve_wikilink(wlink.raw)
            if resolved_id is not None:
                if self.insert_edge(
                    source_id,
                    resolved_id,
                    "relates",
                    "body",
                    today,
                    check_duplicate=True,
                ):
                    count += 1

        return count


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
        self._event_bus: Any | None = None

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

    @property
    def event_bus(self) -> Any | None:
        """The plugin event bus (None if not initialized)."""
        return self._event_bus

    def init_event_bus(self, *, sync: bool = False) -> None:
        """Initialize the plugin event bus.

        Creates a PluginManager, discovers entry-point plugins,
        registers the built-in GitPlugin, and wires up the EventBus.
        Called by AppContext when the vault is first accessed.
        """
        from ztlctl.plugins.builtins.git import GitPlugin
        from ztlctl.plugins.event_bus import EventBus
        from ztlctl.plugins.manager import PluginManager

        pm = PluginManager()
        pm.discover_and_load()

        # Register built-in git plugin with vault context
        git_config = self._settings.git
        git_plugin = GitPlugin(config=git_config, vault_root=self.root)
        pm.register_plugin(git_plugin, name="git-builtin")

        self._event_bus = EventBus(self._engine, pm, sync=sync)

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
