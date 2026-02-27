"""ContextAssembler — token-budgeted agent context payloads.

Separated from SessionService because context assembly is a distinct
concern from session lifecycle management.  Context assembly reads
vault state and delegates to QueryService / GraphService; it does not
modify any data.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select

from ztlctl.infrastructure.database.schema import nodes
from ztlctl.infrastructure.vault import Vault
from ztlctl.services._helpers import estimate_tokens
from ztlctl.services.result import ServiceResult
from ztlctl.services.telemetry import trace_span, traced


class ContextAssembler:
    """Builds token-budgeted agent context payloads.

    Two entry points:
      - assemble(): full 5-layer context for an active session
      - build_brief(): quick orientation (session + stats + decisions + work queue)
    """

    def __init__(self, vault: Vault) -> None:
        self._vault = vault

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @traced
    def assemble(
        self,
        session_row: Any,
        *,
        topic: str | None = None,
        budget: int = 8000,
        ignore_checkpoints: bool = False,
    ) -> ServiceResult:
        """Full 5-layer assembly → ServiceResult(op="context").

        Layers:
          0: Identity + methodology (always included)
          1: Operational state (always included)
          2: Topic-scoped notes (budget-dependent)
          3: Graph-adjacent content (budget-dependent)
          4: Background signals (budget-dependent)
        """
        op = "context"
        warnings: list[str] = []
        token_count = 0

        session_id = str(session_row.id)
        session_topic = topic or str(session_row.topic or "")

        layers: dict[str, Any] = {}

        # -- Layer 0: Identity + Methodology (always) --
        with trace_span("layer_0_identity") as span:
            identity_path = self._vault.root / "self" / "identity.md"
            methodology_path = self._vault.root / "self" / "methodology.md"

            identity = identity_path.read_text(encoding="utf-8") if identity_path.exists() else None
            methodology = (
                methodology_path.read_text(encoding="utf-8") if methodology_path.exists() else None
            )

            layers["identity"] = identity
            layers["methodology"] = methodology
            layer_0_tokens = 0
            if identity:
                layer_0_tokens += estimate_tokens(identity)
            if methodology:
                layer_0_tokens += estimate_tokens(methodology)
            token_count += layer_0_tokens
            if span:
                span.tokens = layer_0_tokens

        # -- Layer 1: Operational State (always) --
        with trace_span("layer_1_operational") as span:
            layers["session"] = {
                "session_id": session_id,
                "topic": str(session_row.topic or ""),
                "status": str(session_row.status),
                "started": str(session_row.created),
            }
            layer_1_tokens = estimate_tokens(json.dumps(layers["session"]))

            # Recent decisions
            layers["recent_decisions"] = self._recent_decisions(warnings)
            for d in layers["recent_decisions"]:
                layer_1_tokens += estimate_tokens(json.dumps(d))

            # Work queue
            layers["work_queue"] = self._work_queue(warnings)
            for t in layers["work_queue"]:
                layer_1_tokens += estimate_tokens(json.dumps(t))

            # Session log entries (from latest checkpoint, unless overridden)
            layers["log_entries"] = self._log_entries(
                session_id,
                budget - token_count - layer_1_tokens,
                warnings,
                ignore_checkpoints=ignore_checkpoints,
            )
            for e in layers["log_entries"]:
                layer_1_tokens += estimate_tokens(json.dumps(e))

            token_count += layer_1_tokens
            if span:
                span.tokens = layer_1_tokens

        # -- Layer 2: Topic-scoped content (budget-dependent) --
        with trace_span("layer_2_topic") as span:
            remaining = budget - token_count
            layer_2_tokens = 0
            if remaining > 0 and session_topic:
                layers["topic_content"] = self._topic_content(session_topic, remaining, warnings)
                for item in layers["topic_content"]:
                    layer_2_tokens += estimate_tokens(json.dumps(item))
            else:
                layers["topic_content"] = []
            token_count += layer_2_tokens
            if span:
                span.tokens = layer_2_tokens

        # -- Layer 3: Graph-adjacent (budget-dependent) --
        with trace_span("layer_3_graph") as span:
            remaining = budget - token_count
            layer_3_tokens = 0
            if remaining > 0 and layers["topic_content"]:
                layers["graph_adjacent"] = self._graph_adjacent(
                    [item["id"] for item in layers["topic_content"] if "id" in item],
                    remaining,
                    warnings,
                )
                for item in layers["graph_adjacent"]:
                    layer_3_tokens += estimate_tokens(json.dumps(item))
            else:
                layers["graph_adjacent"] = []
            token_count += layer_3_tokens
            if span:
                span.tokens = layer_3_tokens

        # -- Layer 4: Background signals (budget-dependent) --
        with trace_span("layer_4_background") as span:
            remaining = budget - token_count
            layer_4_tokens = 0
            if remaining > 0:
                layers["background"] = self._background(remaining, warnings)
                for item in layers["background"]:
                    layer_4_tokens += estimate_tokens(json.dumps(item))
            else:
                layers["background"] = []
            token_count += layer_4_tokens
            if span:
                span.tokens = layer_4_tokens

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

    @traced
    def build_brief(
        self,
        session_row: Any | None,
        vault_stats: dict[str, int],
    ) -> ServiceResult:
        """Quick orientation → ServiceResult(op="brief")."""
        op = "brief"
        warnings: list[str] = []

        session_data: dict[str, Any] | None = None
        if session_row is not None:
            session_data = {
                "session_id": str(session_row.id),
                "topic": str(session_row.topic or ""),
                "status": str(session_row.status),
                "started": str(session_row.created),
            }

        decisions = self._recent_decisions(warnings)
        work_items = self._work_queue(warnings)

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "session": session_data,
                "vault_stats": vault_stats,
                "recent_decisions": decisions,
                "work_queue_count": len(work_items),
            },
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Layer helpers
    # ------------------------------------------------------------------

    def _recent_decisions(self, warnings: list[str]) -> list[dict[str, Any]]:
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

    def _work_queue(self, warnings: list[str]) -> list[dict[str, Any]]:
        """Layer 1: active/blocked tasks for operational awareness."""
        try:
            from ztlctl.services.query import QueryService

            result = QueryService(self._vault).work_queue()
            if result.ok:
                items: list[dict[str, Any]] = result.data.get("items", [])
                return items[:5]
            return []
        except Exception:
            warnings.append("Failed to load work queue")
            return []

    def _log_entries(
        self,
        session_id: str,
        remaining_budget: int,
        warnings: list[str],
        *,
        ignore_checkpoints: bool = False,
    ) -> list[dict[str, Any]]:
        """Load session log entries from latest checkpoint, with budget reduction."""
        from ztlctl.infrastructure.database.schema import session_logs

        try:
            with self._vault.engine.connect() as conn:
                # Load entries from checkpoint (or all if no checkpoint / overridden)
                query = select(session_logs).where(session_logs.c.session_id == session_id)

                if not ignore_checkpoints:
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

    def _topic_content(
        self,
        topic: str,
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 2: topic-scoped notes and references."""
        try:
            from ztlctl.services.query import QueryService

            result = QueryService(self._vault).search(topic, limit=10)
            if not result.ok:
                return []

            items: list[dict[str, Any]] = []
            tokens_used = 0
            for item in result.data.get("items", []):
                item_tokens = estimate_tokens(json.dumps(item))
                if tokens_used + item_tokens > remaining_budget:
                    break
                items.append(item)
                tokens_used += item_tokens
            return items
        except Exception:
            warnings.append("Failed to load topic content")
            return []

    def _graph_adjacent(
        self,
        content_ids: list[str],
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 3: graph neighbors of Layer 2 content (1 hop)."""
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

    def _background(
        self,
        remaining_budget: int,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Layer 4: background signals (recent activity, structural gaps)."""
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
