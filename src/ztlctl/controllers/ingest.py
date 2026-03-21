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
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("list_providers", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="list_providers",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = IngestService(self._vault).list_providers()
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult

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

        kwargs, rejection = self._dispatch_pre_action("ingest_text", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="ingest_text",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = IngestService(self._vault).ingest_text(
            kwargs["title"],
            kwargs["body_text"],
            target_type=kwargs["target_type"],
            topic=kwargs["topic"],
            tags=kwargs["tags"],
            session=kwargs["session"],
            subtype=kwargs["subtype"],
            summary=kwargs["summary"],
            source_kind=kwargs["source_kind"],
            modalities=kwargs["modalities"],
            capture_agent=kwargs["capture_agent"],
            capture_method=kwargs["capture_method"],
            citations=kwargs["citations"],
            excerpts=kwargs["excerpts"],
            artifacts=kwargs["artifacts"],
            source_bundle=kwargs["source_bundle"],
            dry_run=kwargs["dry_run"],
            no_reweave=kwargs["no_reweave"],
        )
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult

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

        kwargs, rejection = self._dispatch_pre_action("ingest_file", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="ingest_file",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = IngestService(self._vault).ingest_file(
            Path(kwargs["path"]),
            title=kwargs["title"],
            target_type=kwargs["target_type"],
            topic=kwargs["topic"],
            tags=kwargs["tags"],
            session=kwargs["session"],
            subtype=kwargs["subtype"],
            summary=kwargs["summary"],
            source_kind=kwargs["source_kind"],
            modalities=kwargs["modalities"],
            capture_agent=kwargs["capture_agent"],
            capture_method=kwargs["capture_method"],
            citations=kwargs["citations"],
            excerpts=kwargs["excerpts"],
            artifacts=kwargs["artifacts"],
            source_bundle=kwargs["source_bundle"],
            dry_run=kwargs["dry_run"],
            no_reweave=kwargs["no_reweave"],
        )
        return result

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
        from ztlctl.services.result import ServiceError, ServiceResult

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

        kwargs, rejection = self._dispatch_pre_action("ingest_url", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="ingest_url",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = IngestService(self._vault).ingest_url(
            kwargs["url"],
            provider=kwargs["provider"],
            title=kwargs["title"],
            target_type=kwargs["target_type"],
            topic=kwargs["topic"],
            tags=kwargs["tags"],
            session=kwargs["session"],
            subtype=kwargs["subtype"],
            summary=kwargs["summary"],
            source_kind=kwargs["source_kind"],
            modalities=kwargs["modalities"],
            capture_agent=kwargs["capture_agent"],
            capture_method=kwargs["capture_method"],
            citations=kwargs["citations"],
            excerpts=kwargs["excerpts"],
            artifacts=kwargs["artifacts"],
            source_bundle=kwargs["source_bundle"],
            dry_run=kwargs["dry_run"],
            no_reweave=kwargs["no_reweave"],
        )
        return result
