"""ReweaveService — graph densification pipeline.

Five-stage: DISCOVER -> SCORE -> FILTER -> PRESENT -> CONNECT
(DESIGN.md Section 5)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import networkx as nx
from sqlalchemy import delete, insert, select, text

from ztlctl.infrastructure.database.schema import edges, node_tags, nodes, reweave_log
from ztlctl.services._helpers import now_iso, today_iso
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult

if TYPE_CHECKING:
    from sqlalchemy import Connection


class ReweaveService(BaseService):
    """Handles link suggestion, creation, and pruning."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reweave(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Run reweave on a specific item or the latest creation.

        Pipeline: DISCOVER -> SCORE -> FILTER -> PRESENT/CONNECT
        """
        op = "reweave"
        cfg = self._vault.settings.reweave

        if not cfg.enabled:
            return ServiceResult(
                ok=True,
                op=op,
                data={"suggestions": [], "skipped": True},
                warnings=["Reweave is disabled in settings"],
            )

        with self._vault.engine.connect() as conn:
            # -- DISCOVER --
            target = self._discover_target(conn, content_id)
            if target is None:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"No target found for reweave (id={content_id})",
                    ),
                )

            target_id = str(target.id)

            # Get existing neighbors (already linked)
            existing_targets = self._get_existing_targets(conn, target_id)

            # Get candidates (non-archived, not self, not already linked)
            candidates = self._get_candidates(conn, target_id, existing_targets)
            if not candidates:
                return ServiceResult(
                    ok=True,
                    op=op,
                    data={"target_id": target_id, "suggestions": [], "count": 0},
                )

            # -- SCORE --
            target_tags = self._get_node_tags(conn, target_id)
            target_topic = target.topic
            target_title = str(target.title)

            scored = self._score_candidates(
                conn,
                target_id=target_id,
                target_title=target_title,
                target_tags=target_tags,
                target_topic=target_topic,
                candidates=candidates,
                cfg=cfg,
            )

            # -- FILTER --
            threshold = cfg.min_score_threshold
            max_new = cfg.max_links_per_note - len(existing_targets)
            if max_new <= 0:
                return ServiceResult(
                    ok=True,
                    op=op,
                    data={
                        "target_id": target_id,
                        "suggestions": [],
                        "count": 0,
                    },
                    warnings=["Node already at max_links_per_note"],
                )

            suggestions = [s for s in scored if s["score"] >= threshold]
            suggestions.sort(key=lambda s: s["score"], reverse=True)
            suggestions = suggestions[:max_new]

        # -- PRESENT (dry_run) / CONNECT --
        if dry_run:
            return ServiceResult(
                ok=True,
                op=op,
                data={
                    "target_id": target_id,
                    "suggestions": suggestions,
                    "count": len(suggestions),
                    "dry_run": True,
                },
            )

        # CONNECT — modify files and DB
        connected = self._connect(target_id, suggestions)
        return ServiceResult(
            ok=True,
            op=op,
            data={
                "target_id": target_id,
                "connected": connected,
                "count": len(connected),
            },
        )

    def prune(
        self,
        *,
        content_id: str | None = None,
        dry_run: bool = False,
    ) -> ServiceResult:
        """Remove stale links that score below threshold."""
        op = "prune"
        cfg = self._vault.settings.reweave

        with self._vault.engine.connect() as conn:
            target = self._discover_target(conn, content_id)
            if target is None:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"No target found for prune (id={content_id})",
                    ),
                )

            target_id = str(target.id)
            target_title = str(target.title)
            target_tags = self._get_node_tags(conn, target_id)
            target_topic = target.topic

            # Get existing outgoing edges
            existing_edges = conn.execute(
                select(edges.c.target_id, edges.c.edge_type).where(edges.c.source_id == target_id)
            ).fetchall()

            if not existing_edges:
                return ServiceResult(
                    ok=True,
                    op=op,
                    data={"target_id": target_id, "pruned": [], "count": 0},
                )

            # Score existing links
            linked_ids = [str(e.target_id) for e in existing_edges]
            linked_candidates = self._build_candidate_list(conn, linked_ids)

            scored = self._score_candidates(
                conn,
                target_id=target_id,
                target_title=target_title,
                target_tags=target_tags,
                target_topic=target_topic,
                candidates=linked_candidates,
                cfg=cfg,
            )

            # Find stale links (below threshold)
            stale = [s for s in scored if s["score"] < cfg.min_score_threshold]

        if dry_run:
            return ServiceResult(
                ok=True,
                op=op,
                data={
                    "target_id": target_id,
                    "stale": stale,
                    "count": len(stale),
                    "dry_run": True,
                },
            )

        # Remove stale links
        pruned = self._prune_links(target_id, stale)
        return ServiceResult(
            ok=True,
            op=op,
            data={
                "target_id": target_id,
                "pruned": pruned,
                "count": len(pruned),
            },
        )

    def undo(self, *, reweave_id: int | None = None) -> ServiceResult:
        """Reverse a reweave operation via audit trail."""
        op = "undo"

        with self._vault.engine.connect() as conn:
            if reweave_id is not None:
                # Undo a specific log entry
                log_row = conn.execute(
                    select(reweave_log).where(
                        reweave_log.c.id == reweave_id,
                        reweave_log.c.undone == 0,
                    )
                ).first()
                if log_row is None:
                    return ServiceResult(
                        ok=False,
                        op=op,
                        error=ServiceError(
                            code="NOT_FOUND",
                            message=f"No undoable reweave log entry with id={reweave_id}",
                        ),
                    )
                entries = [log_row]
            else:
                # Undo most recent un-undone batch (same timestamp)
                latest = conn.execute(
                    select(reweave_log.c.timestamp)
                    .where(reweave_log.c.undone == 0)
                    .order_by(reweave_log.c.id.desc())
                    .limit(1)
                ).first()
                if latest is None:
                    return ServiceResult(
                        ok=False,
                        op=op,
                        error=ServiceError(
                            code="NO_HISTORY",
                            message="No reweave operations to undo",
                        ),
                    )
                entries = list(
                    conn.execute(
                        select(reweave_log).where(
                            reweave_log.c.timestamp == latest.timestamp,
                            reweave_log.c.undone == 0,
                        )
                    ).fetchall()
                )

        # Apply undo operations
        undone = self._apply_undo(entries)
        return ServiceResult(
            ok=True,
            op=op,
            data={
                "undone": undone,
                "count": len(undone),
            },
        )

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    @staticmethod
    def _discover_target(conn: Connection, content_id: str | None) -> Any:
        """Find the target node for reweave/prune.

        If content_id is provided, look it up directly.
        Otherwise, find the most recently modified non-archived node.
        """
        if content_id is not None:
            return conn.execute(
                select(nodes).where(nodes.c.id == content_id, nodes.c.archived == 0)
            ).first()

        return conn.execute(
            select(nodes).where(nodes.c.archived == 0).order_by(nodes.c.modified.desc()).limit(1)
        ).first()

    @staticmethod
    def _get_existing_targets(conn: Connection, source_id: str) -> set[str]:
        """Get IDs of nodes already linked from source."""
        rows = conn.execute(
            select(edges.c.target_id).where(edges.c.source_id == source_id)
        ).fetchall()
        return {str(r.target_id) for r in rows}

    @staticmethod
    def _get_candidates(
        conn: Connection,
        target_id: str,
        existing_targets: set[str],
    ) -> list[Any]:
        """Get candidate nodes (non-archived, not self, not already linked)."""
        rows = conn.execute(
            select(nodes).where(nodes.c.archived == 0, nodes.c.id != target_id)
        ).fetchall()
        return [r for r in rows if str(r.id) not in existing_targets]

    @staticmethod
    def _build_candidate_list(conn: Connection, node_ids: list[str]) -> list[Any]:
        """Build candidate list from specific node IDs."""
        if not node_ids:
            return []
        return list(conn.execute(select(nodes).where(nodes.c.id.in_(node_ids))).fetchall())

    @staticmethod
    def _get_node_tags(conn: Connection, node_id: str) -> set[str]:
        """Get tags for a node."""
        rows = conn.execute(
            select(node_tags.c.tag).where(node_tags.c.node_id == node_id)
        ).fetchall()
        return {str(r.tag) for r in rows}

    # ------------------------------------------------------------------
    # Scoring — four signals
    # ------------------------------------------------------------------

    def _score_candidates(
        self,
        conn: Connection,
        *,
        target_id: str,
        target_title: str,
        target_tags: set[str],
        target_topic: str | None,
        candidates: list[Any],
        cfg: Any,
    ) -> list[dict[str, Any]]:
        """Score all candidates using the 4-signal weighted sum."""
        # Signal 1: Lexical (BM25 percentile)
        bm25_scores = self._score_bm25(conn, target_title, candidates)

        # Signal 3: Graph proximity (needs the full graph)
        g = self._vault.graph.graph
        proximity_scores = self._score_graph_proximity(g, target_id, candidates)

        scored: list[dict[str, Any]] = []
        for cand in candidates:
            cand_id = str(cand.id)

            # S1: Lexical
            s1 = bm25_scores.get(cand_id, 0.0)

            # S2: Tag overlap (Jaccard)
            cand_tags = self._get_node_tags(conn, cand_id)
            s2 = _jaccard(target_tags, cand_tags)

            # S3: Graph proximity
            s3 = proximity_scores.get(cand_id, 0.0)

            # S4: Topic co-occurrence
            s4 = 1.0 if (target_topic and cand.topic and target_topic == cand.topic) else 0.0

            composite = (
                cfg.lexical_weight * s1
                + cfg.tag_weight * s2
                + cfg.graph_weight * s3
                + cfg.topic_weight * s4
            )

            scored.append(
                {
                    "id": cand_id,
                    "title": str(cand.title),
                    "score": round(composite, 4),
                    "signals": {
                        "lexical": round(s1, 4),
                        "tag_overlap": round(s2, 4),
                        "graph_proximity": round(s3, 4),
                        "topic": round(s4, 4),
                    },
                }
            )

        return scored

    @staticmethod
    def _score_bm25(
        conn: Connection,
        target_title: str,
        candidates: list[Any],
    ) -> dict[str, float]:
        """Compute BM25 percentile scores using FTS5.

        Uses the target's title as the query. Each word is quoted to prevent
        FTS5 operator interpretation. Scores are percentile-normalized so
        the top match = 1.0.
        """
        # Sanitize title words for FTS5 query
        words = target_title.split()
        if not words:
            return {}

        # Quote each word and join with OR for broader matching
        quoted = [f'"{w}"' for w in words if w.strip()]
        if not quoted:
            return {}
        fts_query = " OR ".join(quoted)

        candidate_ids = {str(c.id) for c in candidates}

        try:
            rows = conn.execute(
                text(
                    "SELECT fts.id, bm25(nodes_fts) AS score "
                    "FROM nodes_fts AS fts "
                    "WHERE nodes_fts MATCH :query"
                ),
                {"query": fts_query},
            ).fetchall()
        except Exception:
            # FTS5 query failure (e.g., special characters)
            return {}

        # Filter to candidates only, collect raw scores
        raw_scores: dict[str, float] = {}
        for row in rows:
            rid = str(row.id)
            if rid in candidate_ids:
                raw_scores[rid] = float(row.score)

        if not raw_scores:
            return {}

        # BM25 returns negative scores (more negative = more relevant)
        # Percentile normalize: abs(raw) / abs(max_raw) -> top = 1.0
        max_abs = max(abs(s) for s in raw_scores.values())
        if max_abs == 0:
            return {}

        return {rid: abs(score) / max_abs for rid, score in raw_scores.items()}

    @staticmethod
    def _score_graph_proximity(
        g: Any,
        target_id: str,
        candidates: list[Any],
    ) -> dict[str, float]:
        """Compute graph proximity: 1 / shortest_path_length (undirected).

        Returns 0.0 if no path exists or target not in graph.
        """
        if target_id not in g:
            return {}

        ug = g.to_undirected(as_view=True)
        scores: dict[str, float] = {}

        for cand in candidates:
            cand_id = str(cand.id)
            if cand_id not in g:
                scores[cand_id] = 0.0
                continue
            try:
                length = nx.shortest_path_length(ug, target_id, cand_id)
                scores[cand_id] = 1.0 / length if length > 0 else 0.0
            except nx.NetworkXNoPath:
                scores[cand_id] = 0.0

        return scores

    # ------------------------------------------------------------------
    # Connect — apply suggestions
    # ------------------------------------------------------------------

    def _connect(
        self,
        target_id: str,
        suggestions: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply link suggestions: update frontmatter, insert edges, log."""
        today = today_iso()
        timestamp = now_iso()
        connected: list[dict[str, Any]] = []

        with self._vault.transaction() as txn:
            # Read current file
            node_row = txn.conn.execute(
                select(nodes.c.path, nodes.c.maturity).where(nodes.c.id == target_id)
            ).first()
            if node_row is None:
                return []

            file_path = self._vault.root / node_row.path
            fm, body = txn.read_content(file_path)

            # Initialize links dict if not present
            fm_links = fm.get("links", {})
            if not isinstance(fm_links, dict):
                fm_links = {}

            relates_list = list(fm_links.get("relates", []))

            for suggestion in suggestions:
                sugg_id = suggestion["id"]
                sugg_title = suggestion["title"]

                # Add to frontmatter links
                if sugg_id not in relates_list:
                    relates_list.append(sugg_id)

                # Add body wikilink if not a garden note
                if node_row.maturity is None:
                    wikilink = f"[[{sugg_title}]]"
                    if wikilink not in body:
                        if body.strip():
                            body = body.rstrip() + f"\n\n{wikilink}"
                        else:
                            body = wikilink

                # Insert edge
                existing = txn.conn.execute(
                    select(edges.c.source_id).where(
                        edges.c.source_id == target_id,
                        edges.c.target_id == sugg_id,
                        edges.c.edge_type == "relates",
                    )
                ).first()
                if existing is None:
                    txn.conn.execute(
                        insert(edges).values(
                            source_id=target_id,
                            target_id=sugg_id,
                            edge_type="relates",
                            source_layer="frontmatter",
                            weight=1.0,
                            created=today,
                        )
                    )

                # Log entry
                txn.conn.execute(
                    insert(reweave_log).values(
                        source_id=target_id,
                        target_id=sugg_id,
                        action="add",
                        direction="outgoing",
                        timestamp=timestamp,
                        undone=0,
                    )
                )

                connected.append({"id": sugg_id, "title": sugg_title})

            # Update frontmatter and write back
            fm_links["relates"] = relates_list
            fm["links"] = fm_links
            fm["modified"] = today
            txn.write_content(file_path, fm, body)

            # Update FTS5 if body changed
            txn.conn.execute(
                text("DELETE FROM nodes_fts WHERE id = :id"),
                {"id": target_id},
            )
            txn.conn.execute(
                text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
                {"id": target_id, "title": str(fm.get("title", "")), "body": body},
            )

            # Update modified in nodes
            txn.conn.execute(nodes.update().where(nodes.c.id == target_id).values(modified=today))

        return connected

    # ------------------------------------------------------------------
    # Prune — remove stale links
    # ------------------------------------------------------------------

    def _prune_links(
        self,
        source_id: str,
        stale: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Remove stale links from frontmatter, DB, and body."""
        today = today_iso()
        timestamp = now_iso()
        pruned: list[dict[str, Any]] = []

        with self._vault.transaction() as txn:
            node_row = txn.conn.execute(
                select(nodes.c.path, nodes.c.maturity).where(nodes.c.id == source_id)
            ).first()
            if node_row is None:
                return []

            file_path = self._vault.root / node_row.path
            fm, body = txn.read_content(file_path)

            fm_links = fm.get("links", {})
            if not isinstance(fm_links, dict):
                fm_links = {}

            relates_list = list(fm_links.get("relates", []))

            for entry in stale:
                stale_id = entry["id"]
                stale_title = entry["title"]

                # Remove from frontmatter links
                if stale_id in relates_list:
                    relates_list.remove(stale_id)

                # Remove body wikilink
                body = body.replace(f"[[{stale_title}]]", "")

                # Remove edge from DB
                txn.conn.execute(
                    delete(edges).where(
                        edges.c.source_id == source_id,
                        edges.c.target_id == stale_id,
                        edges.c.edge_type == "relates",
                    )
                )

                # Log entry
                txn.conn.execute(
                    insert(reweave_log).values(
                        source_id=source_id,
                        target_id=stale_id,
                        action="remove",
                        direction="outgoing",
                        timestamp=timestamp,
                        undone=0,
                    )
                )

                pruned.append({"id": stale_id, "title": stale_title})

            # Update frontmatter and write back
            fm_links["relates"] = relates_list
            fm["links"] = fm_links
            fm["modified"] = today
            txn.write_content(file_path, fm, body)

            # Update FTS5
            txn.conn.execute(
                text("DELETE FROM nodes_fts WHERE id = :id"),
                {"id": source_id},
            )
            txn.conn.execute(
                text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
                {"id": source_id, "title": str(fm.get("title", "")), "body": body},
            )

            txn.conn.execute(nodes.update().where(nodes.c.id == source_id).values(modified=today))

        return pruned

    # ------------------------------------------------------------------
    # Undo — reverse reweave operations
    # ------------------------------------------------------------------

    def _apply_undo(self, entries: list[Any]) -> list[dict[str, Any]]:
        """Reverse reweave log entries."""
        today = today_iso()
        undone_results: list[dict[str, Any]] = []

        with self._vault.transaction() as txn:
            for entry in entries:
                source_id = str(entry.source_id)
                target_id = str(entry.target_id)
                action = str(entry.action)
                log_id = int(entry.id)

                if action == "add":
                    # Reverse: remove the link
                    self._undo_add(txn, source_id, target_id, today)
                elif action == "remove":
                    # Reverse: re-add the link
                    self._undo_remove(txn, source_id, target_id, today)

                # Mark log entry as undone
                txn.conn.execute(
                    reweave_log.update().where(reweave_log.c.id == log_id).values(undone=1)
                )

                undone_results.append(
                    {
                        "log_id": log_id,
                        "source_id": source_id,
                        "target_id": target_id,
                        "action": action,
                        "reversed": "remove" if action == "add" else "add",
                    }
                )

        return undone_results

    @staticmethod
    def _undo_add(txn: Any, source_id: str, target_id: str, today: str) -> None:
        """Undo an 'add' action: remove the link."""
        # Remove edge
        txn.conn.execute(
            delete(edges).where(
                edges.c.source_id == source_id,
                edges.c.target_id == target_id,
                edges.c.edge_type == "relates",
            )
        )

        # Remove from frontmatter
        from ztlctl.infrastructure.database.schema import nodes as nodes_table

        node_row = txn.conn.execute(
            select(nodes_table.c.path).where(nodes_table.c.id == source_id)
        ).first()
        if node_row is not None:
            file_path = txn._vault.root / node_row.path
            if file_path.exists():
                fm, body = txn.read_content(file_path)
                fm_links = fm.get("links", {})
                if isinstance(fm_links, dict):
                    relates = list(fm_links.get("relates", []))
                    if target_id in relates:
                        relates.remove(target_id)
                        fm_links["relates"] = relates
                        fm["links"] = fm_links
                        fm["modified"] = today
                        txn.write_content(file_path, fm, body)

    @staticmethod
    def _undo_remove(txn: Any, source_id: str, target_id: str, today: str) -> None:
        """Undo a 'remove' action: re-add the link."""
        # Re-insert edge
        existing = txn.conn.execute(
            select(edges.c.source_id).where(
                edges.c.source_id == source_id,
                edges.c.target_id == target_id,
                edges.c.edge_type == "relates",
            )
        ).first()
        if existing is None:
            txn.conn.execute(
                insert(edges).values(
                    source_id=source_id,
                    target_id=target_id,
                    edge_type="relates",
                    source_layer="frontmatter",
                    weight=1.0,
                    created=today,
                )
            )

        # Re-add to frontmatter
        from ztlctl.infrastructure.database.schema import nodes as nodes_table

        node_row = txn.conn.execute(
            select(nodes_table.c.path).where(nodes_table.c.id == source_id)
        ).first()
        if node_row is not None:
            file_path = txn._vault.root / node_row.path
            if file_path.exists():
                fm, body = txn.read_content(file_path)
                fm_links = fm.get("links", {})
                if not isinstance(fm_links, dict):
                    fm_links = {}
                relates = list(fm_links.get("relates", []))
                if target_id not in relates:
                    relates.append(target_id)
                    fm_links["relates"] = relates
                    fm["links"] = fm_links
                    fm["modified"] = today
                    txn.write_content(file_path, fm, body)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _jaccard(set_a: set[str], set_b: set[str]) -> float:
    """Jaccard similarity: |A & B| / |A | B|."""
    if not set_a and not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union if union > 0 else 0.0
