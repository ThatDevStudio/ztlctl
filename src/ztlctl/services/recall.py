"""RecallService — session history retrieval by date range and topic.

Provides temporal and topic-based recall of session logs, enabling agents
and users to query what was worked on, when, and in what context.
"""

from __future__ import annotations

import json
from itertools import combinations
from typing import Any

from sqlalchemy import func, select

from ztlctl.infrastructure.database.schema import node_tags, nodes, session_logs
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import traced


class RecallService(BaseService):
    """Retrieve session history by temporal range or topic keyword."""

    @traced
    def recall_temporal(
        self,
        *,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> ServiceResult:
        """Return sessions filtered by date range with per-session summaries.

        Args:
            from_date: ISO date string (YYYY-MM-DD). Include sessions created
                on or after this date. None means no lower bound.
            to_date: ISO date string (YYYY-MM-DD). Include sessions created
                on or before this date. None means no upper bound.

        Returns:
            ServiceResult with data={"sessions": [...], "count": N}.
            Each session dict contains:
              session_id, topic, status, started, ended, log_entry_count, note_ids
        """
        op = "recall_temporal"

        with self._vault.engine.connect() as conn:
            # Build query for session nodes (type='log')
            q = select(nodes).where(nodes.c.type == "log")

            if from_date is not None:
                q = q.where(nodes.c.created >= from_date)
            if to_date is not None:
                q = q.where(nodes.c.created <= to_date)

            q = q.order_by(nodes.c.created_at.desc(), nodes.c.created.desc())
            session_rows = conn.execute(q).fetchall()

            sessions: list[dict[str, Any]] = []
            for row in session_rows:
                session_id = str(row.id)

                # Count all log entries for this session
                count_row = conn.execute(
                    select(func.count(session_logs.c.id).label("cnt")).where(
                        session_logs.c.session_id == session_id
                    )
                ).first()
                log_entry_count = int(count_row.cnt) if count_row else 0

                # Collect note/reference/task IDs created in this session
                note_rows = conn.execute(
                    select(nodes.c.id).where(
                        nodes.c.session == session_id,
                        nodes.c.type.in_(["note", "reference", "task"]),
                    )
                ).fetchall()
                note_ids = [str(r.id) for r in note_rows]

                # Determine started timestamp
                started = str(row.created_at or row.created)

                # Determine ended timestamp (only for closed sessions)
                ended: str | None = None
                if str(row.status) == "closed":
                    ended = str(row.modified_at or row.modified)

                sessions.append(
                    {
                        "session_id": session_id,
                        "topic": str(row.topic or ""),
                        "status": str(row.status),
                        "started": started,
                        "ended": ended,
                        "log_entry_count": log_entry_count,
                        "note_ids": note_ids,
                    }
                )

        return ServiceResult(
            ok=True,
            op=op,
            data={"sessions": sessions, "count": len(sessions)},
        )

    @traced
    def recall_topic(self, query: str) -> ServiceResult:
        """Return sessions whose log entries match a text query.

        Searches session_logs.summary using case-insensitive LIKE matching.
        Groups results by session, returning matched log entries per session.

        Args:
            query: Text to search for. Must be non-empty.

        Returns:
            ServiceResult with data={"sessions": [...], "count": N, "query": query}.
            Each session dict contains:
              session_id, topic, status, matched_entries: [{summary, timestamp, type}]
        """
        op = "recall_topic"

        # Validate non-empty query
        if not query or not query.strip():
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="EMPTY_QUERY",
                    message="Query must be a non-empty string",
                ),
            )

        query = query.strip()

        with self._vault.engine.connect() as conn:
            # Search session_logs.summary with case-insensitive LIKE
            matching_logs = conn.execute(
                select(session_logs).where(
                    func.lower(session_logs.c.summary).like(f"%{query.lower()}%")
                )
            ).fetchall()

            if not matching_logs:
                return ServiceResult(
                    ok=True,
                    op=op,
                    data={"sessions": [], "count": 0, "query": query},
                )

            # Group matched entries by session_id
            session_entries: dict[str, list[dict[str, Any]]] = {}
            for log_row in matching_logs:
                sid = str(log_row.session_id)
                if sid not in session_entries:
                    session_entries[sid] = []
                session_entries[sid].append(
                    {
                        "summary": str(log_row.summary),
                        "timestamp": str(log_row.timestamp),
                        "type": str(log_row.type),
                    }
                )

            # Fetch session node details for each matched session
            sessions: list[dict[str, Any]] = []
            for sid, entries in session_entries.items():
                session_row = conn.execute(
                    select(nodes).where(nodes.c.id == sid, nodes.c.type == "log")
                ).first()

                if session_row is None:
                    # Orphaned log entries — include minimal info
                    sessions.append(
                        {
                            "session_id": sid,
                            "topic": "",
                            "status": "unknown",
                            "matched_entries": entries,
                        }
                    )
                else:
                    sessions.append(
                        {
                            "session_id": sid,
                            "topic": str(session_row.topic or ""),
                            "status": str(session_row.status),
                            "matched_entries": entries,
                        }
                    )

        return ServiceResult(
            ok=True,
            op=op,
            data={"sessions": sessions, "count": len(sessions), "query": query},
        )

    @traced
    def recall_topology(self, *, limit: int = 10) -> ServiceResult:
        """Return pairs of sessions that share note references or tags.

        For each pair of sessions, computes:
          - shared_notes: note IDs referenced in log entries of both sessions
          - shared_tags: tags used by notes created in both sessions

        Pairs with no shared content are excluded. Results are sorted by
        total shared items (shared_notes + shared_tags) descending, then
        capped to ``limit``.

        Args:
            limit: Maximum number of pairs to return.

        Returns:
            ServiceResult with data={"pairs": [...], "count": N}.
            Each pair: {session_a, session_b, shared_notes: [...], shared_tags: [...]}
        """
        op = "recall_topology"

        with self._vault.engine.connect() as conn:
            # Step 1: Collect all session IDs (nodes of type='log')
            session_rows = conn.execute(select(nodes.c.id).where(nodes.c.type == "log")).fetchall()
            session_ids = [str(r.id) for r in session_rows]

            if len(session_ids) < 2:
                return ServiceResult(
                    ok=True,
                    op=op,
                    data={"pairs": [], "count": 0, "limit": limit},
                )

            # Step 2: For each session, collect referenced note IDs from log entries
            session_refs: dict[str, set[str]] = {}
            for sid in session_ids:
                log_rows = conn.execute(
                    select(session_logs.c.references).where(
                        session_logs.c.session_id == sid,
                        session_logs.c.references.isnot(None),
                    )
                ).fetchall()
                refs: set[str] = set()
                for row in log_rows:
                    raw = row.references
                    if raw:
                        try:
                            parsed = json.loads(raw)
                            if isinstance(parsed, list):
                                refs.update(str(r) for r in parsed)
                        except (json.JSONDecodeError, TypeError):
                            pass
                session_refs[sid] = refs

            # Step 3: For each session, collect tags via notes created in that session
            session_tags: dict[str, set[str]] = {}
            for sid in session_ids:
                note_rows = conn.execute(
                    select(nodes.c.id).where(
                        nodes.c.session == sid,
                        nodes.c.type.in_(["note", "reference", "task"]),
                    )
                ).fetchall()
                note_ids = [str(r.id) for r in note_rows]

                tags: set[str] = set()
                if note_ids:
                    tag_rows = conn.execute(
                        select(node_tags.c.tag).where(node_tags.c.node_id.in_(note_ids))
                    ).fetchall()
                    tags = {str(r.tag) for r in tag_rows}
                session_tags[sid] = tags

        # Step 4: Build pairs with shared notes and tags
        pairs: list[dict[str, Any]] = []
        for sid_a, sid_b in combinations(session_ids, 2):
            shared_notes = sorted(session_refs[sid_a] & session_refs[sid_b])
            shared_tags = sorted(session_tags[sid_a] & session_tags[sid_b])

            if not shared_notes and not shared_tags:
                continue

            pairs.append(
                {
                    "session_a": sid_a,
                    "session_b": sid_b,
                    "shared_notes": shared_notes,
                    "shared_tags": shared_tags,
                }
            )

        # Step 5: Sort by total shared items descending, then cap to limit
        pairs.sort(key=lambda p: len(p["shared_notes"]) + len(p["shared_tags"]), reverse=True)
        pairs = pairs[:limit]

        return ServiceResult(
            ok=True,
            op=op,
            data={"pairs": pairs, "count": len(pairs), "limit": limit},
        )
