"""ExportController — orchestration wrapper for ExportService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.export import ExportFilters
    from ztlctl.services.result import ServiceResult


class ExportController(BaseController):
    """Thin wrapper over ExportService. All methods return ServiceResult."""

    def export_markdown(
        self,
        output_dir: Path | str,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Copy all content files to output_dir, preserving relative paths."""
        from ztlctl.services.export import ExportService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"output_dir": output_dir, "filters": filters}

        kwargs, rejection = self._dispatch_pre_action("export_markdown", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="export_markdown",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = ExportService(self._vault).export_markdown(
            Path(kwargs["output_dir"]), filters=kwargs["filters"]
        )

        self._dispatch_post_action("export_markdown", kwargs, result)
        return result

    def export_indexes(
        self,
        output_dir: Path | str,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Generate index files grouped by type and topic."""
        from ztlctl.services.export import ExportService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"output_dir": output_dir, "filters": filters}

        kwargs, rejection = self._dispatch_pre_action("export_indexes", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="export_indexes",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = ExportService(self._vault).export_indexes(
            Path(kwargs["output_dir"]), filters=kwargs["filters"]
        )

        self._dispatch_post_action("export_indexes", kwargs, result)
        return result

    def export_graph(
        self,
        *,
        fmt: str = "dot",
        output_file: str | None = None,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Export the vault's knowledge graph (dot or json format).

        When ``output_file`` is provided the graph content is written to that
        path and the returned ServiceResult contains summary metadata only
        (no ``content`` key).  When omitted the full content is available in
        ``result.data["content"]`` for CLI/MCP consumers to render.
        """
        from ztlctl.services.export import ExportService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"fmt": fmt, "output_file": output_file, "filters": filters}

        kwargs, rejection = self._dispatch_pre_action("export_graph", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="export_graph",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        svc_result = ExportService(self._vault).export_graph(
            fmt=kwargs["fmt"], filters=kwargs["filters"]
        )
        if not svc_result.ok or kwargs["output_file"] is None:
            result = svc_result
        else:
            out_path = Path(kwargs["output_file"])
            out_path.write_text(svc_result.data["content"], encoding="utf-8")
            result = ServiceResult(
                ok=True,
                op="export_graph",
                data={
                    "format": kwargs["fmt"],
                    "output_file": kwargs["output_file"],
                    "node_count": svc_result.data.get("node_count", 0),
                },
            )

        self._dispatch_post_action("export_graph", kwargs, result)
        return result

    def export_dashboard(
        self,
        output_dir: Path | str,
        *,
        viewer: Literal["obsidian", "none"] | str = "obsidian",
    ) -> ServiceResult:
        """Export an external review workbench plus review and dossier artifacts."""
        from ztlctl.services.export import ExportService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"output_dir": output_dir, "viewer": viewer}

        kwargs, rejection = self._dispatch_pre_action("export_dashboard", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="export_dashboard",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = ExportService(self._vault).export_dashboard(
            Path(kwargs["output_dir"]), viewer=kwargs["viewer"]
        )

        self._dispatch_post_action("export_dashboard", kwargs, result)
        return result
