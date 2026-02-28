"""VectorService — sqlite-vec vector storage and similarity search.

Requires: sqlite-vec extension, EmbeddingProvider (sentence-transformers).
All operations gated by is_available() — graceful no-op when deps missing.
"""

from __future__ import annotations

import logging
import struct
from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import trace_span, traced

if TYPE_CHECKING:
    from ztlctl.infrastructure.embeddings import EmbeddingProvider

logger = logging.getLogger(__name__)


def _serialize_f32(vec: list[float]) -> bytes:
    """Serialize a float list to compact binary format for sqlite-vec."""
    return struct.pack(f"{len(vec)}f", *vec)


class VectorService(BaseService):
    """Manages vector embeddings for semantic search."""

    def __init__(
        self,
        vault: Any,
        *,
        provider: EmbeddingProvider | None = None,
    ) -> None:
        super().__init__(vault)
        self._provider = provider
        self._vec_available: bool | None = None

    def _ensure_provider(self) -> EmbeddingProvider:
        if self._provider is None:
            from ztlctl.infrastructure.embeddings import EmbeddingProvider

            cfg = self._vault.settings.search
            self._provider = EmbeddingProvider(
                model_name=cfg.embedding_model
                if cfg.embedding_model != "local"
                else "all-MiniLM-L6-v2",
                dim=cfg.embedding_dim,
            )
        return self._provider

    @staticmethod
    def _driver_connection(conn: Any) -> Any:
        """Return the underlying sqlite3 connection for extension loading."""
        pool_conn = conn.connection
        return getattr(pool_conn, "driver_connection", pool_conn.connection)

    def is_available(self) -> bool:
        """Check if sqlite-vec extension can be loaded."""
        if self._vec_available is not None:
            return self._vec_available
        try:
            import sqlite_vec  # type: ignore[import-not-found]

            with self._vault.engine.connect() as conn:
                raw = self._driver_connection(conn)
                sqlite_vec.load(raw)
            self._vec_available = True
        except Exception:
            self._vec_available = False
        return self._vec_available

    def ensure_table(self) -> None:
        """Create the vec_items virtual table if it doesn't exist."""
        if not self.is_available():
            return
        dim = self._vault.settings.search.embedding_dim
        with self._vault.engine.connect() as conn:
            raw = self._driver_connection(conn)
            import sqlite_vec

            sqlite_vec.load(raw)
            conn.execute(
                text(
                    f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_items "
                    f"USING vec0(node_id TEXT PRIMARY KEY, embedding FLOAT[{dim}])"
                )
            )
            conn.commit()

    @traced
    def index_node(self, node_id: str, content: str) -> None:
        """Embed content and store in vec_items."""
        if not self.is_available():
            return
        provider = self._ensure_provider()
        vec = provider.embed(content)
        blob = _serialize_f32(vec)
        with self._vault.engine.connect() as conn:
            raw = self._driver_connection(conn)
            import sqlite_vec

            sqlite_vec.load(raw)
            # Upsert: delete then insert (sqlite-vec doesn't support ON CONFLICT)
            conn.execute(text("DELETE FROM vec_items WHERE node_id = :nid"), {"nid": node_id})
            conn.execute(
                text("INSERT INTO vec_items(node_id, embedding) VALUES (:nid, :emb)"),
                {"nid": node_id, "emb": blob},
            )
            conn.commit()

    @traced
    def remove_node(self, node_id: str) -> None:
        """Remove a node's embedding from vec_items."""
        if not self.is_available():
            return
        with self._vault.engine.connect() as conn:
            raw = self._driver_connection(conn)
            import sqlite_vec

            sqlite_vec.load(raw)
            conn.execute(text("DELETE FROM vec_items WHERE node_id = :nid"), {"nid": node_id})
            conn.commit()

    @traced
    def search_similar(
        self,
        query_text: str,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Find nodes most similar to query text by cosine distance."""
        if not self.is_available():
            return []
        provider = self._ensure_provider()
        with trace_span("embed_query"):
            query_vec = provider.embed(query_text)
        blob = _serialize_f32(query_vec)

        with self._vault.engine.connect() as conn:
            raw = self._driver_connection(conn)
            import sqlite_vec

            sqlite_vec.load(raw)
            rows = conn.execute(
                text(
                    "SELECT node_id, distance FROM vec_items "
                    "WHERE embedding MATCH :qvec AND k = :k "
                    "ORDER BY distance"
                ),
                {"qvec": blob, "k": limit},
            ).fetchall()

        return [{"node_id": r.node_id, "distance": float(r.distance)} for r in rows]

    @traced
    def reindex_all(self) -> ServiceResult:
        """Re-embed all non-archived nodes."""
        op = "vector_reindex"
        if not self.is_available():
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="SEMANTIC_UNAVAILABLE",
                    message="sqlite-vec extension not available",
                ),
            )
        provider = self._ensure_provider()

        with self._vault.engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT n.id, n.title, COALESCE(fts.body, '') AS body "
                    "FROM nodes n LEFT JOIN nodes_fts fts ON n.id = fts.id "
                    "WHERE n.archived = 0"
                )
            ).fetchall()

        texts = [f"{r.title} {r.body}".strip() for r in rows]
        node_ids = [r.id for r in rows]

        if not texts:
            return ServiceResult(ok=True, op=op, data={"indexed_count": 0})

        with trace_span("batch_embed"):
            vectors = provider.embed_batch(texts)

        with self._vault.engine.connect() as conn:
            raw = self._driver_connection(conn)
            import sqlite_vec

            sqlite_vec.load(raw)
            conn.execute(text("DELETE FROM vec_items"))
            for nid, vec in zip(node_ids, vectors):
                blob = _serialize_f32(vec)
                conn.execute(
                    text("INSERT INTO vec_items(node_id, embedding) VALUES (:nid, :emb)"),
                    {"nid": nid, "emb": blob},
                )
            conn.commit()

        return ServiceResult(
            ok=True,
            op=op,
            data={"indexed_count": len(node_ids)},
        )
