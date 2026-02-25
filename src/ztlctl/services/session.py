"""SessionService — session lifecycle and context management.

Sessions are first-class organizational containers. Every content
item links to its creation session. (DESIGN.md Section 2, 8)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import insert, select, text

from ztlctl.infrastructure.database.counters import next_sequential_id
from ztlctl.infrastructure.database.schema import edges, nodes
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult

if TYPE_CHECKING:
    pass


def _today() -> str:
    """ISO date string for today (UTC)."""
    return datetime.now(UTC).date().isoformat()


def _now_iso() -> str:
    """ISO timestamp for log entries."""
    return datetime.now(UTC).isoformat()


class SessionService(BaseService):
    """Handles session lifecycle and agent context."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, topic: str) -> ServiceResult:
        """Start a new session, returning the LOG-NNNN id."""
        op = "session_start"
        today = _today()

        with self._vault.transaction() as txn:
            session_id = next_sequential_id(txn.conn, "LOG-")

            # Create JSONL file with initial entry
            path = txn.resolve_path("log", session_id)
            initial_entry = json.dumps(
                {
                    "type": "session_start",
                    "session_id": session_id,
                    "topic": topic,
                    "timestamp": _now_iso(),
                },
                separators=(",", ":"),
            )
            txn.write_file(path, initial_entry + "\n")

            # Insert nodes row
            rel_path = str(path.relative_to(self._vault.root))
            txn.conn.execute(
                insert(nodes).values(
                    id=session_id,
                    title=f"Session: {topic}",
                    type="log",
                    status="open",
                    path=rel_path,
                    topic=topic,
                    created=today,
                    modified=today,
                )
            )

            # FTS5 entry
            txn.conn.execute(
                text("INSERT INTO nodes_fts(id, title, body) VALUES (:id, :title, :body)"),
                {"id": session_id, "title": f"Session: {topic}", "body": topic},
            )

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "id": session_id,
                "topic": topic,
                "path": rel_path,
                "status": "open",
            },
        )

    def close(self, *, summary: str | None = None) -> ServiceResult:
        """Close the active session with enrichment pipeline.

        Pipeline: LOG CLOSE -> CROSS-SESSION REWEAVE -> ORPHAN SWEEP -> INTEGRITY CHECK -> REPORT
        """
        op = "session_close"
        today = _today()
        warnings: list[str] = []
        cfg = self._vault.settings.session

        # Find the active (most recent open) session
        with self._vault.engine.connect() as conn:
            active = conn.execute(
                select(nodes)
                .where(nodes.c.type == "log", nodes.c.status == "open")
                .order_by(nodes.c.created.desc())
                .limit(1)
            ).first()

        if active is None:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="NO_ACTIVE_SESSION",
                    message="No active session to close",
                ),
            )

        session_id = str(active.id)

        # -- LOG CLOSE --
        with self._vault.transaction() as txn:
            # Update status to closed
            txn.conn.execute(
                nodes.update()
                .where(nodes.c.id == session_id)
                .values(status="closed", modified=today)
            )

            # Append close entry to JSONL
            file_path = self._vault.root / active.path
            close_entry = json.dumps(
                {
                    "type": "session_close",
                    "session_id": session_id,
                    "summary": summary or "",
                    "timestamp": _now_iso(),
                },
                separators=(",", ":"),
            )
            existing = txn.read_file(file_path)
            txn.write_file(file_path, existing + close_entry + "\n")

        # -- CROSS-SESSION REWEAVE --
        reweave_count = 0
        if cfg.close_reweave:
            reweave_count = self._cross_session_reweave(session_id, warnings)

        # -- ORPHAN SWEEP --
        orphan_count = 0
        if cfg.close_orphan_sweep:
            orphan_count = self._orphan_sweep(warnings)

        # -- INTEGRITY CHECK --
        integrity_issues = 0
        if cfg.close_integrity_check:
            integrity_issues = self._integrity_check(warnings)

        # -- REPORT --
        return ServiceResult(
            ok=True,
            op=op,
            data={
                "session_id": session_id,
                "status": "closed",
                "reweave_count": reweave_count,
                "orphan_count": orphan_count,
                "integrity_issues": integrity_issues,
            },
            warnings=warnings,
        )

    def reopen(self, session_id: str) -> ServiceResult:
        """Reopen a previously closed session."""
        op = "session_reopen"
        today = _today()

        with self._vault.engine.connect() as conn:
            session = conn.execute(
                select(nodes).where(nodes.c.id == session_id, nodes.c.type == "log")
            ).first()

        if session is None:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"No session found with ID: {session_id}",
                ),
            )

        if session.status == "open":
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="ALREADY_OPEN",
                    message=f"Session {session_id} is already open",
                ),
            )

        with self._vault.transaction() as txn:
            txn.conn.execute(
                nodes.update().where(nodes.c.id == session_id).values(status="open", modified=today)
            )

            # Append reopen entry to JSONL
            file_path = self._vault.root / session.path
            reopen_entry = json.dumps(
                {
                    "type": "session_reopen",
                    "session_id": session_id,
                    "timestamp": _now_iso(),
                },
                separators=(",", ":"),
            )
            existing = txn.read_file(file_path)
            txn.write_file(file_path, existing + reopen_entry + "\n")

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "id": session_id,
                "status": "open",
            },
        )

    def log_entry(
        self,
        message: str,
        *,
        pin: bool = False,
        cost: int = 0,
    ) -> ServiceResult:
        """Append a log entry to the active session."""
        raise NotImplementedError

    def cost(self, *, report: int | None = None) -> ServiceResult:
        """Query or report accumulated token cost for the session."""
        raise NotImplementedError

    def context(
        self,
        *,
        topic: str | None = None,
        budget: int = 8000,
    ) -> ServiceResult:
        """Build token-budgeted agent context payload."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Close pipeline helpers
    # ------------------------------------------------------------------

    def _cross_session_reweave(self, session_id: str, warnings: list[str]) -> int:
        """Reweave all notes created in this session."""
        from ztlctl.services.reweave import ReweaveService

        count = 0
        with self._vault.engine.connect() as conn:
            session_notes = conn.execute(
                select(nodes.c.id).where(
                    nodes.c.session == session_id,
                    nodes.c.type.in_(["note", "reference"]),
                    nodes.c.archived == 0,
                )
            ).fetchall()

        svc = ReweaveService(self._vault)
        for row in session_notes:
            result = svc.reweave(content_id=str(row.id))
            if result.ok:
                count += result.data.get("count", 0)
            else:
                msg = result.error.message if result.error else "unknown"
                warnings.append(f"Reweave failed for {row.id}: {msg}")

        return count

    def _orphan_sweep(self, warnings: list[str]) -> int:
        """Reweave orphan notes (0 outgoing edges) at lower threshold."""
        from ztlctl.services.reweave import ReweaveService

        count = 0
        with self._vault.engine.connect() as conn:
            # Find notes with 0 outgoing edges
            all_notes = conn.execute(
                select(nodes.c.id).where(
                    nodes.c.type.in_(["note", "reference"]),
                    nodes.c.archived == 0,
                )
            ).fetchall()

            orphans: list[str] = []
            for row in all_notes:
                edge_count = conn.execute(
                    select(edges.c.source_id).where(edges.c.source_id == row.id)
                ).fetchall()
                if len(edge_count) == 0:
                    orphans.append(str(row.id))

        svc = ReweaveService(self._vault)
        for orphan_id in orphans:
            result = svc.reweave(content_id=orphan_id)
            if result.ok:
                count += result.data.get("count", 0)
            else:
                msg = result.error.message if result.error else "unknown"
                warnings.append(f"Orphan reweave failed for {orphan_id}: {msg}")

        return count

    def _integrity_check(self, warnings: list[str]) -> int:
        """Run an integrity check via CheckService."""
        from ztlctl.services.check import CheckService

        svc = CheckService(self._vault)
        result = svc.check()
        if result.ok:
            issues = result.data.get("issues", [])
            error_count = sum(1 for i in issues if i.get("severity") == "error")
            if error_count > 0:
                warnings.append(f"Integrity check found {error_count} errors")
            return error_count
        msg = result.error.message if result.error else "unknown"
        warnings.append(f"Integrity check failed: {msg}")
        return 0
