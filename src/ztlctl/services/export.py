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

    # ── Private helpers ───────────────────────────────────────────────

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
