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

        kwargs: dict[str, Any] = {"output_dir": output_dir, "filters": filters}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ExportService(self._vault).export_markdown(
                Path(kw["output_dir"]), filters=kw["filters"]
            )

        return self._run_action("export_markdown", kwargs, _invoke)

    def export_indexes(
        self,
        output_dir: Path | str,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Generate index files grouped by type and topic."""
        from ztlctl.services.export import ExportService

        kwargs: dict[str, Any] = {"output_dir": output_dir, "filters": filters}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ExportService(self._vault).export_indexes(
                Path(kw["output_dir"]), filters=kw["filters"]
            )

        return self._run_action("export_indexes", kwargs, _invoke)

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
        from ztlctl.services.result import ServiceResult

        kwargs: dict[str, Any] = {"fmt": fmt, "output_file": output_file, "filters": filters}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            svc_result = ExportService(self._vault).export_graph(
                fmt=kw["fmt"], filters=kw["filters"]
            )
            if not svc_result.ok or kw["output_file"] is None:
                return svc_result
            else:
                out_path = Path(kw["output_file"])
                out_path.write_text(svc_result.data["content"], encoding="utf-8")
                return ServiceResult(
                    ok=True,
                    op="export_graph",
                    data={
                        "format": kw["fmt"],
                        "output_file": kw["output_file"],
                        "node_count": svc_result.data.get("node_count", 0),
                    },
                )

        return self._run_action("export_graph", kwargs, _invoke)

    def export_dashboard(
        self,
        output_dir: Path | str,
        *,
        viewer: Literal["obsidian", "none"] | str = "obsidian",
    ) -> ServiceResult:
        """Export an external review workbench plus review and dossier artifacts."""
        from ztlctl.services.export import ExportService

        kwargs: dict[str, Any] = {"output_dir": output_dir, "viewer": viewer}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return ExportService(self._vault).export_dashboard(
                Path(kw["output_dir"]), viewer=kw["viewer"]
            )

        return self._run_action("export_dashboard", kwargs, _invoke)
