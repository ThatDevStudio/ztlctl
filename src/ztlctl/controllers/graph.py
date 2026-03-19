"""GraphController — orchestration wrapper for GraphService."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class GraphController(BaseController):
    """Thin wrapper over GraphService. All methods return ServiceResult."""

    def related(
        self,
        content_id: str,
        *,
        depth: int = 2,
        top: int = 20,
    ) -> ServiceResult:
        """Find related content via spreading activation (BFS with decay)."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).related(content_id, depth=depth, top=top)

    def themes(self) -> ServiceResult:
        """Discover topic clusters via community detection."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).themes()

    def rank(self, *, top: int = 20) -> ServiceResult:
        """Identify important nodes via PageRank."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).rank(top=top)

    def path(self, source_id: str, target_id: str) -> ServiceResult:
        """Find shortest connection chain between two nodes."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).path(source_id, target_id)

    def gaps(self, *, top: int = 20) -> ServiceResult:
        """Find structural holes — nodes with high constraint."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).gaps(top=top)

    def bridges(self, *, top: int = 20) -> ServiceResult:
        """Find bridge nodes via betweenness centrality."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).bridges(top=top)

    def unlink(self, source_id: str, target_id: str, *, both: bool = False) -> ServiceResult:
        """Remove links from source_id to target_id."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).unlink(source_id, target_id, both=both)

    def materialize_metrics(self) -> ServiceResult:
        """Compute and store graph metrics in the nodes table."""
        from ztlctl.services.graph import GraphService

        return GraphService(self._vault).materialize_metrics()
