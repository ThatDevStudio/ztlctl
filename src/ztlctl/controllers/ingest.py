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

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return IngestService(self._vault).list_providers()

        return self._run_action("list_providers", kwargs, _invoke)

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

        kwargs: dict[str, Any] = {
            "title": title,
            "body_text": body_text,
            "target_type": target_type,
            "topic": topic,
            "tags": tags,
            "session": session,
            "subtype": subtype,
            "summary": summary,
            "source_kind": source_kind,
            "modalities": modalities,
            "capture_agent": capture_agent,
            "capture_method": capture_method,
            "citations": citations,
            "excerpts": excerpts,
            "artifacts": artifacts,
            "source_bundle": source_bundle,
            "dry_run": dry_run,
            "no_reweave": no_reweave,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return IngestService(self._vault).ingest_text(
                kw["title"],
                kw["body_text"],
                target_type=kw["target_type"],
                topic=kw["topic"],
                tags=kw["tags"],
                session=kw["session"],
                subtype=kw["subtype"],
                summary=kw["summary"],
                source_kind=kw["source_kind"],
                modalities=kw["modalities"],
                capture_agent=kw["capture_agent"],
                capture_method=kw["capture_method"],
                citations=kw["citations"],
                excerpts=kw["excerpts"],
                artifacts=kw["artifacts"],
                source_bundle=kw["source_bundle"],
                dry_run=kw["dry_run"],
                no_reweave=kw["no_reweave"],
            )

        return self._run_action("ingest_text", kwargs, _invoke)

    def ingest_file(
        self,
        path: Path | str,
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

        kwargs: dict[str, Any] = {
            "path": path,
            "title": title,
            "target_type": target_type,
            "topic": topic,
            "tags": tags,
            "session": session,
            "subtype": subtype,
            "summary": summary,
            "source_kind": source_kind,
            "modalities": modalities,
            "capture_agent": capture_agent,
            "capture_method": capture_method,
            "citations": citations,
            "excerpts": excerpts,
            "artifacts": artifacts,
            "source_bundle": source_bundle,
            "dry_run": dry_run,
            "no_reweave": no_reweave,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return IngestService(self._vault).ingest_file(
                Path(kw["path"]),
                title=kw["title"],
                target_type=kw["target_type"],
                topic=kw["topic"],
                tags=kw["tags"],
                session=kw["session"],
                subtype=kw["subtype"],
                summary=kw["summary"],
                source_kind=kw["source_kind"],
                modalities=kw["modalities"],
                capture_agent=kw["capture_agent"],
                capture_method=kw["capture_method"],
                citations=kw["citations"],
                excerpts=kw["excerpts"],
                artifacts=kw["artifacts"],
                source_bundle=kw["source_bundle"],
                dry_run=kw["dry_run"],
                no_reweave=kw["no_reweave"],
            )

        return self._run_action("ingest_file", kwargs, _invoke)

    def ingest_media(
        self,
        path: Path | str,
        *,
        title: str | None = None,
        topic: str | None = None,
        tags: list[str] | None = None,
        session: str | None = None,
        subtype: str | None = None,
        summary: str | None = None,
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest a media file or transcript into a captured reference."""
        from ztlctl.services.ingest import IngestService

        kwargs: dict[str, Any] = {
            "path": path,
            "title": title,
            "topic": topic,
            "tags": tags,
            "session": session,
            "subtype": subtype,
            "summary": summary,
            "dry_run": dry_run,
            "no_reweave": no_reweave,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return IngestService(self._vault).ingest_media(
                Path(kw["path"]),
                title=kw["title"],
                topic=kw["topic"],
                tags=kw["tags"],
                session=kw["session"],
                subtype=kw["subtype"],
                summary=kw["summary"],
                dry_run=kw["dry_run"],
                no_reweave=kw["no_reweave"],
            )

        return self._run_action("ingest_media", kwargs, _invoke)

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

        kwargs: dict[str, Any] = {
            "url": url,
            "provider": provider,
            "title": title,
            "target_type": target_type,
            "topic": topic,
            "tags": tags,
            "session": session,
            "subtype": subtype,
            "summary": summary,
            "source_kind": source_kind,
            "modalities": modalities,
            "capture_agent": capture_agent,
            "capture_method": capture_method,
            "citations": citations,
            "excerpts": excerpts,
            "artifacts": artifacts,
            "source_bundle": source_bundle,
            "dry_run": dry_run,
            "no_reweave": no_reweave,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return IngestService(self._vault).ingest_url(
                kw["url"],
                provider=kw["provider"],
                title=kw["title"],
                target_type=kw["target_type"],
                topic=kw["topic"],
                tags=kw["tags"],
                session=kw["session"],
                subtype=kw["subtype"],
                summary=kw["summary"],
                source_kind=kw["source_kind"],
                modalities=kw["modalities"],
                capture_agent=kw["capture_agent"],
                capture_method=kw["capture_method"],
                citations=kw["citations"],
                excerpts=kw["excerpts"],
                artifacts=kw["artifacts"],
                source_bundle=kw["source_bundle"],
                dry_run=kw["dry_run"],
                no_reweave=kw["no_reweave"],
            )

        return self._run_action("ingest_url", kwargs, _invoke)
