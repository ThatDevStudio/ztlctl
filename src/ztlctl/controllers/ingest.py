"""IngestController — orchestration wrapper for IngestService."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class IngestController(BaseController):
    """Thin wrapper over IngestService. All methods return ServiceResult."""

    def list_providers(self) -> ServiceResult:
        """List registered source providers."""
        from ztlctl.services.ingest import IngestService

        return IngestService(self._vault).list_providers()

    def ingest_text(
        self,
        title: str,
        body_text: str,
        *,
        target_type: str | None = None,
        topic: str | None = None,
        tags: list[str] | None = None,
        session: str | None = None,
        subtype: str | None = None,
        summary: str | None = None,
        source_kind: str | None = None,
        modalities: list[str] | None = None,
        capture_agent: str | None = None,
        capture_method: str | None = None,
        citations: list[str] | None = None,
        excerpts: list[str] | None = None,
        artifacts: list[dict[str, object]] | None = None,
        source_bundle: dict[str, Any] | None = None,
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest raw text into a note or reference."""
        from ztlctl.services.ingest import IngestService

        return IngestService(self._vault).ingest_text(
            title,
            body_text,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            subtype=subtype,
            summary=summary,
            source_kind=source_kind,
            modalities=modalities,
            capture_agent=capture_agent,
            capture_method=capture_method,
            citations=citations,
            excerpts=excerpts,
            artifacts=artifacts,
            source_bundle=source_bundle,
            dry_run=dry_run,
            no_reweave=no_reweave,
        )

    def ingest_file(
        self,
        path: Path,
        *,
        title: str | None = None,
        target_type: str | None = None,
        topic: str | None = None,
        tags: list[str] | None = None,
        session: str | None = None,
        subtype: str | None = None,
        summary: str | None = None,
        source_kind: str | None = None,
        modalities: list[str] | None = None,
        capture_agent: str | None = None,
        capture_method: str | None = None,
        citations: list[str] | None = None,
        excerpts: list[str] | None = None,
        artifacts: list[dict[str, object]] | None = None,
        source_bundle: dict[str, Any] | None = None,
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest a plain text or markdown file."""
        from ztlctl.services.ingest import IngestService

        return IngestService(self._vault).ingest_file(
            path,
            title=title,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            subtype=subtype,
            summary=summary,
            source_kind=source_kind,
            modalities=modalities,
            capture_agent=capture_agent,
            capture_method=capture_method,
            citations=citations,
            excerpts=excerpts,
            artifacts=artifacts,
            source_bundle=source_bundle,
            dry_run=dry_run,
            no_reweave=no_reweave,
        )

    def ingest_url(
        self,
        url: str,
        *,
        provider: str | None = None,
        title: str | None = None,
        target_type: str | None = None,
        topic: str | None = None,
        tags: list[str] | None = None,
        session: str | None = None,
        subtype: str | None = None,
        summary: str | None = None,
        source_kind: str | None = None,
        modalities: list[str] | None = None,
        capture_agent: str | None = None,
        capture_method: str | None = None,
        citations: list[str] | None = None,
        excerpts: list[str] | None = None,
        artifacts: list[dict[str, object]] | None = None,
        source_bundle: dict[str, Any] | None = None,
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest a URL through a registered source provider."""
        from ztlctl.services.ingest import IngestService

        return IngestService(self._vault).ingest_url(
            url,
            provider=provider,
            title=title,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            subtype=subtype,
            summary=summary,
            source_kind=source_kind,
            modalities=modalities,
            capture_agent=capture_agent,
            capture_method=capture_method,
            citations=citations,
            excerpts=excerpts,
            artifacts=artifacts,
            source_bundle=source_bundle,
            dry_run=dry_run,
            no_reweave=no_reweave,
        )
