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
        output_dir: Path,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Copy all content files to output_dir, preserving relative paths."""
        from ztlctl.services.export import ExportService

        return ExportService(self._vault).export_markdown(output_dir, filters=filters)

    def export_indexes(
        self,
        output_dir: Path,
        *,
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Generate index files grouped by type and topic."""
        from ztlctl.services.export import ExportService

        return ExportService(self._vault).export_indexes(output_dir, filters=filters)

    def export_graph(
        self,
        *,
        fmt: str = "dot",
        filters: ExportFilters | None = None,
    ) -> ServiceResult:
        """Export the vault's knowledge graph (dot or json format)."""
        from ztlctl.services.export import ExportService

        return ExportService(self._vault).export_graph(fmt=fmt, filters=filters)

    def export_dashboard(
        self,
        output_dir: Path,
        *,
        viewer: Literal["obsidian", "none"] | str = "obsidian",
    ) -> ServiceResult:
        """Export an external review workbench plus review and dossier artifacts."""
        from ztlctl.services.export import ExportService

        return ExportService(self._vault).export_dashboard(output_dir, viewer=viewer)
