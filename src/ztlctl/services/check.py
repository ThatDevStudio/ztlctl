"""CheckService — integrity and reconciliation.

Single command following the linter pattern.
Four categories: DB-file consistency, schema integrity,
graph health, structural validation. (DESIGN.md Section 14)
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, insert, select, text

from ztlctl.domain.content import parse_frontmatter, render_frontmatter
from ztlctl.domain.ids import ID_PATTERNS
from ztlctl.infrastructure.database.schema import edges, node_tags, nodes
from ztlctl.services._helpers import now_compact, now_iso, today_iso
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import trace_span, traced

if TYPE_CHECKING:
    from sqlalchemy import Connection

    from ztlctl.infrastructure.vault import VaultTransaction


# ---------------------------------------------------------------------------
# Issue severity and category constants
# ---------------------------------------------------------------------------

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

CAT_DB_FILE = "db_file_consistency"
CAT_SCHEMA = "schema_integrity"
CAT_GRAPH = "graph_health"
CAT_STRUCTURAL = "structural_validation"
CAT_GARDEN = "garden_health"


# ---------------------------------------------------------------------------
# CheckService
# ---------------------------------------------------------------------------


class CheckService(BaseService):
    """Handles vault integrity checking and repair."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @traced
    def check(self) -> ServiceResult:
        """Report integrity issues without modifying anything."""
        issues: list[dict[str, Any]] = []
        with self._vault.engine.connect() as conn:
            with trace_span("db_file_consistency"):
                issues.extend(self._check_db_file_consistency(conn))
            with trace_span("schema_integrity"):
                issues.extend(self._check_schema_integrity(conn))
            with trace_span("graph_health"):
                issues.extend(self._check_graph_health(conn))
            with trace_span("structural_validation"):
                issues.extend(self._check_structural_validation(conn))
            with trace_span("garden_health"):
                issues.extend(self._check_garden_health(conn))

        warnings: list[str] = []
        issues_fixed = sum(1 for i in issues if i.get("fix_action") is not None)
        self._dispatch_event(
            "post_check",
            {"issues_found": len(issues), "issues_fixed": issues_fixed},
            warnings,
        )

        return ServiceResult(
            ok=True,
            op="check",
            data={"issues": issues, "count": len(issues)},
            warnings=warnings,
        )

    @traced
    def fix(self, *, level: str = "safe") -> ServiceResult:
        """Automatically repair issues. Level: 'safe' or 'aggressive'."""
        self._backup_db()
        fixes: list[str] = []
        today = today_iso()

        with self._vault.transaction() as txn:
            fixes.extend(self._fix_orphan_db_rows(txn))
            fixes.extend(self._fix_dangling_edges(txn.conn))
            fixes.extend(self._fix_missing_fts(txn))
            fixes.extend(self._fix_resync_from_files(txn.conn, today))

            if level == "aggressive":
                fixes.extend(self._fix_reindex_edges(txn, today))
                fixes.extend(self._fix_reorder_frontmatter(txn))

        return ServiceResult(
            ok=True,
            op="fix",
            data={"fixes": fixes, "count": len(fixes)},
        )

    @traced
    def rebuild(self) -> ServiceResult:
        """Full DB rebuild from filesystem (files are truth)."""
        self._backup_db()
        warnings: list[str] = []
        today = today_iso()

        with self._vault.transaction() as txn:
            # Clear derived tables (preserve id_counters and tags_registry)
            txn.clear_fts()
            txn.conn.execute(delete(node_tags))
            txn.conn.execute(delete(edges))
            txn.conn.execute(delete(nodes))

            content_files = self._vault.find_content()
            nodes_indexed = 0
            edges_created = 0
            tags_found = 0

            for file_path in content_files:
                try:
                    fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    warnings.append(f"Failed to parse {file_path}: {exc}")
                    continue

                content_id = fm.get("id")
                if not content_id:
                    warnings.append(f"File missing 'id' in frontmatter: {file_path}")
                    continue

                content_type = str(fm.get("type", "note"))
                title = str(fm.get("title", ""))
                rel_path = str(file_path.relative_to(self._vault.root))

                # Insert node
                node_row: dict[str, Any] = {
                    "id": content_id,
                    "title": title,
                    "type": content_type,
                    "subtype": fm.get("subtype"),
                    "status": str(fm.get("status", "draft")),
                    "maturity": fm.get("maturity"),
                    "path": rel_path,
                    "aliases": None,
                    "topic": fm.get("topic"),
                    "session": fm.get("session"),
                    "archived": 1 if fm.get("archived") else 0,
                    "created": str(fm.get("created", today)),
                    "modified": str(fm.get("modified", today)),
                    "created_at": str(
                        fm.get("created_at") or f"{fm.get('created', today)!s}T00:00:00+00:00"
                    ),
                    "modified_at": str(
                        fm.get("modified_at") or f"{fm.get('modified', today)!s}T00:00:00+00:00"
                    ),
                }
                # Store aliases as JSON if present
                aliases = fm.get("aliases")
                if isinstance(aliases, list):
                    import json

                    node_row["aliases"] = json.dumps(aliases)

                txn.conn.execute(insert(nodes).values(**node_row))
                nodes_indexed += 1

                # FTS5 index
                txn.upsert_fts(content_id, title, body)

                # Tags
                file_tags = fm.get("tags", [])
                if isinstance(file_tags, list):
                    tags_found += txn.index_tags(content_id, [str(t) for t in file_tags], today)

            # Second pass: index edges (all nodes must exist first)
            for file_path in content_files:
                try:
                    fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
                except Exception:
                    continue

                content_id = fm.get("id")
                if not content_id:
                    continue

                fm_links = fm.get("links", {})
                if isinstance(fm_links, dict):
                    edges_created += txn.index_links(content_id, fm_links, body, today)

        # Materialize graph metrics after rebuild
        from ztlctl.services.graph import GraphService

        mat_result = GraphService(self._vault).materialize_metrics()
        if mat_result.ok:
            nodes_materialized = mat_result.data.get("nodes_updated", 0)
        else:
            nodes_materialized = 0
            warnings.append("Graph metric materialization failed after rebuild")

        return ServiceResult(
            ok=True,
            op="rebuild",
            data={
                "nodes_indexed": nodes_indexed,
                "edges_created": edges_created,
                "tags_found": tags_found,
                "nodes_materialized": nodes_materialized,
            },
            warnings=warnings,
        )

    @traced
    def rollback(self) -> ServiceResult:
        """Restore DB from latest backup."""
        backup_dir = self._vault.root / ".ztlctl" / "backups"
        if not backup_dir.exists():
            return ServiceResult(
                ok=False,
                op="rollback",
                error=ServiceError(
                    code="NO_BACKUPS",
                    message="No backup directory found",
                ),
            )

        backups = sorted(backup_dir.glob("ztlctl-*.db"))
        if not backups:
            return ServiceResult(
                ok=False,
                op="rollback",
                error=ServiceError(
                    code="NO_BACKUPS",
                    message="No backup files found",
                ),
            )

        latest = backups[-1]
        db_path = self._vault.root / ".ztlctl" / "ztlctl.db"

        # Dispose the engine to release file locks before copying
        self._vault.engine.dispose()

        shutil.copy2(str(latest), str(db_path))

        return ServiceResult(
            ok=True,
            op="rollback",
            data={
                "backup_file": latest.name,
                "restored_from": str(latest),
            },
        )

    # ------------------------------------------------------------------
    # Backup helpers
    # ------------------------------------------------------------------

    def _backup_db(self) -> Path:
        """Create a timestamped backup of the database."""
        backup_dir = self._vault.root / ".ztlctl" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        db_path = self._vault.root / ".ztlctl" / "ztlctl.db"
        timestamp = now_compact()
        backup_path = backup_dir / f"ztlctl-{timestamp}.db"
        shutil.copy2(str(db_path), str(backup_path))

        self._prune_backups(backup_dir)
        return backup_path

    def _prune_backups(self, backup_dir: Path) -> None:
        """Remove old backups exceeding retention settings."""
        config = self._vault.settings.check
        backups = sorted(backup_dir.glob("ztlctl-*.db"))

        # Enforce max count (keep newest)
        if len(backups) > config.backup_max_count:
            for old in backups[: len(backups) - config.backup_max_count]:
                old.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Check categories (read-only)
    # ------------------------------------------------------------------

    def _check_db_file_consistency(self, conn: Connection) -> list[dict[str, Any]]:
        """Category 1: DB rows vs. files on disk."""
        issues: list[dict[str, Any]] = []

        # For each DB node, verify the file exists
        all_nodes = conn.execute(
            select(nodes.c.id, nodes.c.path, nodes.c.title, nodes.c.type, nodes.c.status)
        ).fetchall()

        db_paths: set[str] = set()
        for row in all_nodes:
            db_paths.add(row.path)
            file_path = self._vault.root / row.path
            if not file_path.exists():
                issues.append(
                    {
                        "category": CAT_DB_FILE,
                        "severity": SEVERITY_ERROR,
                        "node_id": row.id,
                        "message": f"DB row exists but file missing: {row.path}",
                        "fix_action": "remove_orphan_db_row",
                    }
                )
                continue

            # Verify frontmatter matches DB
            try:
                fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8"))
            except Exception:
                issues.append(
                    {
                        "category": CAT_DB_FILE,
                        "severity": SEVERITY_ERROR,
                        "node_id": row.id,
                        "message": f"Cannot parse frontmatter: {row.path}",
                        "fix_action": "resync_from_file",
                    }
                )
                continue

            # Compare key fields
            fm_id = fm.get("id", "")
            if str(fm_id) != str(row.id):
                issues.append(
                    {
                        "category": CAT_DB_FILE,
                        "severity": SEVERITY_ERROR,
                        "node_id": row.id,
                        "message": f"ID mismatch: DB={row.id}, file={fm_id}",
                        "fix_action": "resync_from_file",
                    }
                )

            fm_title = fm.get("title", "")
            if str(fm_title) != str(row.title):
                issues.append(
                    {
                        "category": CAT_DB_FILE,
                        "severity": SEVERITY_WARNING,
                        "node_id": row.id,
                        "message": (f"Title mismatch: DB='{row.title}', file='{fm_title}'"),
                        "fix_action": "resync_from_file",
                    }
                )

            fm_status = fm.get("status", "")
            if str(fm_status) != str(row.status):
                issues.append(
                    {
                        "category": CAT_DB_FILE,
                        "severity": SEVERITY_WARNING,
                        "node_id": row.id,
                        "message": (f"Status mismatch: DB='{row.status}', file='{fm_status}'"),
                        "fix_action": "resync_from_file",
                    }
                )

        # For each content file on disk, verify it has a DB row
        content_files = self._vault.find_content()
        for file_path in content_files:
            rel_path = str(file_path.relative_to(self._vault.root))
            if rel_path not in db_paths:
                issues.append(
                    {
                        "category": CAT_DB_FILE,
                        "severity": SEVERITY_ERROR,
                        "node_id": None,
                        "message": f"File exists but no DB row: {rel_path}",
                        "fix_action": "index_orphan_file",
                    }
                )

        return issues

    def _check_schema_integrity(self, conn: Connection) -> list[dict[str, Any]]:
        """Category 2: referential integrity and FTS5 sync."""
        issues: list[dict[str, Any]] = []
        node_ids = {row.id for row in conn.execute(select(nodes.c.id)).fetchall()}

        # Edges referencing nonexistent nodes
        all_edges = conn.execute(
            select(edges.c.source_id, edges.c.target_id, edges.c.edge_type)
        ).fetchall()
        for edge in all_edges:
            if edge.source_id not in node_ids:
                issues.append(
                    {
                        "category": CAT_SCHEMA,
                        "severity": SEVERITY_ERROR,
                        "node_id": edge.source_id,
                        "message": (
                            f"Edge source '{edge.source_id}' not in nodes "
                            f"(target: {edge.target_id}, type: {edge.edge_type})"
                        ),
                        "fix_action": "remove_dangling_edge",
                    }
                )
            if edge.target_id not in node_ids:
                issues.append(
                    {
                        "category": CAT_SCHEMA,
                        "severity": SEVERITY_ERROR,
                        "node_id": edge.target_id,
                        "message": (
                            f"Edge target '{edge.target_id}' not in nodes "
                            f"(source: {edge.source_id}, type: {edge.edge_type})"
                        ),
                        "fix_action": "remove_dangling_edge",
                    }
                )

        # node_tags referencing nonexistent nodes
        all_nt = conn.execute(select(node_tags.c.node_id, node_tags.c.tag)).fetchall()
        for nt in all_nt:
            if nt.node_id not in node_ids:
                issues.append(
                    {
                        "category": CAT_SCHEMA,
                        "severity": SEVERITY_ERROR,
                        "node_id": nt.node_id,
                        "message": (f"node_tags entry for '{nt.node_id}' but node does not exist"),
                        "fix_action": "remove_orphan_tag",
                    }
                )

        # FTS5 sync: every node should have an FTS row
        fts_ids = {row[0] for row in conn.execute(text("SELECT id FROM nodes_fts")).fetchall()}
        for nid in node_ids:
            if nid not in fts_ids:
                issues.append(
                    {
                        "category": CAT_SCHEMA,
                        "severity": SEVERITY_ERROR,
                        "node_id": nid,
                        "message": f"Node '{nid}' missing from FTS5 index",
                        "fix_action": "reinsert_fts",
                    }
                )

        return issues

    def _check_graph_health(self, conn: Connection) -> list[dict[str, Any]]:
        """Category 3: graph-level issues."""
        issues: list[dict[str, Any]] = []

        # Self-referencing edges
        self_edges = conn.execute(
            select(edges.c.source_id, edges.c.edge_type).where(
                edges.c.source_id == edges.c.target_id
            )
        ).fetchall()
        for se in self_edges:
            issues.append(
                {
                    "category": CAT_GRAPH,
                    "severity": SEVERITY_ERROR,
                    "node_id": se.source_id,
                    "message": (
                        f"Self-referencing edge: {se.source_id} -> {se.source_id} ({se.edge_type})"
                    ),
                    "fix_action": "remove_self_edge",
                }
            )

        # Isolated nodes (0 in-degree and 0 out-degree)
        node_ids = {row.id for row in conn.execute(select(nodes.c.id)).fetchall()}
        edge_participants: set[str] = set()
        all_edges = conn.execute(select(edges.c.source_id, edges.c.target_id)).fetchall()
        for e in all_edges:
            edge_participants.add(e.source_id)
            edge_participants.add(e.target_id)

        for nid in node_ids:
            if nid not in edge_participants:
                issues.append(
                    {
                        "category": CAT_GRAPH,
                        "severity": SEVERITY_WARNING,
                        "node_id": nid,
                        "message": f"Isolated node with zero connections: {nid}",
                        "fix_action": "reweave_candidate",
                    }
                )

        return issues

    def _check_structural_validation(self, conn: Connection) -> list[dict[str, Any]]:
        """Category 4: ID format, status validity, tag format."""
        issues: list[dict[str, Any]] = []

        all_nodes = conn.execute(select(nodes.c.id, nodes.c.type, nodes.c.status)).fetchall()

        # Collect valid statuses per type from lifecycle
        from ztlctl.domain.lifecycle import (
            DECISION_TRANSITIONS,
            LOG_TRANSITIONS,
            NOTE_TRANSITIONS,
            REFERENCE_TRANSITIONS,
            TASK_TRANSITIONS,
        )

        status_map: dict[str, set[str]] = {
            "note": set(NOTE_TRANSITIONS.keys()),
            "reference": set(REFERENCE_TRANSITIONS.keys()),
            "log": set(LOG_TRANSITIONS.keys()),
            "task": set(TASK_TRANSITIONS.keys()),
        }
        # Decision is a subtype of note — add decision statuses to note
        decision_statuses = set(DECISION_TRANSITIONS.keys())

        for row in all_nodes:
            # ID pattern check
            pattern = ID_PATTERNS.get(row.type)
            if pattern is not None and not pattern.match(row.id):
                issues.append(
                    {
                        "category": CAT_STRUCTURAL,
                        "severity": SEVERITY_ERROR,
                        "node_id": row.id,
                        "message": (
                            f"ID '{row.id}' does not match expected pattern for type '{row.type}'"
                        ),
                        "fix_action": None,
                    }
                )

            # Status validity
            valid_statuses = status_map.get(row.type, set())
            # Include decision statuses for notes (could be decision subtype)
            if row.type == "note":
                valid_statuses = valid_statuses | decision_statuses
            if valid_statuses and row.status not in valid_statuses:
                issues.append(
                    {
                        "category": CAT_STRUCTURAL,
                        "severity": SEVERITY_ERROR,
                        "node_id": row.id,
                        "message": (f"Invalid status '{row.status}' for type '{row.type}'"),
                        "fix_action": None,
                    }
                )

        # Tag format warnings
        all_tags = conn.execute(select(node_tags.c.node_id, node_tags.c.tag)).fetchall()
        for nt in all_tags:
            if "/" not in nt.tag:
                issues.append(
                    {
                        "category": CAT_STRUCTURAL,
                        "severity": SEVERITY_WARNING,
                        "node_id": nt.node_id,
                        "message": (
                            f"Tag '{nt.tag}' missing domain/scope format (e.g. 'domain/scope')"
                        ),
                        "fix_action": None,
                    }
                )

        return issues

    def _check_garden_health(self, conn: Connection) -> list[dict[str, Any]]:
        """Category 5: garden advisory — aging seeds and evergreen readiness."""
        from datetime import UTC, datetime, timedelta

        issues: list[dict[str, Any]] = []
        garden = self._vault.settings.garden

        # --- Aging seeds ---
        cutoff = (datetime.now(UTC) - timedelta(days=garden.seed_age_warning_days)).strftime(
            "%Y-%m-%d"
        )
        aging_seeds = conn.execute(
            select(nodes.c.id, nodes.c.title, nodes.c.created).where(
                nodes.c.maturity == "seed",
                nodes.c.type == "note",
                nodes.c.archived == 0,
                nodes.c.created < cutoff,
            )
        ).fetchall()
        for row in aging_seeds:
            issues.append(
                {
                    "category": CAT_GARDEN,
                    "severity": SEVERITY_WARNING,
                    "node_id": row.id,
                    "message": (
                        f"Aging seed: '{row.title}' created {row.created}, "
                        f"older than {garden.seed_age_warning_days} days"
                    ),
                    "fix_action": None,
                }
            )

        # --- Evergreen readiness ---
        min_bidir = garden.evergreen_min_bidirectional_links
        min_kp = garden.evergreen_min_key_points
        candidates = conn.execute(
            select(nodes.c.id, nodes.c.title, nodes.c.path).where(
                nodes.c.maturity.in_(["seed", "budding"]),
                nodes.c.type == "note",
                nodes.c.archived == 0,
            )
        ).fetchall()
        for row in candidates:
            # Count bidirectional links for this node
            bidir_count = (
                conn.execute(
                    text(
                        "SELECT COUNT(*) FROM edges e1"
                        " WHERE e1.source_id = :nid"
                        "   AND EXISTS ("
                        "     SELECT 1 FROM edges e2"
                        "     WHERE e2.source_id = e1.target_id"
                        "       AND e2.target_id = e1.source_id"
                        "   )"
                    ),
                    {"nid": row.id},
                ).scalar()
                or 0
            )
            if bidir_count < min_bidir:
                continue

            # Check key_points count from frontmatter
            file_path = self._vault.root / row.path
            if not file_path.exists():
                continue
            try:
                fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue
            key_points = fm.get("key_points", [])
            if not isinstance(key_points, list) or len(key_points) < min_kp:
                continue

            issues.append(
                {
                    "category": CAT_GARDEN,
                    "severity": SEVERITY_WARNING,
                    "node_id": row.id,
                    "message": (
                        f"Evergreen candidate: '{row.title}' has "
                        f"{bidir_count} bidirectional links and "
                        f"{len(key_points)} key points — "
                        f"consider promoting to evergreen"
                    ),
                    "fix_action": None,
                }
            )

        return issues

    # ------------------------------------------------------------------
    # Fix helpers
    # ------------------------------------------------------------------

    def _fix_orphan_db_rows(self, txn: VaultTransaction) -> list[str]:
        """Remove DB rows whose files no longer exist."""
        fixes: list[str] = []
        all_nodes = txn.conn.execute(select(nodes.c.id, nodes.c.path)).fetchall()

        for row in all_nodes:
            file_path = self._vault.root / row.path
            if not file_path.exists():
                txn.conn.execute(delete(node_tags).where(node_tags.c.node_id == row.id))
                txn.conn.execute(
                    delete(edges).where(
                        (edges.c.source_id == row.id) | (edges.c.target_id == row.id)
                    )
                )
                txn.delete_fts(row.id)
                txn.conn.execute(delete(nodes).where(nodes.c.id == row.id))
                fixes.append(f"Removed orphan DB row: {row.id}")

        return fixes

    def _fix_dangling_edges(self, conn: Connection) -> list[str]:
        """Remove edges referencing nonexistent nodes."""
        fixes: list[str] = []
        node_ids = {row.id for row in conn.execute(select(nodes.c.id)).fetchall()}

        all_edges = conn.execute(
            select(edges.c.source_id, edges.c.target_id, edges.c.edge_type)
        ).fetchall()
        for edge in all_edges:
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                conn.execute(
                    delete(edges).where(
                        edges.c.source_id == edge.source_id,
                        edges.c.target_id == edge.target_id,
                        edges.c.edge_type == edge.edge_type,
                    )
                )
                fixes.append(
                    f"Removed dangling edge: {edge.source_id} -> "
                    f"{edge.target_id} ({edge.edge_type})"
                )

        return fixes

    def _fix_missing_fts(self, txn: VaultTransaction) -> list[str]:
        """Re-insert missing FTS5 rows."""
        fixes: list[str] = []
        node_ids = {row.id for row in txn.conn.execute(select(nodes.c.id)).fetchall()}
        fts_ids = {row[0] for row in txn.conn.execute(text("SELECT id FROM nodes_fts")).fetchall()}

        for nid in node_ids:
            if nid not in fts_ids:
                # Read from file
                row = txn.conn.execute(
                    select(nodes.c.path, nodes.c.title).where(nodes.c.id == nid)
                ).first()
                if row is None:
                    continue
                file_path = self._vault.root / row.path
                if not file_path.exists():
                    continue
                _, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
                txn.upsert_fts(nid, row.title, body)
                fixes.append(f"Re-inserted FTS5 row for: {nid}")

        return fixes

    def _fix_resync_from_files(self, conn: Connection, today: str) -> list[str]:
        """Re-sync DB rows from file frontmatter (files are truth)."""
        fixes: list[str] = []
        all_nodes = conn.execute(
            select(
                nodes.c.id,
                nodes.c.path,
                nodes.c.title,
                nodes.c.type,
                nodes.c.status,
            )
        ).fetchall()

        for row in all_nodes:
            file_path = self._vault.root / row.path
            if not file_path.exists():
                continue

            try:
                fm, _ = parse_frontmatter(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            updates: dict[str, Any] = {}
            fm_title = str(fm.get("title", ""))
            fm_status = str(fm.get("status", ""))

            if fm_title and fm_title != str(row.title):
                updates["title"] = fm_title
            if fm_status and fm_status != str(row.status):
                updates["status"] = fm_status

            if updates:
                updates["modified"] = today
                updates["modified_at"] = now_iso()
                conn.execute(nodes.update().where(nodes.c.id == row.id).values(**updates))
                fixes.append(f"Re-synced DB from file for {row.id}: {list(updates.keys())}")

        return fixes

    def _fix_reindex_edges(self, txn: VaultTransaction, today: str) -> list[str]:
        """Aggressive: re-index all edges from files."""
        fixes: list[str] = []

        # Clear all edges and rebuild
        txn.conn.execute(delete(edges))
        fixes.append("Cleared all edges for re-indexing")

        all_nodes = txn.conn.execute(select(nodes.c.id, nodes.c.path)).fetchall()

        for row in all_nodes:
            file_path = self._vault.root / row.path
            if not file_path.exists():
                continue

            try:
                fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            fm_links = fm.get("links", {})
            if isinstance(fm_links, dict):
                txn.index_links(row.id, fm_links, body, today)

        fixes.append("Re-indexed all edges from files")
        return fixes

    def _fix_reorder_frontmatter(self, txn: VaultTransaction) -> list[str]:
        """Aggressive: re-order frontmatter keys in canonical order on disk.

        Uses ``txn.write_file()`` so writes are tracked for rollback.
        ``render_frontmatter()`` applies ``order_frontmatter()`` internally.
        """
        fixes: list[str] = []
        content_files = self._vault.find_content()

        for file_path in content_files:
            try:
                fm, body = parse_frontmatter(file_path.read_text(encoding="utf-8"))
            except Exception:
                continue

            if not fm:
                continue

            rendered = render_frontmatter(fm, body)
            txn.write_file(file_path, rendered)
            fixes.append(f"Re-ordered frontmatter: {file_path.name}")

        return fixes
