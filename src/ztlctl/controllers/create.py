"""CreateController — orchestration wrapper for CreateService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class CreateController(BaseController):
    """Thin wrapper over CreateService. All methods return ServiceResult."""

    def create_note(
        self,
        title: str,
        *,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
        maturity: str | None = None,
        body: str | None = None,
        key_points: list[str] | None = None,
        links: dict[str, list[str]] | None = None,
        aliases: list[str] | None = None,
        dispatch_post_create: bool = True,
    ) -> ServiceResult:
        """Create a new note."""
        from ztlctl.services.create import CreateService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "title": title,
            "subtype": subtype,
            "tags": tags,
            "topic": topic,
            "session": session,
            "maturity": maturity,
            "body": body,
            "key_points": key_points,
            "links": links,
            "aliases": aliases,
        }

        kwargs, rejection = self._dispatch_pre_action("create_note", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="create_note",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CreateService(self._vault).create_note(
            kwargs["title"],
            subtype=kwargs["subtype"],
            tags=kwargs["tags"],
            topic=kwargs["topic"],
            session=kwargs["session"],
            maturity=kwargs["maturity"],
            body=kwargs["body"],
            key_points=kwargs["key_points"],
            links=kwargs["links"],
            aliases=kwargs["aliases"],
            dispatch_post_create=dispatch_post_create,
        )

        self._dispatch_post_action("create_note", kwargs, result)
        return result

    def create_reference(
        self,
        title: str,
        *,
        url: str | None = None,
        canonical_url: str | None = None,
        subtype: str | None = None,
        tags: list[str] | None = None,
        topic: str | None = None,
        session: str | None = None,
        aliases: list[str] | None = None,
        links: dict[str, list[str]] | None = None,
        key_points: list[str] | None = None,
        body: str | None = None,
        summary: str | None = None,
        excerpts: list[str] | None = None,
        notes: str | None = None,
        provenance: list[str] | None = None,
        source_provider: str | None = None,
        source_type: str | None = None,
        source_kind: str | None = None,
        modalities: list[str] | None = None,
        capture_agent: str | None = None,
        capture_method: str | None = None,
        citations: list[str] | None = None,
        artifacts: list[dict[str, Any]] | None = None,
        source_bundle_path: str | None = None,
        retrieved_at: str | None = None,
        content_hash: str | None = None,
        language: str | None = None,
        dispatch_post_create: bool = True,
    ) -> ServiceResult:
        """Create a new reference to an external source."""
        from ztlctl.services.create import CreateService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "title": title,
            "url": url,
            "canonical_url": canonical_url,
            "subtype": subtype,
            "tags": tags,
            "topic": topic,
            "session": session,
            "aliases": aliases,
            "links": links,
            "key_points": key_points,
            "body": body,
            "summary": summary,
            "excerpts": excerpts,
            "notes": notes,
            "provenance": provenance,
            "source_provider": source_provider,
            "source_type": source_type,
            "source_kind": source_kind,
            "modalities": modalities,
            "capture_agent": capture_agent,
            "capture_method": capture_method,
            "citations": citations,
            "artifacts": artifacts,
            "source_bundle_path": source_bundle_path,
            "retrieved_at": retrieved_at,
            "content_hash": content_hash,
            "language": language,
        }

        kwargs, rejection = self._dispatch_pre_action("create_reference", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="create_reference",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CreateService(self._vault).create_reference(
            kwargs["title"],
            url=kwargs["url"],
            canonical_url=kwargs["canonical_url"],
            subtype=kwargs["subtype"],
            tags=kwargs["tags"],
            topic=kwargs["topic"],
            session=kwargs["session"],
            aliases=kwargs["aliases"],
            links=kwargs["links"],
            key_points=kwargs["key_points"],
            body=kwargs["body"],
            summary=kwargs["summary"],
            excerpts=kwargs["excerpts"],
            notes=kwargs["notes"],
            provenance=kwargs["provenance"],
            source_provider=kwargs["source_provider"],
            source_type=kwargs["source_type"],
            source_kind=kwargs["source_kind"],
            modalities=kwargs["modalities"],
            capture_agent=kwargs["capture_agent"],
            capture_method=kwargs["capture_method"],
            citations=kwargs["citations"],
            artifacts=kwargs["artifacts"],
            source_bundle_path=kwargs["source_bundle_path"],
            retrieved_at=kwargs["retrieved_at"],
            content_hash=kwargs["content_hash"],
            language=kwargs["language"],
            dispatch_post_create=dispatch_post_create,
        )

        self._dispatch_post_action("create_reference", kwargs, result)
        return result

    def create_task(
        self,
        title: str,
        *,
        priority: str = "medium",
        impact: str = "medium",
        effort: str = "medium",
        tags: list[str] | None = None,
        session: str | None = None,
    ) -> ServiceResult:
        """Create a new task."""
        from ztlctl.services.create import CreateService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "title": title,
            "priority": priority,
            "impact": impact,
            "effort": effort,
            "tags": tags,
            "session": session,
        }

        kwargs, rejection = self._dispatch_pre_action("create_task", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="create_task",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CreateService(self._vault).create_task(
            kwargs["title"],
            priority=kwargs["priority"],
            impact=kwargs["impact"],
            effort=kwargs["effort"],
            tags=kwargs["tags"],
            session=kwargs["session"],
        )

        self._dispatch_post_action("create_task", kwargs, result)
        return result

    def create_batch(
        self,
        items: list[dict[str, object]],
        *,
        partial: bool = False,
    ) -> ServiceResult:
        """Create multiple items atomically (or partially if partial=True)."""
        from ztlctl.services.create import CreateService
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {
            "items": items,
            "partial": partial,
        }

        kwargs, rejection = self._dispatch_pre_action("create_batch", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="create_batch",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        result = CreateService(self._vault).create_batch(kwargs["items"], partial=kwargs["partial"])

        self._dispatch_post_action("create_batch", kwargs, result)
        return result
