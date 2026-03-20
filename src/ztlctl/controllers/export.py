"""ExportController — orchestration wrapper for ExportService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Literal

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

        return ExportService(self._vault).export_markdown(Path(output_dir), filters=filters)

    def export_indexes(
        self,
        output_dir: Path | str,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Generate index files grouped by type and topic."""
        from ztlctl.services.export import ExportService

        return ExportService(self._vault).export_indexes(Path(output_dir), filters=filters)

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

        result = ExportService(self._vault).export_graph(fmt=fmt, filters=filters)
        if not result.ok or output_file is None:
            return result

        out_path = Path(output_file)
        out_path.write_text(result.data["content"], encoding="utf-8")
        return ServiceResult(
            ok=True,
            op="export_graph",
            data={
                "format": fmt,
                "output_file": output_file,
                "node_count": result.data.get("node_count", 0),
            },
        )

    def export_dashboard(
        self,
        output_dir: Path | str,
        *,
        viewer: Literal["obsidian", "none"] | str = "obsidian",
    ) -> ServiceResult:
        """Export an external review workbench plus review and dossier artifacts."""
        from ztlctl.services.export import ExportService

        return ExportService(self._vault).export_dashboard(Path(output_dir), viewer=viewer)
