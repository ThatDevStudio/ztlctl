"""ExportService — markdown, indexes, and graph export.

Extends BaseService (operates on existing vault).
"""

from __future__ import annotations

import json
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from sqlalchemy import select

from ztlctl.domain.content import parse_frontmatter
from ztlctl.infrastructure.database.schema import node_tags, nodes
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceResult
from ztlctl.services.telemetry import traced

if TYPE_CHECKING:
    from sqlalchemy import Row


ArchivedMode = Literal["include", "exclude", "only"]


@dataclass(frozen=True)
class ExportFilters:
    """Optional filters applied to export operations."""

    content_type: str | None = None
    status: str | None = None
    tag: str | None = None
    topic: str | None = None
    since: str | None = None
    archived: ArchivedMode | None = None

    def to_dict(self) -> dict[str, str]:
        """Return a normalized user-facing payload for applied filters."""
        data: dict[str, str] = {}
        if self.content_type is not None:
            data["type"] = self.content_type
        if self.status is not None:
            data["status"] = self.status
        if self.tag is not None:
            data["tag"] = self.tag
        if self.topic is not None:
            data["topic"] = self.topic
        if self.since is not None:
            data["since"] = self.since
        if self.archived is not None:
            data["archived"] = self.archived
        return data


def _has_filters(filters: ExportFilters | None) -> bool:
    """Return True when any export filter is active."""
    return filters is not None and any(
        value is not None
        for value in (
            filters.content_type,
            filters.status,
            filters.tag,
            filters.topic,
            filters.since,
            filters.archived,
        )
    )


class ExportService(BaseService):
    """Export vault content in various portable formats."""

    @traced
    def export_markdown(
        self,
        output_dir: Path,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Copy all content files to *output_dir*, preserving relative paths.

        Walks notes/ and ops/ via find_content_files(), copies each to the
        output directory with the same relative path structure.
        """
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []

        from ztlctl.infrastructure.filesystem import find_content_files

        content_files = find_content_files(self._vault.root)
        file_count = 0

        for src_path in content_files:
            if _has_filters(filters):
                try:
                    frontmatter, _body = parse_frontmatter(src_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    warnings.append(f"Skipped {src_path.relative_to(self._vault.root)}: {exc}")
                    continue
                if not frontmatter:
                    warnings.append(
                        f"Skipped {src_path.relative_to(self._vault.root)}:"
                        " missing markdown frontmatter"
                    )
                    continue

                metadata = {
                    "type": str(frontmatter.get("type", "note")),
                    "status": str(frontmatter.get("status", "draft")),
                    "topic": self._normalize_optional(frontmatter.get("topic")),
                    "tags": self._normalize_tags(frontmatter.get("tags")),
                    "modified": str(frontmatter.get("modified", frontmatter.get("created", ""))),
                    "archived": frontmatter.get("archived"),
                }
                if not self._matches_metadata(
                    metadata,
                    filters,
                    default_archived_mode="include",
                ):
                    continue

            rel = src_path.relative_to(self._vault.root)
            dest = output_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)
            file_count += 1

        payload: dict[str, Any] = {
            "output_dir": str(output_dir),
            "file_count": file_count,
        }
        if filters is not None and _has_filters(filters):
            payload["filters"] = filters.to_dict()

        return ServiceResult(
            ok=True,
            op="export_markdown",
            data=payload,
            warnings=warnings,
        )

    @traced
    def export_indexes(
        self,
        output_dir: Path,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Generate index files grouped by type and topic.

        Creates:
        - index.md — master index with counts
        - by-type/{type}.md — per-type listings
        - by-topic/{topic}.md — per-topic listings
        """
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        rows = self._select_filtered_node_rows(filters, default_archived_mode="exclude")
        node_ids = [str(row.id) for row in rows]

        with self._vault.engine.connect() as conn:
            if node_ids:
                tag_rows = conn.execute(
                    select(node_tags.c.node_id, node_tags.c.tag).where(
                        node_tags.c.node_id.in_(node_ids)
                    )
                ).fetchall()
            else:
                tag_rows = []

        # Build lookup structures
        by_type: dict[str, list[dict[str, str]]] = {}
        by_topic: dict[str, list[dict[str, str]]] = {}
        tag_map: dict[str, list[str]] = {}
        type_counts = Counter(str(row.type) for row in rows)

        for row in tag_rows:
            tag_map.setdefault(row.node_id, []).append(row.tag)

        for row in rows:
            entry = {
                "id": row.id,
                "title": row.title,
                "type": row.type,
                "status": row.status,
            }
            by_type.setdefault(row.type, []).append(entry)
            if row.topic:
                by_topic.setdefault(row.topic, []).append(entry)

        files_created: list[str] = []

        # Master index
        lines = ["# Vault Index\n"]
        for content_type, count in sorted(type_counts.items()):
            lines.append(f"- **{content_type}**: {count}")
        lines.append(f"\nTotal: {len(rows)} items\n")

        if by_type:
            lines.append("\n## By Type\n")
            for t in sorted(by_type):
                lines.append(f"- [{t}](by-type/{t}.md) ({len(by_type[t])})")

        if by_topic:
            lines.append("\n## By Topic\n")
            for t in sorted(by_topic):
                lines.append(f"- [{t}](by-topic/{t}.md) ({len(by_topic[t])})")

        (output_dir / "index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        files_created.append("index.md")

        # Per-type indexes
        type_dir = output_dir / "by-type"
        type_dir.mkdir(exist_ok=True)
        for content_type, items in sorted(by_type.items()):
            type_lines = [f"# {content_type.title()}\n"]
            for item in items:
                tags = tag_map.get(item["id"], [])
                tag_str = f" — {', '.join(tags)}" if tags else ""
                type_lines.append(f"- [[{item['id']}]] {item['title']} ({item['status']}){tag_str}")
            (type_dir / f"{content_type}.md").write_text(
                "\n".join(type_lines) + "\n", encoding="utf-8"
            )
            files_created.append(f"by-type/{content_type}.md")

        # Per-topic indexes
        topic_dir = output_dir / "by-topic"
        topic_dir.mkdir(exist_ok=True)
        for topic, items in sorted(by_topic.items()):
            topic_lines = [f"# {topic.title()}\n"]
            for item in items:
                topic_lines.append(
                    f"- [[{item['id']}]] {item['title']} ({item['type']}, {item['status']})"
                )
            (topic_dir / f"{topic}.md").write_text("\n".join(topic_lines) + "\n", encoding="utf-8")
            files_created.append(f"by-topic/{topic}.md")

        payload: dict[str, Any] = {
            "output_dir": str(output_dir),
            "files_created": files_created,
            "node_count": len(rows),
        }
        if filters is not None and _has_filters(filters):
            payload["filters"] = filters.to_dict()

        return ServiceResult(
            ok=True,
            op="export_indexes",
            data=payload,
        )

    @traced
    def export_graph(
        self,
        *,
        fmt: str = "dot",
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Export the vault's knowledge graph.

        Formats:
        - ``dot`` — Graphviz DOT language
        - ``json`` — D3-compatible ``{"nodes": [...], "links": [...]}``

        Returns the content as a string in ``data["content"]``.
        """
        g = self._vault.graph.graph
        if _has_filters(filters):
            import networkx as nx

            node_ids = {
                str(row.id)
                for row in self._select_filtered_node_rows(filters, default_archived_mode="include")
            }
            graph_to_export: Any = g.subgraph(node_ids).copy() if node_ids else nx.DiGraph()
        else:
            graph_to_export = g

        if fmt == "dot":
            content = self._to_dot(graph_to_export)
        elif fmt == "json":
            content = self._to_d3_json(graph_to_export)
        else:
            from ztlctl.services.result import ServiceError

            return ServiceResult(
                ok=False,
                op="export_graph",
                error=ServiceError(
                    code="INVALID_FORMAT",
                    message=f"Unknown graph format: {fmt}",
                    detail={"format": fmt, "valid": ["dot", "json"]},
                ),
            )

        payload: dict[str, Any] = {
            "format": fmt,
            "content": content,
            "node_count": graph_to_export.number_of_nodes(),
            "edge_count": graph_to_export.number_of_edges(),
        }
        if filters is not None and _has_filters(filters):
            payload["filters"] = filters.to_dict()

        return ServiceResult(
            ok=True,
            op="export_graph",
            data=payload,
        )

    @traced
    def export_dashboard(
        self,
        output_dir: Path,
        *,
        viewer: Literal["obsidian", "vanilla"] = "obsidian",
    ) -> ServiceResult:
        """Export a viewer-friendly dashboard plus review and dossier artifacts."""
        from ztlctl.services.query import QueryService

        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        topics_dir = output_dir / "topics"
        topics_dir.mkdir(parents=True, exist_ok=True)

        query = QueryService(self._vault)
        export_cfg = self._vault.settings.exports.dashboard
        work_queue_result = query.work_queue()
        decisions_result = query.list_items(
            content_type="note",
            subtype="decision",
            sort="recency",
            limit=10,
        )
        review_result = query.vault_review(top=10)
        recent_items_result = query.list_items(sort="recency", limit=25)

        work_queue = work_queue_result.data.get("items", []) if work_queue_result.ok else []
        recent_decisions = decisions_result.data.get("items", []) if decisions_result.ok else []
        review_data = review_result.data if review_result.ok else {}
        garden_backlog = [
            *review_data.get("stale_seeds", []),
            *review_data.get("orphan_notes", []),
        ]

        seen_backlog: set[str] = set()
        deduped_backlog: list[dict[str, Any]] = []
        for item in garden_backlog:
            item_id = str(item.get("id", ""))
            if item_id in seen_backlog:
                continue
            seen_backlog.add(item_id)
            deduped_backlog.append(item)
        garden_backlog = deduped_backlog

        recent_items = recent_items_result.data.get("items", []) if recent_items_result.ok else []
        by_topic = Counter(
            str(item.get("topic") or "unscoped")
            for item in recent_items
            if str(item.get("topic") or "").strip() or item.get("topic") is None
        )
        topic_summaries = [
            {"topic": topic, "count": count}
            for topic, count in sorted(by_topic.items(), key=lambda item: (-item[1], item[0]))
        ]
        dossier_topics = [
            str(summary["topic"]) for summary in topic_summaries if summary["topic"] != "unscoped"
        ][: export_cfg.topic_dossier_limit]

        files_created: list[str] = []

        dashboard_path = output_dir / "dashboard.md"
        dashboard_sections = [
            "# ztlctl Dashboard",
            "",
            f"- Viewer mode: {viewer}",
            "- Focus: capture and synthesis feed the enrichment backlog.",
        ]
        if export_cfg.include_work_queue:
            dashboard_sections.extend(
                [
                    "",
                    "## Work Queue",
                    *self._dashboard_lines(
                        work_queue[:10], viewer=viewer, empty="No active tasks."
                    ),
                ]
            )
        if export_cfg.include_recent_decisions:
            dashboard_sections.extend(
                [
                    "",
                    "## Recent Decisions",
                    *self._dashboard_lines(
                        recent_decisions[:10],
                        viewer=viewer,
                        empty="No recent decisions.",
                    ),
                ]
            )
        if export_cfg.include_garden_backlog:
            dashboard_sections.extend(
                [
                    "",
                    "## Garden Backlog",
                    *self._dashboard_lines(
                        garden_backlog[:10],
                        viewer=viewer,
                        empty="No garden backlog items.",
                    ),
                ]
            )
        dashboard_sections.extend(
            [
                "",
                "## Review Queue",
                f"- Gaps: {len(review_data.get('gaps', []))}",
                f"- Bridges: {len(review_data.get('bridges', []))}",
                f"- Stale Seeds: {len(review_data.get('stale_seeds', []))}",
                f"- Orphan Notes: {len(review_data.get('orphan_notes', []))}",
            ]
        )
        topic_lines = [
            f"- {summary['topic']}: {summary['count']}" for summary in topic_summaries[:10]
        ] or ["- No recent topic activity."]
        dashboard_sections.extend(["", "## Topic Review Summary", *topic_lines])
        dossier_lines = [
            f"- {self._topic_dossier_link(topic, viewer=viewer)}" for topic in dossier_topics
        ] or ["- No scoped topics available for dossier export."]
        dashboard_sections.extend(["", "## Topic Dossiers", *dossier_lines])
        dashboard_path.write_text("\n".join(dashboard_sections) + "\n", encoding="utf-8")
        files_created.append("dashboard.md")

        if export_cfg.include_work_queue:
            (output_dir / "work-queue.json").write_text(
                json.dumps({"items": work_queue}, indent=2) + "\n",
                encoding="utf-8",
            )
            files_created.append("work-queue.json")
        if export_cfg.include_recent_decisions:
            (output_dir / "recent-decisions.json").write_text(
                json.dumps({"items": recent_decisions}, indent=2) + "\n",
                encoding="utf-8",
            )
            files_created.append("recent-decisions.json")
        if export_cfg.include_garden_backlog:
            (output_dir / "garden-backlog.json").write_text(
                json.dumps({"items": garden_backlog}, indent=2) + "\n",
                encoding="utf-8",
            )
            files_created.append("garden-backlog.json")

        (output_dir / "review-queue.json").write_text(
            json.dumps(review_data, indent=2) + "\n",
            encoding="utf-8",
        )
        files_created.append("review-queue.json")

        (output_dir / "decision-queue.json").write_text(
            json.dumps({"items": recent_decisions, "work_queue": work_queue}, indent=2) + "\n",
            encoding="utf-8",
        )
        files_created.append("decision-queue.json")

        (output_dir / "topic-review-summary.json").write_text(
            json.dumps({"items": topic_summaries}, indent=2) + "\n",
            encoding="utf-8",
        )
        files_created.append("topic-review-summary.json")

        for topic in dossier_topics:
            packet_result = query.topic_packet(topic, mode="review", budget=5000)
            packet = packet_result.data if packet_result.ok else {"topic": topic}
            slug = self._topic_slug(topic)
            dossier_md = topics_dir / f"{slug}.md"
            dossier_json = topics_dir / f"{slug}.json"
            dossier_md.write_text(
                self._topic_dossier_markdown(topic, packet, viewer=viewer),
                encoding="utf-8",
            )
            dossier_json.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
            files_created.append(str(dossier_md.relative_to(output_dir)))
            files_created.append(str(dossier_json.relative_to(output_dir)))

        return ServiceResult(
            ok=True,
            op="export_dashboard",
            data={
                "output_dir": str(output_dir),
                "viewer": viewer,
                "files_created": files_created,
            },
        )

    # ── Private helpers ───────────────────────────────────────────────

    @staticmethod
    def _dashboard_lines(
        items: list[dict[str, Any]],
        *,
        viewer: Literal["obsidian", "vanilla"],
        empty: str,
    ) -> list[str]:
        """Render one dashboard section according to the target viewer."""
        if not items:
            return [f"- {empty}"]

        lines: list[str] = []
        for item in items:
            item_id = str(item.get("id", ""))
            title = str(item.get("title", item_id))
            status = str(item.get("status", ""))
            topic = str(item.get("topic") or "")
            label = ExportService._viewer_item_label(item_id, title, viewer=viewer)
            suffix_parts = [part for part in (status, topic) if part]
            suffix = f" ({', '.join(suffix_parts)})" if suffix_parts else ""
            lines.append(f"- {label}{suffix}")
        return lines

    @staticmethod
    def _viewer_item_label(
        item_id: str,
        title: str,
        *,
        viewer: Literal["obsidian", "vanilla"],
    ) -> str:
        """Render an item label appropriate for the target viewer."""
        if viewer == "obsidian":
            return f"[[{item_id}]] {title}"
        return f"{item_id} - {title}"

    @staticmethod
    def _topic_slug(topic: str) -> str:
        """Normalize a topic into a filename-safe slug."""
        safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in topic.strip())
        while "--" in safe:
            safe = safe.replace("--", "-")
        return safe.strip("-") or "topic"

    @classmethod
    def _topic_dossier_link(
        cls,
        topic: str,
        *,
        viewer: Literal["obsidian", "vanilla"],
    ) -> str:
        """Render a dashboard link to a topic dossier."""
        slug = cls._topic_slug(topic)
        if viewer == "obsidian":
            return f"[[topics/{slug}|{topic} dossier]]"
        return f"[{topic} dossier](topics/{slug}.md)"

    @classmethod
    def _topic_dossier_markdown(
        cls,
        topic: str,
        packet: dict[str, Any],
        *,
        viewer: Literal["obsidian", "vanilla"],
    ) -> str:
        """Render a markdown topic dossier from a packet payload."""
        lines = [
            f"# Topic Dossier: {topic}",
            "",
            f"- Mode: {packet.get('mode', 'review')}",
            f"- Budget: {packet.get('budget', 0)}",
            "",
            "## Suggested Actions",
        ]
        actions = packet.get("suggested_actions", [])
        if actions:
            for action in actions[:8]:
                lines.append(f"- {action.get('title')}: {action.get('rationale')}")
        else:
            lines.append("- No suggested actions.")

        lines.extend(["", "## Evidence"])
        evidence = packet.get("evidence", [])
        if evidence:
            for item in evidence[:10]:
                locator = str(item.get("locator") or "").strip()
                suffix = f" [{locator}]" if locator else ""
                lines.append(f"- {item.get('title')}: {item.get('text')}{suffix}")
        else:
            lines.append("- No evidence excerpts.")

        citations = cls._packet_citations(packet)
        lines.extend(["", "## Citations"])
        if citations:
            for citation in citations[:10]:
                lines.append(f"- {citation}")
        else:
            lines.append("- No citations captured.")

        artifacts = cls._packet_artifacts(packet)
        lines.extend(["", "## Source Artifacts"])
        if artifacts:
            for artifact in artifacts[:10]:
                label = artifact.get("label") or artifact.get("kind") or "artifact"
                uri = str(artifact.get("uri") or "").strip()
                kind = str(artifact.get("kind") or "").strip()
                suffix = f" ({kind})" if kind else ""
                if uri:
                    lines.append(f"- {label}{suffix}: {uri}")
                else:
                    lines.append(f"- {label}{suffix}")
        else:
            lines.append("- No source artifacts captured.")

        lines.extend(["", "## Stale Items"])
        stale_items = packet.get("stale_items", [])
        if stale_items:
            for item in stale_items[:10]:
                label = cls._viewer_item_label(
                    str(item.get("id", "")),
                    str(item.get("title", item.get("id", ""))),
                    viewer=viewer,
                )
                lines.append(f"- {label}")
        else:
            lines.append("- No stale items.")

        lines.extend(["", "## Bridge Candidates"])
        bridge_candidates = packet.get("bridge_candidates", [])
        if bridge_candidates:
            for item in bridge_candidates[:10]:
                label = cls._viewer_item_label(
                    str(item.get("id", "")),
                    str(item.get("title", item.get("id", ""))),
                    viewer=viewer,
                )
                lines.append(f"- {label}")
        else:
            lines.append("- No bridge candidates.")

        return "\n".join(lines).strip() + "\n"

    @staticmethod
    def _packet_citations(packet: dict[str, Any]) -> list[str]:
        """Collect unique citation lines from packet items."""
        seen: set[str] = set()
        lines: list[str] = []
        for collection_name in ("references", "notes", "decisions"):
            for item in packet.get(collection_name, []):
                for citation in item.get("citations", []):
                    text = str(citation).strip()
                    if not text or text in seen:
                        continue
                    seen.add(text)
                    lines.append(text)
        for provenance_lines in packet.get("provenance_map", {}).values():
            if not isinstance(provenance_lines, list):
                continue
            for entry in provenance_lines:
                text = str(entry).strip()
                if not text.startswith("Citation: "):
                    continue
                citation = text.removeprefix("Citation: ").strip()
                if citation and citation not in seen:
                    seen.add(citation)
                    lines.append(citation)
        return lines

    @staticmethod
    def _packet_artifacts(packet: dict[str, Any]) -> list[dict[str, Any]]:
        """Collect unique source artifact payloads from packet items."""
        seen: set[tuple[str, str, str]] = set()
        items: list[dict[str, Any]] = []
        for collection_name in ("references", "notes", "decisions"):
            for item in packet.get(collection_name, []):
                for artifact in item.get("artifacts", []):
                    if not isinstance(artifact, dict):
                        continue
                    key = (
                        str(artifact.get("kind") or ""),
                        str(artifact.get("label") or ""),
                        str(artifact.get("uri") or ""),
                    )
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append(dict(artifact))
        for provenance_lines in packet.get("provenance_map", {}).values():
            if not isinstance(provenance_lines, list):
                continue
            for entry in provenance_lines:
                text = str(entry).strip()
                if not text.startswith("Artifact "):
                    continue
                body = text.removeprefix("Artifact ").strip()
                label_part, _, uri = body.partition(": ")
                label = label_part
                kind = ""
                if label_part.endswith(")") and " (" in label_part:
                    label, _, kind_part = label_part.rpartition(" (")
                    kind = kind_part[:-1]
                key = (kind, label, uri)
                if key in seen:
                    continue
                seen.add(key)
                items.append(
                    {
                        "kind": kind or None,
                        "label": label or None,
                        "uri": uri or None,
                    }
                )
        return items

    def _select_filtered_node_rows(
        self,
        filters: ExportFilters | None,
        *,
        default_archived_mode: ArchivedMode,
    ) -> list[Row[Any]]:
        """Fetch node rows matching export filters."""
        active = filters or ExportFilters()
        archived_mode = active.archived or default_archived_mode

        stmt = select(
            nodes.c.id,
            nodes.c.title,
            nodes.c.type,
            nodes.c.status,
            nodes.c.topic,
            nodes.c.path,
            nodes.c.archived,
            nodes.c.created,
            nodes.c.modified,
        )

        if active.tag is not None:
            stmt = stmt.join(node_tags, node_tags.c.node_id == nodes.c.id).where(
                node_tags.c.tag == active.tag
            )

        if archived_mode == "exclude":
            stmt = stmt.where(nodes.c.archived == 0)
        elif archived_mode == "only":
            stmt = stmt.where(nodes.c.archived == 1)

        if active.content_type is not None:
            stmt = stmt.where(nodes.c.type == active.content_type)
        if active.status is not None:
            stmt = stmt.where(nodes.c.status == active.status)
        if active.topic is not None:
            stmt = stmt.where(nodes.c.topic == active.topic)
        if active.since is not None:
            stmt = stmt.where(nodes.c.modified >= active.since)

        stmt = stmt.order_by(nodes.c.path).distinct()

        with self._vault.engine.connect() as conn:
            return list(conn.execute(stmt).fetchall())

    def _matches_metadata(
        self,
        metadata: dict[str, Any],
        filters: ExportFilters | None,
        *,
        default_archived_mode: ArchivedMode,
    ) -> bool:
        """Return True when file metadata satisfies the given filters."""
        active = filters or ExportFilters()
        archived_mode = active.archived or default_archived_mode
        archived = self._is_archived(metadata.get("archived"))

        if archived_mode == "exclude" and archived:
            return False
        if archived_mode == "only" and not archived:
            return False

        if active.content_type is not None and metadata.get("type") != active.content_type:
            return False
        if active.status is not None and metadata.get("status") != active.status:
            return False
        if active.topic is not None and metadata.get("topic") != active.topic:
            return False
        if active.tag is not None and active.tag not in self._normalize_tags(metadata.get("tags")):
            return False
        if active.since is not None:
            modified = str(metadata.get("modified", ""))
            if not modified or modified < active.since:
                return False
        return True

    @staticmethod
    def _is_archived(value: Any) -> bool:
        """Normalize frontmatter/db archived values to bool."""
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    @staticmethod
    def _normalize_optional(value: Any) -> str | None:
        """Normalize optional scalar metadata."""
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _normalize_tags(value: Any) -> list[str]:
        """Normalize frontmatter tags to a list of strings."""
        if isinstance(value, list):
            return [str(tag) for tag in value]
        if value is None:
            return []
        return [str(value)]

    @staticmethod
    def _to_dot(g: object) -> str:
        """Generate Graphviz DOT notation from a NetworkX DiGraph."""
        import networkx as nx

        assert isinstance(g, nx.DiGraph)
        lines = ["digraph vault {", "  rankdir=LR;", "  node [shape=box];"]

        for node_id, attrs in g.nodes(data=True):
            label = attrs.get("title", node_id)
            ntype = attrs.get("type", "")
            # Escape quotes in labels
            safe_label = str(label).replace('"', '\\"')
            lines.append(f'  "{node_id}" [label="{safe_label}" type="{ntype}"];')

        for src, tgt, attrs in g.edges(data=True):
            edge_type = attrs.get("edge_type", "relates")
            lines.append(f'  "{src}" -> "{tgt}" [label="{edge_type}"];')

        lines.append("}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _to_d3_json(g: object) -> str:
        """Generate D3-compatible JSON from a NetworkX DiGraph."""
        import networkx as nx

        assert isinstance(g, nx.DiGraph)
        d3_nodes = []
        for node_id, attrs in g.nodes(data=True):
            d3_nodes.append(
                {
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "type": attrs.get("type", ""),
                }
            )

        d3_links = []
        for src, tgt, attrs in g.edges(data=True):
            d3_links.append(
                {
                    "source": src,
                    "target": tgt,
                    "edge_type": attrs.get("edge_type", "relates"),
                }
            )

        return json.dumps({"nodes": d3_nodes, "links": d3_links}, indent=2) + "\n"
