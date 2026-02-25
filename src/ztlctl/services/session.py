"""SessionService — session lifecycle and context management.

Sessions are first-class organizational containers. Every content
item links to its creation session. (DESIGN.md Section 2, 8)
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import insert, select, text

from ztlctl.infrastructure.database.counters import next_sequential_id
from ztlctl.infrastructure.database.schema import edges, nodes, session_logs
from ztlctl.services._helpers import now_iso, today_iso
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult


class SessionService(BaseService):
    """Handles session lifecycle and agent context."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, topic: str) -> ServiceResult:
        """Start a new session, returning the LOG-NNNN id."""
        op = "session_start"
        today = today_iso()

        with self._vault.transaction() as txn:
            session_id = next_sequential_id(txn.conn, "LOG-")

            # Create JSONL file with initial entry
            path = txn.resolve_path("log", session_id)
            initial_entry = json.dumps(
                {
                    "type": "session_start",
                    "session_id": session_id,
                    "topic": topic,
                    "timestamp": now_iso(),
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

        # Dispatch event
        warnings: list[str] = []
        self._dispatch_event("post_session_start", {"session_id": session_id}, warnings)

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "id": session_id,
                "topic": topic,
                "path": rel_path,
                "status": "open",
            },
            warnings=warnings,
        )

    def close(self, *, summary: str | None = None) -> ServiceResult:
        """Close the active session with enrichment pipeline.

        Pipeline: LOG CLOSE -> CROSS-SESSION REWEAVE -> ORPHAN SWEEP -> INTEGRITY CHECK -> REPORT
        """
        op = "session_close"
        today = today_iso()
        warnings: list[str] = []
        cfg = self._vault.settings.session

        # -- LOG CLOSE (find + update in one transaction to avoid TOCTOU) --
        with self._vault.transaction() as txn:
            active = txn.conn.execute(
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
                    "timestamp": now_iso(),
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

        # -- EVENT DISPATCH --
        self._dispatch_event(
            "post_session_close",
            {
                "session_id": session_id,
                "stats": {
                    "reweave_count": reweave_count,
                    "orphan_count": orphan_count,
                    "integrity_issues": integrity_issues,
                },
            },
            warnings,
            session_id=session_id,
        )

        # Drain event bus as sync barrier
        bus = self._vault.event_bus
        if bus is not None:
            bus.drain()

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
        today = today_iso()

        with self._vault.transaction() as txn:
            session = txn.conn.execute(
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

            txn.conn.execute(
                nodes.update().where(nodes.c.id == session_id).values(status="open", modified=today)
            )

            # Append reopen entry to JSONL
            file_path = self._vault.root / session.path
            reopen_entry = json.dumps(
                {
                    "type": "session_reopen",
                    "session_id": session_id,
                    "timestamp": now_iso(),
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
        detail: str | None = None,
        entry_type: str = "log_entry",
        subtype: str | None = None,
        references: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceResult:
        """Append a log entry to the active session.

        Writes to both the JSONL file (for portability) and the
        session_logs DB table (for querying and budget tracking).
        """
        op = "log_entry"
        timestamp = now_iso()

        with self._vault.transaction() as txn:
            # Find active session
            active = txn.conn.execute(
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
                        message="No active session for log entry",
                    ),
                )

            session_id = str(active.id)

            # Append to JSONL
            file_path = self._vault.root / active.path
            jsonl_entry = json.dumps(
                {
                    "type": "log_entry",
                    "session_id": session_id,
                    "message": message,
                    "pinned": pin,
                    "cost": cost,
                    "timestamp": timestamp,
                },
                separators=(",", ":"),
            )
            existing = txn.read_file(file_path)
            txn.write_file(file_path, existing + jsonl_entry + "\n")

            # Insert into session_logs DB table
            result = txn.conn.execute(
                insert(session_logs).values(
                    session_id=session_id,
                    timestamp=timestamp,
                    type=entry_type,
                    subtype=subtype,
                    summary=message,
                    detail=detail,
                    cost=cost,
                    pinned=1 if pin else 0,
                    references=json.dumps(references) if references else None,
                    metadata=json.dumps(metadata) if metadata else None,
                )
            )
            entry_id = result.lastrowid

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "entry_id": entry_id,
                "session_id": session_id,
                "timestamp": timestamp,
            },
        )

    def cost(self, *, report: int | None = None) -> ServiceResult:
        """Query or report accumulated token cost for the active session.

        Query mode (report=None): returns total cost and entry count.
        Report mode (report=N): also includes budget, remaining, and over_budget flag.
        """
        op = "cost"

        with self._vault.engine.connect() as conn:
            # Find active session
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
                        message="No active session for cost query",
                    ),
                )

            session_id = str(active.id)

            # Sum costs from session_logs
            from sqlalchemy import func

            row = conn.execute(
                select(
                    func.coalesce(func.sum(session_logs.c.cost), 0).label("total"),
                    func.count(session_logs.c.id).label("count"),
                ).where(session_logs.c.session_id == session_id)
            ).first()

            total_cost = int(row.total) if row else 0
            entry_count = int(row.count) if row else 0

        data: dict[str, Any] = {
            "session_id": session_id,
            "total_cost": total_cost,
            "entry_count": entry_count,
        }

        if report is not None:
            remaining = report - total_cost
            data["budget"] = report
            data["remaining"] = remaining
            data["over_budget"] = remaining < 0

        return ServiceResult(ok=True, op=op, data=data)

    def context(
        self,
        *,
        topic: str | None = None,
        budget: int = 8000,
    ) -> ServiceResult:
        """Build token-budgeted agent context payload.

        5-layer assembly:
          Layer 0: Identity + methodology (always included)
          Layer 1: Operational state (always included)
          Layer 2: Topic-scoped notes (budget-dependent)
          Layer 3: Graph-adjacent content (budget-dependent)
          Layer 4: Background signals (budget-dependent)
        """
        from ztlctl.services._helpers import estimate_tokens

        op = "context"
        warnings: list[str] = []
        token_count = 0

        # Find active session
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
                    message="No active session for context assembly",
                ),
            )

        session_id = str(active.id)
        session_topic = topic or str(active.topic or "")

        layers: dict[str, Any] = {}

        # -- Layer 0: Identity + Methodology (always) --
        identity_path = self._vault.root / "self" / "identity.md"
        methodology_path = self._vault.root / "self" / "methodology.md"

        identity = identity_path.read_text(encoding="utf-8") if identity_path.exists() else None
        methodology = (
            methodology_path.read_text(encoding="utf-8") if methodology_path.exists() else None
        )

        layers["identity"] = identity
        layers["methodology"] = methodology
        if identity:
            token_count += estimate_tokens(identity)
        if methodology:
            token_count += estimate_tokens(methodology)

        # -- Layer 1: Operational State (always) --
        layers["session"] = {
            "session_id": session_id,
            "topic": str(active.topic or ""),
            "status": str(active.status),
            "started": str(active.created),
        }
        token_count += estimate_tokens(json.dumps(layers["session"]))

        # Recent decisions
        layers["recent_decisions"] = self._context_recent_decisions(warnings)
        for d in layers["recent_decisions"]:
            token_count += estimate_tokens(json.dumps(d))

        # Work queue
        layers["work_queue"] = self._context_work_queue(warnings)
        for t in layers["work_queue"]:
            token_count += estimate_tokens(json.dumps(t))

        # Session log entries (from latest checkpoint)
        layers["log_entries"] = self._context_log_entries(
            session_id, budget - token_count, warnings
        )
        for e in layers["log_entries"]:
            token_count += estimate_tokens(json.dumps(e))

        # -- Layer 2: Topic-scoped content (budget-dependent) --
        remaining = budget - token_count
        if remaining > 0 and session_topic:
            layers["topic_content"] = self._context_topic_content(
                session_topic, remaining, warnings
            )
            for item in layers["topic_content"]:
                token_count += estimate_tokens(json.dumps(item))
        else:
            layers["topic_content"] = []

        # -- Layer 3: Graph-adjacent (budget-dependent) --
        remaining = budget - token_count
        if remaining > 0 and layers["topic_content"]:
            layers["graph_adjacent"] = self._context_graph_adjacent(
                [item["id"] for item in layers["topic_content"] if "id" in item],
                remaining,
                warnings,
            )
            for item in layers["graph_adjacent"]:
                token_count += estimate_tokens(json.dumps(item))
        else:
            layers["graph_adjacent"] = []

        # -- Layer 4: Background signals (budget-dependent) --
        remaining = budget - token_count
        if remaining > 0:
            layers["background"] = self._context_background(remaining, warnings)
            for item in layers["background"]:
                token_count += estimate_tokens(json.dumps(item))
        else:
            layers["background"] = []

        remaining = budget - token_count
        pressure = "normal"
        if remaining < 0:
            pressure = "exceeded"
        elif remaining < budget * 0.15:
            pressure = "caution"

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "total_tokens": token_count,
                "budget": budget,
                "remaining": remaining,
                "pressure": pressure,
                "layers": layers,
            },
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Context assembly helpers
    # ------------------------------------------------------------------

    def _context_recent_decisions(self, warnings: list[str]) -> list[dict[str, Any]]:
        """Layer 1: recent non-superseded decisions."""
        try:
            with self._vault.engine.connect() as conn:
                rows = conn.execute(
                    select(nodes.c.id, nodes.c.title, nodes.c.status, nodes.c.created)
                    .where(
                        nodes.c.type == "note",
                        nodes.c.subtype == "decision",
                        nodes.c.status != "superseded",
                        nodes.c.archived == 0,
                    )
                    .order_by(nodes.c.created.desc())
                    .limit(5)
                ).fetchall()
                return [
                    {"id": str(r.id), "title": str(r.title), "status": str(r.status)} for r in rows
                ]
        except Exception:
            warnings.append("Failed to load recent decisions")
            return []

    def _context_work_queue(self, warnings: list[str]) -> list[dict[str, Any]]:
        """Layer 1: active/blocked tasks for operational awareness."""
        try:
            from ztlctl.services.query import QueryService

            result = QueryService(self._vault).work_queue()
            if result.ok:
                return result.data.get("items", [])[:5]
            return []
        except Exception:
            warnings.append("Failed to load work queue")
            return []

    def _context_log_entries(
        self,
        session_id: str,
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Load session log entries from latest checkpoint, with budget reduction."""
        from ztlctl.services._helpers import estimate_tokens

        try:
            with self._vault.engine.connect() as conn:
                # Find latest checkpoint
                checkpoint = conn.execute(
                    select(session_logs)
                    .where(
                        session_logs.c.session_id == session_id,
                        session_logs.c.subtype == "checkpoint",
                    )
                    .order_by(session_logs.c.timestamp.desc())
                    .limit(1)
                ).first()

                # Load entries from checkpoint (or all if no checkpoint)
                query = select(session_logs).where(session_logs.c.session_id == session_id)
                if checkpoint:
                    query = query.where(session_logs.c.timestamp >= str(checkpoint.timestamp))
                query = query.order_by(session_logs.c.timestamp.asc())
                rows = conn.execute(query).fetchall()

            # Build entries with budget reduction
            entries: list[dict[str, Any]] = []
            tokens_used = 0

            for row in rows:
                entry: dict[str, Any] = {
                    "id": row.id,
                    "type": str(row.type),
                    "summary": str(row.summary),
                    "timestamp": str(row.timestamp),
                    "pinned": bool(row.pinned),
                    "cost": int(row.cost or 0),
                }

                # Include detail if budget allows
                if row.detail and tokens_used < remaining_budget:
                    detail_tokens = estimate_tokens(str(row.detail))
                    if tokens_used + detail_tokens < remaining_budget:
                        entry["detail"] = str(row.detail)
                        tokens_used += detail_tokens

                # Include references if present
                if row.references:
                    entry["references"] = json.loads(row.references)

                entry_tokens = estimate_tokens(json.dumps(entry))
                if tokens_used + entry_tokens > remaining_budget and not row.pinned:
                    continue  # Skip non-pinned entries when over budget
                tokens_used += entry_tokens
                entries.append(entry)

            return entries
        except Exception:
            warnings.append("Failed to load session log entries")
            return []

    def _context_topic_content(
        self,
        topic: str,
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 2: topic-scoped notes and references."""
        from ztlctl.services._helpers import estimate_tokens

        try:
            from ztlctl.services.query import QueryService

            result = QueryService(self._vault).search(topic, limit=10)
            if not result.ok:
                return []

            items: list[dict[str, Any]] = []
            tokens_used = 0
            for item in result.data.get("results", []):
                item_tokens = estimate_tokens(json.dumps(item))
                if tokens_used + item_tokens > remaining_budget:
                    break
                items.append(item)
                tokens_used += item_tokens
            return items
        except Exception:
            warnings.append("Failed to load topic content")
            return []

    def _context_graph_adjacent(
        self,
        content_ids: list[str],
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 3: graph neighbors of Layer 2 content (1 hop)."""
        from ztlctl.services._helpers import estimate_tokens

        try:
            from ztlctl.services.graph import GraphService

            svc = GraphService(self._vault)

            seen: set[str] = set(content_ids)
            neighbors: list[dict[str, Any]] = []
            tokens_used = 0

            for cid in content_ids[:3]:  # Limit to first 3 to avoid explosion
                result = svc.related(cid, depth=1, top=5)
                if not result.ok:
                    continue
                for item in result.data.get("items", []):
                    item_id = item.get("id", "")
                    if item_id in seen:
                        continue
                    seen.add(item_id)
                    item_tokens = estimate_tokens(json.dumps(item))
                    if tokens_used + item_tokens > remaining_budget:
                        return neighbors
                    neighbors.append(item)
                    tokens_used += item_tokens

            return neighbors
        except Exception:
            warnings.append("Failed to load graph neighbors")
            return []

    def _context_background(
        self,
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 4: background signals (recent activity, structural gaps)."""
        from ztlctl.services._helpers import estimate_tokens

        try:
            from ztlctl.services.query import QueryService

            svc = QueryService(self._vault)

            items: list[dict[str, Any]] = []
            tokens_used = 0

            # Recent activity
            recent = svc.list_items(sort="recency", limit=5)
            if recent.ok:
                for item in recent.data.get("items", []):
                    item_tokens = estimate_tokens(json.dumps(item))
                    if tokens_used + item_tokens > remaining_budget:
                        break
                    items.append({**item, "_signal": "recent"})
                    tokens_used += item_tokens

            # Structural gaps: notes with 0 outgoing edges
            remaining = remaining_budget - tokens_used
            if remaining > 0:
                from ztlctl.services.graph import GraphService

                gaps = GraphService(self._vault).gaps()
                if gaps.ok:
                    for gap in gaps.data.get("items", [])[:3]:
                        gap_tokens = estimate_tokens(json.dumps(gap))
                        if tokens_used + gap_tokens > remaining_budget:
                            break
                        items.append({**gap, "_signal": "gap"})
                        tokens_used += gap_tokens

            return items
        except Exception:
            warnings.append("Failed to load background signals")
            return []

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
