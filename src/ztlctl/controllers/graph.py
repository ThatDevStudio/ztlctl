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
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"content_id": content_id, "depth": depth, "top": top}

        kwargs, rejection = self._dispatch_pre_action("related", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="related",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).related(
            kwargs["content_id"], depth=kwargs["depth"], top=kwargs["top"]
        )

        self._dispatch_post_action("related", kwargs, result)
        return result

    def themes(self) -> ServiceResult:
        """Discover topic clusters via community detection."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("themes", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="themes",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).themes()

        self._dispatch_post_action("themes", kwargs, result)
        return result

    def rank(self, *, top: int = 20) -> ServiceResult:
        """Identify important nodes via PageRank."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"top": top}

        kwargs, rejection = self._dispatch_pre_action("rank", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="rank",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).rank(top=kwargs["top"])

        self._dispatch_post_action("rank", kwargs, result)
        return result

    def path(self, source_id: str, target_id: str) -> ServiceResult:
        """Find shortest connection chain between two nodes."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"source_id": source_id, "target_id": target_id}

        kwargs, rejection = self._dispatch_pre_action("path", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="path",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).path(kwargs["source_id"], kwargs["target_id"])

        self._dispatch_post_action("path", kwargs, result)
        return result

    def gaps(self, *, top: int = 20) -> ServiceResult:
        """Find structural holes — nodes with high constraint."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"top": top}

        kwargs, rejection = self._dispatch_pre_action("gaps", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="gaps",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).gaps(top=kwargs["top"])

        self._dispatch_post_action("gaps", kwargs, result)
        return result

    def bridges(self, *, top: int = 20) -> ServiceResult:
        """Find bridge nodes via betweenness centrality."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"top": top}

        kwargs, rejection = self._dispatch_pre_action("bridges", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="bridges",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).bridges(top=kwargs["top"])

        self._dispatch_post_action("bridges", kwargs, result)
        return result

    def unlink(self, source_id: str, target_id: str, *, both: bool = False) -> ServiceResult:
        """Remove links from source_id to target_id."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "source_id": source_id,
            "target_id": target_id,
            "both": both,
        }

        kwargs, rejection = self._dispatch_pre_action("unlink", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="unlink",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).unlink(
            kwargs["source_id"], kwargs["target_id"], both=kwargs["both"]
        )

        self._dispatch_post_action("unlink", kwargs, result)
        return result

    def materialize_metrics(self) -> ServiceResult:
        """Compute and store graph metrics in the nodes table."""
        from ztlctl.services.graph import GraphService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("materialize_metrics", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="materialize_metrics",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = GraphService(self._vault).materialize_metrics()

        self._dispatch_post_action("materialize_metrics", kwargs, result)
        return result
