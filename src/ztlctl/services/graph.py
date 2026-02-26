"""GraphService — graph traversal and analysis algorithms.

Six read-only algorithms via NetworkX computed on the lazy-built DiGraph,
plus ``unlink()`` for removing specific links between nodes.
Uses ``self._vault.graph.graph`` to access the graph (triggers lazy build).
(DESIGN.md Section 3, 5)
"""

from __future__ import annotations

import math
import re
from collections import deque
from typing import Any

import networkx as nx

from ztlctl.infrastructure.database.schema import edges, nodes
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.telemetry import trace_span, traced


class GraphService(BaseService):
    """Handles graph queries and analysis."""

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_graph_result(op: str, *, key: str = "items") -> ServiceResult:
        """Return an ok result for an empty graph."""
        return ServiceResult(ok=True, op=op, data={"count": 0, key: []})

    # ------------------------------------------------------------------
    # related — spreading activation (BFS with decay)
    # ------------------------------------------------------------------

    @traced
    def related(
        self,
        content_id: str,
        *,
        depth: int = 2,
        top: int = 20,
    ) -> ServiceResult:
        """Find related content via spreading activation (BFS with decay).

        Starting from *content_id*, explores neighbors up to *depth* hops.
        Each hop decays the activation score by 0.5. Treats the graph as
        undirected for traversal (both in-edges and out-edges matter).

        Args:
            content_id: The source node to find related content for.
            depth: Maximum hops from the source (1-5).
            top: Maximum results to return.
        """
        g = self._vault.graph.graph

        if content_id not in g:
            return ServiceResult(
                ok=False,
                op="related",
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"Node '{content_id}' not found in graph",
                ),
            )

        depth = max(1, min(depth, 5))
        decay = 0.5

        # BFS with activation scores on undirected view.
        # Track both score and depth per node during traversal.
        scores: dict[str, float] = {}
        depths: dict[str, int] = {}
        visited: set[str] = {content_id}
        queue: deque[tuple[str, int, float]] = deque()

        # Seed neighbors (both directions)
        for neighbor in nx.all_neighbors(g, content_id):
            if neighbor not in visited:
                queue.append((neighbor, 1, 1.0))
                visited.add(neighbor)

        while queue:
            node, d, activation = queue.popleft()
            if activation > scores.get(node, 0.0):
                scores[node] = activation
                depths[node] = d
            if d < depth:
                for neighbor in nx.all_neighbors(g, node):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, d + 1, activation * decay))

        # Sort by score descending, take top N
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top]

        items: list[dict[str, Any]] = []
        for node_id, score in ranked:
            attrs = g.nodes[node_id]
            items.append(
                {
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "type": attrs.get("type", ""),
                    "score": round(score, 4),
                    "depth": depths[node_id],
                }
            )

        return ServiceResult(
            ok=True,
            op="related",
            data={
                "source_id": content_id,
                "count": len(items),
                "items": items,
            },
        )

    # ------------------------------------------------------------------
    # themes — community detection (Leiden → Louvain fallback)
    # ------------------------------------------------------------------

    @traced
    def themes(self) -> ServiceResult:
        """Discover topic clusters via community detection.

        Tries leidenalg first (higher quality), falls back to NetworkX
        Louvain if leidenalg is not installed.
        """
        with trace_span("build_graph") as span:
            g = self._vault.graph.graph
            if span:
                span.annotate("nodes", g.number_of_nodes())
                span.annotate("edges", g.number_of_edges())

        if g.number_of_nodes() == 0:
            return self._empty_graph_result("themes", key="communities")

        # Work on undirected view for community detection
        ug = g.to_undirected(as_view=True)

        warnings: list[str] = []
        partition: dict[str, int] = {}

        with trace_span("community_detection"):
            try:
                partition = self._leiden_communities(ug)
            except ImportError:
                warnings.append("leidenalg not installed, using Louvain fallback")
                communities = nx.community.louvain_communities(ug, seed=42)
                partition = self._sets_to_partition(communities)

        # Group nodes by community
        comm_groups: dict[int, list[dict[str, Any]]] = {}
        for node_id, comm_id in partition.items():
            attrs = g.nodes.get(node_id, {})
            entry = {
                "id": node_id,
                "title": attrs.get("title", ""),
                "type": attrs.get("type", ""),
            }
            comm_groups.setdefault(comm_id, []).append(entry)

        # Build output — sort communities by size (largest first)
        community_list: list[dict[str, Any]] = []
        for comm_id, members in sorted(comm_groups.items(), key=lambda x: len(x[1]), reverse=True):
            community_list.append(
                {
                    "community_id": comm_id,
                    "size": len(members),
                    "members": members,
                }
            )

        return ServiceResult(
            ok=True,
            op="themes",
            data={"count": len(community_list), "communities": community_list},
            warnings=warnings,
        )

    @staticmethod
    def _leiden_communities(ug: nx.Graph[str]) -> dict[str, int]:
        """Run Leiden community detection via leidenalg + igraph."""
        import igraph as ig  # type: ignore[import-not-found]
        import leidenalg  # type: ignore[import-not-found]

        # Convert NetworkX → igraph
        mapping = {node: i for i, node in enumerate(ug.nodes())}
        ig_graph = ig.Graph(
            n=len(mapping),
            edges=[(mapping[u], mapping[v]) for u, v in ug.edges()],
            directed=False,
        )

        result = leidenalg.find_partition(ig_graph, leidenalg.ModularityVertexPartition)
        reverse_mapping = {i: node for node, i in mapping.items()}
        return {reverse_mapping[i]: comm for i, comm in enumerate(result.membership)}

    @staticmethod
    def _sets_to_partition(communities: Any) -> dict[str, int]:
        """Convert Louvain output (frozensets) to node->community_id mapping."""
        partition: dict[str, int] = {}
        for comm_id, members in enumerate(communities):
            for node_id in members:
                partition[node_id] = comm_id
        return partition

    # ------------------------------------------------------------------
    # rank — PageRank importance scoring
    # ------------------------------------------------------------------

    @traced
    def rank(self, *, top: int = 20) -> ServiceResult:
        """Identify important nodes via PageRank.

        Args:
            top: Maximum number of top-ranked nodes to return.
        """
        g = self._vault.graph.graph

        if g.number_of_nodes() == 0:
            return self._empty_graph_result("rank")

        scores = nx.pagerank(g)

        # Sort by PageRank score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top]

        items: list[dict[str, Any]] = []
        for node_id, score in ranked:
            attrs = g.nodes[node_id]
            items.append(
                {
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "type": attrs.get("type", ""),
                    "score": round(score, 6),
                }
            )

        return ServiceResult(
            ok=True,
            op="rank",
            data={"count": len(items), "items": items},
        )

    # ------------------------------------------------------------------
    # path — shortest connection chain between two nodes
    # ------------------------------------------------------------------

    @traced
    def path(self, source_id: str, target_id: str) -> ServiceResult:
        """Find shortest connection chain between two nodes.

        Uses undirected view so that both link directions count.

        Args:
            source_id: Starting node ID.
            target_id: Destination node ID.
        """
        g = self._vault.graph.graph

        for nid, label in [(source_id, "source"), (target_id, "target")]:
            if nid not in g:
                return ServiceResult(
                    ok=False,
                    op="path",
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"Node '{nid}' ({label}) not found in graph",
                    ),
                )

        try:
            ug = g.to_undirected(as_view=True)
            node_path = nx.shortest_path(ug, source_id, target_id)
        except nx.NetworkXNoPath:
            return ServiceResult(
                ok=False,
                op="path",
                error=ServiceError(
                    code="NO_PATH",
                    message=f"No path between '{source_id}' and '{target_id}'",
                ),
            )

        steps: list[dict[str, Any]] = []
        for node_id in node_path:
            attrs = g.nodes[node_id]
            steps.append(
                {
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "type": attrs.get("type", ""),
                }
            )

        return ServiceResult(
            ok=True,
            op="path",
            data={
                "source_id": source_id,
                "target_id": target_id,
                "length": len(node_path) - 1,
                "steps": steps,
            },
        )

    # ------------------------------------------------------------------
    # gaps — structural holes via constraint
    # ------------------------------------------------------------------

    @traced
    def gaps(self, *, top: int = 20) -> ServiceResult:
        """Find structural holes — nodes with high constraint.

        High constraint nodes are tightly embedded in their local cluster
        with few connections outside it. These represent opportunities
        for new cross-cutting links.

        Args:
            top: Maximum results to return.
        """
        g = self._vault.graph.graph

        if g.number_of_nodes() == 0:
            return self._empty_graph_result("gaps")

        ug = g.to_undirected(as_view=True)
        constraints = nx.constraint(ug)

        # Filter out NaN/Inf (isolated or degree-1 nodes)
        valid: list[tuple[str, float]] = [
            (n, c) for n, c in constraints.items() if math.isfinite(c)
        ]

        # Sort by constraint descending (highest = most constrained = structural hole)
        valid.sort(key=lambda x: x[1], reverse=True)
        valid = valid[:top]

        items: list[dict[str, Any]] = []
        for node_id, constraint_val in valid:
            attrs = g.nodes[node_id]
            items.append(
                {
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "type": attrs.get("type", ""),
                    "constraint": round(constraint_val, 6),
                }
            )

        return ServiceResult(
            ok=True,
            op="gaps",
            data={"count": len(items), "items": items},
        )

    # ------------------------------------------------------------------
    # bridges — betweenness centrality
    # ------------------------------------------------------------------

    @traced
    def bridges(self, *, top: int = 20) -> ServiceResult:
        """Find bridge nodes via betweenness centrality.

        Bridge nodes have high betweenness — they sit on many shortest
        paths between other nodes, connecting different clusters.

        Args:
            top: Maximum results to return.
        """
        g = self._vault.graph.graph

        if g.number_of_nodes() == 0:
            return self._empty_graph_result("bridges")

        bc = nx.betweenness_centrality(g)

        # Filter to non-zero centrality and sort descending
        nonzero = [(n, c) for n, c in bc.items() if c > 0]
        nonzero.sort(key=lambda x: x[1], reverse=True)
        nonzero = nonzero[:top]

        items: list[dict[str, Any]] = []
        for node_id, centrality in nonzero:
            attrs = g.nodes[node_id]
            items.append(
                {
                    "id": node_id,
                    "title": attrs.get("title", ""),
                    "type": attrs.get("type", ""),
                    "centrality": round(centrality, 6),
                }
            )

        return ServiceResult(
            ok=True,
            op="bridges",
            data={"count": len(items), "items": items},
        )

    # ------------------------------------------------------------------
    # materialize_metrics — persist graph metrics to the nodes table
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # unlink — remove specific links (DESIGN.md Section 5)
    # ------------------------------------------------------------------

    @traced
    def unlink(self, source_id: str, target_id: str) -> ServiceResult:
        """Remove all links between *source_id* and *target_id*.

        Removes edges from DB, frontmatter link entries, and body
        wikilinks. Respects garden note protection (maturity set →
        body not modified). Re-indexes FTS5 if body was changed.
        """
        op = "unlink"
        warnings: list[str] = []

        with self._vault.transaction() as txn:
            # Verify both nodes exist
            source = txn.conn.execute(nodes.select().where(nodes.c.id == source_id)).first()
            if source is None:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"Source node not found: {source_id}",
                    ),
                )

            target = txn.conn.execute(nodes.select().where(nodes.c.id == target_id)).first()
            if target is None:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"Target node not found: {target_id}",
                    ),
                )

            # -- Remove DB edges (both directions) --
            with trace_span("remove_edges") as span:
                result = txn.conn.execute(
                    edges.delete().where(
                        edges.c.source_id == source_id,
                        edges.c.target_id == target_id,
                    )
                )
                removed = result.rowcount

                # Also remove reverse direction
                result_rev = txn.conn.execute(
                    edges.delete().where(
                        edges.c.source_id == target_id,
                        edges.c.target_id == source_id,
                    )
                )
                removed += result_rev.rowcount

                if span:
                    span.annotate("edges_removed", removed)

            if removed == 0:
                return ServiceResult(
                    ok=False,
                    op=op,
                    error=ServiceError(
                        code="NO_LINK",
                        message=f"No link found between {source_id} and {target_id}",
                    ),
                )

            # -- Update source file (frontmatter + body) --
            with trace_span("update_source_file"):
                self._remove_link_from_file(txn, source, target_id, str(target.title), warnings)

            # -- Update target file (reverse frontmatter + body) --
            with trace_span("update_target_file"):
                self._remove_link_from_file(txn, target, source_id, str(source.title), warnings)

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "source_id": source_id,
                "target_id": target_id,
                "edges_removed": removed,
            },
            warnings=warnings,
        )

    def _remove_link_from_file(
        self,
        txn: Any,
        node_row: Any,
        other_id: str,
        other_title: str,
        warnings: list[str],
    ) -> None:
        """Remove references to *other_id* from a node's file content."""
        file_path = self._vault.root / node_row.path
        if not file_path.exists():
            return

        fm, body = txn.read_content(file_path)
        changed = False

        # Remove from frontmatter links
        links: dict[str, list[str]] = fm.get("links", {})
        for edge_type in list(links.keys()):
            targets = links[edge_type]
            if other_id in targets:
                targets.remove(other_id)
                changed = True
            if not targets:
                del links[edge_type]
        if links:
            fm["links"] = links
        elif "links" in fm:
            del fm["links"]

        # Remove body wikilinks (unless garden note)
        maturity = fm.get("maturity")
        if maturity is not None:
            warnings.append(
                f"Body wikilinks preserved for garden note {node_row.id} (maturity={maturity})"
            )
        else:
            # Remove [[other_id]], [[other_id|display]], [[other_title]],
            # [[other_title|display]]
            targets_to_remove = {other_id, other_title}
            pattern = re.compile(
                r"\[\[(" + "|".join(re.escape(t) for t in targets_to_remove) + r")(?:\|[^\]]+)?\]\]"
            )
            new_body = pattern.sub("", body)
            if new_body != body:
                body = new_body
                changed = True

        if changed:
            txn.write_content(file_path, fm, body)
            # Re-index FTS5
            txn.upsert_fts(str(node_row.id), str(node_row.title), body)

    # ------------------------------------------------------------------
    # materialize_metrics — compute and store graph metrics
    # ------------------------------------------------------------------

    @traced
    def materialize_metrics(self) -> ServiceResult:
        """Compute and store graph metrics in the nodes table.

        Computes PageRank, degree_in, degree_out, and betweenness centrality
        via NetworkX and writes the results to the materialized columns
        in the nodes table.
        """
        g = self._vault.graph.graph

        if g.number_of_nodes() == 0:
            return ServiceResult(
                ok=True,
                op="materialize_metrics",
                data={"nodes_updated": 0},
            )

        # Compute metrics
        pageranks = nx.pagerank(g)
        betweenness = nx.betweenness_centrality(g)

        # Compute community assignments (Leiden → Louvain fallback)
        warnings: list[str] = []
        cluster_map: dict[str, int] = {}
        ug = g.to_undirected(as_view=True)
        if ug.number_of_edges() > 0:
            try:
                cluster_map = self._leiden_communities(ug)
            except ImportError:
                warnings.append("leidenalg not installed, using Louvain fallback")
                communities = nx.community.louvain_communities(ug, seed=42)
                cluster_map = self._sets_to_partition(communities)

        updated = 0
        with self._vault.engine.begin() as conn:
            for node_id in g.nodes():
                d_in = g.in_degree(node_id)
                d_out = g.out_degree(node_id)
                pr = pageranks.get(node_id, 0.0)
                bc = betweenness.get(node_id, 0.0)
                cid = cluster_map.get(node_id)

                conn.execute(
                    nodes.update()
                    .where(nodes.c.id == node_id)
                    .values(
                        degree_in=d_in,
                        degree_out=d_out,
                        pagerank=round(pr, 8),
                        betweenness=round(bc, 8),
                        cluster_id=cid,
                    )
                )
                updated += 1

        return ServiceResult(
            ok=True,
            op="materialize_metrics",
            data={"nodes_updated": updated},
            warnings=warnings,
        )
