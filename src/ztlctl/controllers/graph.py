"""GraphController — orchestration wrapper for GraphService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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

        kwargs: dict[str, Any] = {"content_id": content_id, "depth": depth, "top": top}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).related(
                kw["content_id"], depth=kw["depth"], top=kw["top"]
            )

        return self._run_action("related", kwargs, _invoke)

    def themes(self) -> ServiceResult:
        """Discover topic clusters via community detection."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).themes()

        return self._run_action("themes", kwargs, _invoke)

    def rank(self, *, top: int = 20) -> ServiceResult:
        """Identify important nodes via PageRank."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {"top": top}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).rank(top=kw["top"])

        return self._run_action("rank", kwargs, _invoke)

    def path(self, source_id: str, target_id: str) -> ServiceResult:
        """Find shortest connection chain between two nodes."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {"source_id": source_id, "target_id": target_id}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).path(kw["source_id"], kw["target_id"])

        return self._run_action("path", kwargs, _invoke)

    def gaps(self, *, top: int = 20) -> ServiceResult:
        """Find structural holes — nodes with high constraint."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {"top": top}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).gaps(top=kw["top"])

        return self._run_action("gaps", kwargs, _invoke)

    def bridges(self, *, top: int = 20) -> ServiceResult:
        """Find bridge nodes via betweenness centrality."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {"top": top}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).bridges(top=kw["top"])

        return self._run_action("bridges", kwargs, _invoke)

    def unlink(self, source_id: str, target_id: str, *, both: bool = False) -> ServiceResult:
        """Remove links from source_id to target_id."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {
            "source_id": source_id,
            "target_id": target_id,
            "both": both,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).unlink(
                kw["source_id"], kw["target_id"], both=kw["both"]
            )

        return self._run_action("unlink", kwargs, _invoke)

    def materialize_metrics(self) -> ServiceResult:
        """Compute and store graph metrics in the nodes table."""
        from ztlctl.services.graph import GraphService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return GraphService(self._vault).materialize_metrics()

        return self._run_action("materialize_metrics", kwargs, _invoke)
