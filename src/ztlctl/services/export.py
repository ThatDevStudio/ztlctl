"""ExportService — markdown, indexes, and graph export.

Extends BaseService (operates on existing vault).
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from sqlalchemy import func, select

from ztlctl.infrastructure.database.schema import node_tags, nodes
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceResult
from ztlctl.services.telemetry import traced


class ExportService(BaseService):
    """Export vault content in various portable formats."""

    @traced
    def export_markdown(self, output_dir: Path) -> ServiceResult:
        """Copy all content files to *output_dir*, preserving relative paths.

        Walks notes/ and ops/ via find_content_files(), copies each to the
        output directory with the same relative path structure.
        """
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        from ztlctl.infrastructure.filesystem import find_content_files

        content_files = find_content_files(self._vault.root)
        file_count = 0

        for src_path in content_files:
            rel = src_path.relative_to(self._vault.root)
            dest = output_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)
            file_count += 1

        return ServiceResult(
            ok=True,
            op="export_markdown",
            data={
                "output_dir": str(output_dir),
                "file_count": file_count,
            },
        )

    @traced
    def export_indexes(self, output_dir: Path) -> ServiceResult:
        """Generate index files grouped by type and topic.

        Creates:
        - index.md — master index with counts
        - by-type/{type}.md — per-type listings
        - by-topic/{topic}.md — per-topic listings
        """
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        with self._vault.engine.connect() as conn:
            # Fetch all non-archived nodes
            rows = conn.execute(
                select(
                    nodes.c.id,
                    nodes.c.title,
                    nodes.c.type,
                    nodes.c.status,
                    nodes.c.topic,
                ).where(nodes.c.archived == 0)
            ).fetchall()

            # Count by type
            type_counts = conn.execute(
                select(nodes.c.type, func.count())
                .where(nodes.c.archived == 0)
                .group_by(nodes.c.type)
            ).fetchall()

            # Fetch tags for index
            tag_rows = conn.execute(select(node_tags.c.node_id, node_tags.c.tag)).fetchall()

        # Build lookup structures
        by_type: dict[str, list[dict[str, str]]] = {}
        by_topic: dict[str, list[dict[str, str]]] = {}
        tag_map: dict[str, list[str]] = {}

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
        for tc in type_counts:
            lines.append(f"- **{tc[0]}**: {tc[1]}")
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

        return ServiceResult(
            ok=True,
            op="export_indexes",
            data={
                "output_dir": str(output_dir),
                "files_created": files_created,
                "node_count": len(rows),
            },
        )

    @traced
    def export_graph(self, *, fmt: str = "dot") -> ServiceResult:
        """Export the vault's knowledge graph.

        Formats:
        - ``dot`` — Graphviz DOT language
        - ``json`` — D3-compatible ``{"nodes": [...], "links": [...]}``

        Returns the content as a string in ``data["content"]``.
        """
        g = self._vault.graph.graph

        if fmt == "dot":
            content = self._to_dot(g)
        elif fmt == "json":
            content = self._to_d3_json(g)
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

        return ServiceResult(
            ok=True,
            op="export_graph",
            data={
                "format": fmt,
                "content": content,
                "node_count": g.number_of_nodes(),
                "edge_count": g.number_of_edges(),
            },
        )

    # ── Private helpers ───────────────────────────────────────────────

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
