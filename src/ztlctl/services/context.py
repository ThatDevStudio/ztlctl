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

from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.database.schema import nodes
from ztlctl.infrastructure.vault import Vault
from ztlctl.services._helpers import estimate_tokens
from ztlctl.services.contracts import AgentContextResultData, TopicPacketData, dump_validated
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

        payload = dump_validated(
            AgentContextResultData,
            {
                "total_tokens": token_count,
                "budget": budget,
                "remaining": remaining,
                "pressure": pressure,
                "layers": layers,
            },
        )

        return ServiceResult(
            ok=True,
            op=op,
            data=payload,
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

    @traced
    def build_topic_packet(
        self,
        topic: str,
        *,
        mode: str = "learn",
        budget: int = 4000,
    ) -> ServiceResult:
        """Build a topic packet for conversational learning and review."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.query import QueryService

        warnings: list[str] = []
        query = QueryService(self._vault)
        graph = GraphService(self._vault)
        total_tokens = 0

        def _budget_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
            nonlocal total_tokens
            selected: list[dict[str, Any]] = []
            for item in items:
                item_tokens = estimate_tokens(json.dumps(item))
                if total_tokens + item_tokens > budget:
                    break
                total_tokens += item_tokens
                selected.append(item)
            return selected

        note_rank = "review" if mode == "review" else "garden" if mode == "decision" else "hybrid"
        reference_rank = "review" if mode == "review" else "garden"
        notes_result = query.search(topic, content_type="note", rank_by=note_rank, limit=8)
        ref_result = query.search(
            topic,
            content_type="reference",
            rank_by=reference_rank,
            limit=6,
        )
        decisions_result = query.list_items(
            content_type="note",
            subtype="decision",
            topic=topic,
            limit=5,
        )
        tasks_result = query.list_items(content_type="task", topic=topic, limit=5)

        notes = notes_result.data.get("items", []) if notes_result.ok else []
        references = ref_result.data.get("items", []) if ref_result.ok else []
        decisions = decisions_result.data.get("items", []) if decisions_result.ok else []
        tasks = tasks_result.data.get("items", []) if tasks_result.ok else []

        adjacent = self._graph_adjacent(
            [item["id"] for item in notes[:3] if item.get("id")],
            max(budget - total_tokens, 0),
            warnings,
        )
        graph_adjacent = adjacent

        gaps: list[dict[str, Any]] = []
        bridges: list[dict[str, Any]] = []
        gaps_result = graph.gaps(top=5)
        if gaps_result.ok:
            gaps = gaps_result.data.get("items", [])
        bridges_result = graph.bridges(top=5)
        if bridges_result.ok:
            bridges = bridges_result.data.get("items", [])

        all_items = [*notes, *references, *decisions, *tasks, *graph_adjacent, *bridges]
        stale_seed_result = query.list_items(topic=topic, limit=20)
        stale_seed_items = stale_seed_result.data.get("items", []) if stale_seed_result.ok else []
        all_items.extend(stale_seed_items)
        detail_map = self._packet_detail_map(
            [str(item["id"]) for item in all_items if item.get("id")],
            warnings,
        )
        notes = self._decorate_packet_items(notes, detail_map)
        references = self._decorate_packet_items(references, detail_map)
        decisions = self._decorate_packet_items(decisions, detail_map)
        tasks = self._decorate_packet_items(tasks, detail_map)
        graph_adjacent = self._decorate_packet_items(graph_adjacent, detail_map)

        bridge_candidates = self._decorate_packet_items(bridges[:3], detail_map)
        stale_items = self._stale_topic_items(topic, warnings)
        stale_items = self._decorate_packet_items(stale_items, detail_map)

        notes = _budget_items(notes)
        references = _budget_items(references)
        decisions = _budget_items(decisions)
        tasks = _budget_items(tasks)
        graph_adjacent = _budget_items(graph_adjacent)
        gaps = _budget_items(gaps)
        bridges = _budget_items(bridges)
        bridge_candidates = _budget_items(bridge_candidates)
        stale_items = _budget_items(stale_items)

        packet_ids = {
            str(item["id"])
            for item in [*notes, *references, *decisions, *tasks, *graph_adjacent]
            if item.get("id")
        }
        evidence = _budget_items(
            self._packet_evidence([*references, *notes, *decisions], detail_map)
        )
        supporting_links, conflicts = self._packet_links(packet_ids, detail_map)
        supporting_links = _budget_items(supporting_links)
        conflicts = _budget_items(conflicts)

        provenance = self._packet_provenance_from_details(detail_map, packet_ids)
        ranking_explanations = self._packet_ranking_explanations(
            notes,
            references,
            decisions,
            tasks,
            graph_adjacent,
            stale_items,
            bridge_candidates,
        )
        suggested_actions = _budget_items(
            self._suggested_actions(
                topic,
                mode=mode,
                notes=notes,
                references=references,
                decisions=decisions,
                tasks=tasks,
                stale_items=stale_items,
                bridge_candidates=bridge_candidates,
                conflicts=conflicts,
            )
        )

        payload = dump_validated(
            TopicPacketData,
            {
                "topic": topic,
                "mode": mode,
                "budget": budget,
                "total_tokens": total_tokens,
                "notes": notes,
                "references": references,
                "decisions": decisions,
                "tasks": tasks,
                "evidence": evidence,
                "graph_adjacent": graph_adjacent,
                "gaps": gaps,
                "bridges": bridges,
                "bridge_candidates": bridge_candidates,
                "stale_items": stale_items,
                "supporting_links": supporting_links,
                "conflicts": conflicts,
                "suggested_actions": suggested_actions,
                "ranking_explanations": ranking_explanations,
                "provenance": provenance,
                "provenance_map": provenance,
            },
        )

        return ServiceResult(ok=True, op="topic_packet", data=payload, warnings=warnings)

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

    @staticmethod
    def _section_map(markdown: str) -> dict[str, str]:
        """Split markdown into second-level sections."""
        sections: dict[str, list[str]] = {}
        current: str | None = None
        for line in markdown.splitlines():
            if line.startswith("## "):
                current = line[3:].strip()
                sections.setdefault(current, [])
                continue
            if current is not None:
                sections[current].append(line)
        return {name: "\n".join(lines).strip() for name, lines in sections.items()}

    @staticmethod
    def _bullet_lines(section_text: str) -> list[str]:
        """Extract markdown bullet lines from a section."""
        return [
            line.strip().lstrip("- ").strip()
            for line in section_text.splitlines()
            if line.strip().startswith("-")
        ]

    @staticmethod
    def _excerpt_lines(section_text: str) -> list[str]:
        """Extract blockquote lines from an excerpts section."""
        excerpts: list[str] = []
        current: list[str] = []
        for line in section_text.splitlines():
            stripped = line.strip()
            if stripped.startswith(">"):
                current.append(stripped.lstrip("> ").strip())
                continue
            if current:
                excerpts.append(" ".join(current).strip())
                current = []
        if current:
            excerpts.append(" ".join(current).strip())
        return [excerpt for excerpt in excerpts if excerpt]

    @staticmethod
    def _first_summary(body: str) -> str | None:
        """Return the first non-empty paragraph-like line."""
        for line in body.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
        return None

    def _packet_detail_map(
        self,
        content_ids: list[str],
        warnings: list[str],
    ) -> dict[str, dict[str, Any]]:
        """Load packet item details from files and get() payloads."""
        details: dict[str, dict[str, Any]] = {}
        try:
            from ztlctl.services.query import QueryService

            query = QueryService(self._vault)
            for content_id in content_ids:
                if content_id in details:
                    continue
                result = query.get(content_id)
                if not result.ok:
                    continue
                item = result.data
                raw_path = self._vault.root / str(item.get("path", ""))
                sections: dict[str, str] = {}
                if raw_path.is_file():
                    raw = raw_path.read_text(encoding="utf-8")
                    _, body = parse_frontmatter(raw)
                    sections = self._section_map(body)
                summary = sections.get("Summary") or self._first_summary(str(item.get("body", "")))
                details[content_id] = {
                    "summary": summary,
                    "key_points": self._bullet_lines(sections.get("Key Points", "")),
                    "excerpts": self._excerpt_lines(sections.get("Excerpts", "")),
                    "provenance": self._bullet_lines(sections.get("Provenance", "")),
                    "links_out": list(item.get("links_out", [])),
                    "links_in": list(item.get("links_in", [])),
                    "type": item.get("type"),
                    "title": item.get("title"),
                    "path": item.get("path"),
                    "status": item.get("status"),
                    "topic": item.get("topic"),
                }
        except Exception:
            warnings.append("Failed to load packet item details")
        return details

    def _decorate_packet_items(
        self,
        items: list[dict[str, Any]],
        detail_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Attach summary and evidence hints to packet items."""
        decorated: list[dict[str, Any]] = []
        for item in items:
            updated = item.copy()
            detail = detail_map.get(str(item.get("id", "")), {})
            if detail.get("summary"):
                updated["summary"] = detail["summary"]
            if detail.get("key_points"):
                updated["key_points"] = detail["key_points"][:5]
            if detail.get("excerpts"):
                updated["excerpts"] = detail["excerpts"][:3]
            if detail.get("provenance"):
                updated["provenance_count"] = len(detail["provenance"])
            decorated.append(updated)
        return decorated

    def _packet_evidence(
        self,
        items: list[dict[str, Any]],
        detail_map: dict[str, dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build evidence excerpts from packet references and notes."""
        evidence: list[dict[str, Any]] = []
        for item in items:
            content_id = str(item.get("id", ""))
            if not content_id:
                continue
            detail = detail_map.get(content_id, {})
            title = str(item.get("title", content_id))
            source_type = str(item.get("type", "note"))
            excerpts = list(detail.get("excerpts", []))
            if excerpts:
                for excerpt in excerpts[:2]:
                    evidence.append(
                        {
                            "content_id": content_id,
                            "title": title,
                            "source_type": source_type,
                            "text": excerpt,
                            "locator": "excerpts",
                        }
                    )
                continue
            summary = detail.get("summary")
            if summary:
                evidence.append(
                    {
                        "content_id": content_id,
                        "title": title,
                        "source_type": source_type,
                        "text": str(summary),
                        "locator": "summary",
                    }
                )
        return evidence

    def _packet_links(
        self,
        packet_ids: set[str],
        detail_map: dict[str, dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Extract supporting and conflicting typed links across packet items."""
        supporting_types = {"relates", "supports", "supersedes", "implements"}
        conflict_types = {"contradicts", "opposes", "conflicts"}
        supporting: list[dict[str, Any]] = []
        conflicts: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str]] = set()

        def _append_link(
            source_id: str,
            target_id: str,
            edge_type: str,
            direction: str,
        ) -> None:
            key = (source_id, target_id, edge_type, direction)
            if key in seen or target_id not in packet_ids:
                return
            seen.add(key)
            payload = {
                "source_id": source_id,
                "target_id": target_id,
                "edge_type": edge_type,
                "direction": direction,
            }
            if edge_type in supporting_types:
                supporting.append(payload)
            if edge_type in conflict_types:
                conflicts.append(payload)

        for source_id, detail in detail_map.items():
            if source_id not in packet_ids:
                continue
            for link in detail.get("links_out", []):
                _append_link(
                    source_id,
                    str(link.get("id", "")),
                    str(link.get("edge_type", "relates")),
                    "outgoing",
                )
            for link in detail.get("links_in", []):
                _append_link(
                    str(link.get("id", "")),
                    source_id,
                    str(link.get("edge_type", "relates")),
                    "incoming",
                )
        return supporting, conflicts

    def _stale_topic_items(
        self,
        topic: str,
        warnings: list[str],
    ) -> list[dict[str, Any]]:
        """Find older topic items that should be revisited."""
        try:
            from ztlctl.services.query import QueryService

            result = QueryService(self._vault).list_items(topic=topic, limit=20)
            if not result.ok:
                return []
            items = list(result.data.get("items", []))
            items.sort(key=lambda item: str(item.get("modified", "")))
            stale: list[dict[str, Any]] = []
            for item in items:
                age_days = self._age_days(item.get("modified"))
                if age_days < 14:
                    continue
                stale.append({**item, "stale_days": round(age_days, 1)})
            return stale[:5]
        except Exception:
            warnings.append("Failed to build stale topic items")
            return []

    def _packet_ranking_explanations(
        self,
        *collections: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        """Collect ranking explanations from packet item collections."""
        explanations: dict[str, dict[str, Any]] = {}
        for items in collections:
            for item in items:
                item_id = str(item.get("id", ""))
                ranking = item.get("ranking")
                if item_id and isinstance(ranking, dict):
                    explanations[item_id] = ranking
        return explanations

    def _suggested_actions(
        self,
        topic: str,
        *,
        mode: str,
        notes: list[dict[str, Any]],
        references: list[dict[str, Any]],
        decisions: list[dict[str, Any]],
        tasks: list[dict[str, Any]],
        stale_items: list[dict[str, Any]],
        bridge_candidates: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Generate follow-up actions from packet structure."""
        actions: list[dict[str, Any]] = []
        if references and not notes:
            actions.append(
                {
                    "type": "note",
                    "title": f"Synthesize notes for {topic}",
                    "rationale": (
                        "There are references for this topic but little durable synthesis."
                    ),
                    "related_ids": [str(item.get("id", "")) for item in references[:3]],
                }
            )
        if not decisions and mode == "decision":
            actions.append(
                {
                    "type": "decision",
                    "title": f"Draft a decision for {topic}",
                    "rationale": "The packet surfaced evidence but no recorded decision.",
                    "related_ids": [str(item.get("id", "")) for item in notes[:2] + references[:2]],
                }
            )
        if stale_items:
            first_stale = stale_items[0]
            actions.append(
                {
                    "type": "review",
                    "title": f"Refresh {first_stale.get('title', topic)}",
                    "rationale": "This item is stale enough to revisit during enrichment.",
                    "related_ids": [str(first_stale.get("id", ""))],
                }
            )
        if bridge_candidates:
            actions.append(
                {
                    "type": "link",
                    "title": f"Review bridge candidates for {topic}",
                    "rationale": "Bridge-like items may connect this topic to nearby clusters.",
                    "related_ids": [str(item.get("id", "")) for item in bridge_candidates[:3]],
                }
            )
        if conflicts:
            actions.append(
                {
                    "type": "note",
                    "title": f"Resolve conflicting evidence in {topic}",
                    "rationale": "Conflicting links suggest the topic needs explicit synthesis.",
                    "related_ids": [str(link.get("source_id", "")) for link in conflicts[:3]],
                }
            )
        if mode == "review" and not tasks:
            actions.append(
                {
                    "type": "task",
                    "title": f"Create review task for {topic}",
                    "rationale": "The topic has review signals but no explicit task queue.",
                    "related_ids": [str(item.get("id", "")) for item in stale_items[:2]],
                }
            )
        return actions

    @staticmethod
    def _packet_provenance_from_details(
        detail_map: dict[str, dict[str, Any]],
        packet_ids: set[str],
    ) -> dict[str, list[str]]:
        """Build a simple provenance map for packet items."""
        provenance: dict[str, list[str]] = {}
        for content_id in packet_ids:
            detail = detail_map.get(content_id, {})
            entries: list[str] = []
            if detail.get("path"):
                entries.append(f"Path: {detail['path']}")
            for item in detail.get("provenance", []):
                if item:
                    entries.append(str(item))
            provenance[content_id] = entries
        return provenance

    @staticmethod
    def _age_days(timestamp: Any) -> float:
        """Compute age in days from an ISO timestamp-like value."""
        if timestamp is None:
            return 0.0
        from datetime import UTC, datetime

        try:
            dt = datetime.fromisoformat(str(timestamp))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
        except ValueError:
            return 0.0
        return max((datetime.now(UTC) - dt).total_seconds() / 86400, 0.0)
