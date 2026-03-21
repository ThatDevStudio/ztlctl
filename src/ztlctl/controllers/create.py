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

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CreateService(self._vault).create_note(
                kw["title"],
                subtype=kw["subtype"],
                tags=kw["tags"],
                topic=kw["topic"],
                session=kw["session"],
                maturity=kw["maturity"],
                body=kw["body"],
                key_points=kw["key_points"],
                links=kw["links"],
                aliases=kw["aliases"],
                dispatch_post_create=dispatch_post_create,
            )

        return self._run_action("create_note", kwargs, _invoke)

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

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CreateService(self._vault).create_reference(
                kw["title"],
                url=kw["url"],
                canonical_url=kw["canonical_url"],
                subtype=kw["subtype"],
                tags=kw["tags"],
                topic=kw["topic"],
                session=kw["session"],
                aliases=kw["aliases"],
                links=kw["links"],
                key_points=kw["key_points"],
                body=kw["body"],
                summary=kw["summary"],
                excerpts=kw["excerpts"],
                notes=kw["notes"],
                provenance=kw["provenance"],
                source_provider=kw["source_provider"],
                source_type=kw["source_type"],
                source_kind=kw["source_kind"],
                modalities=kw["modalities"],
                capture_agent=kw["capture_agent"],
                capture_method=kw["capture_method"],
                citations=kw["citations"],
                artifacts=kw["artifacts"],
                source_bundle_path=kw["source_bundle_path"],
                retrieved_at=kw["retrieved_at"],
                content_hash=kw["content_hash"],
                language=kw["language"],
                dispatch_post_create=dispatch_post_create,
            )

        return self._run_action("create_reference", kwargs, _invoke)

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

        kwargs: dict[str, Any] = {
            "title": title,
            "priority": priority,
            "impact": impact,
            "effort": effort,
            "tags": tags,
            "session": session,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CreateService(self._vault).create_task(
                kw["title"],
                priority=kw["priority"],
                impact=kw["impact"],
                effort=kw["effort"],
                tags=kw["tags"],
                session=kw["session"],
            )

        return self._run_action("create_task", kwargs, _invoke)

    def create_batch(
        self,
        items: list[dict[str, object]],
        *,
        partial: bool = False,
    ) -> ServiceResult:
        """Create multiple items atomically (or partially if partial=True)."""
        from ztlctl.services.create import CreateService

        kwargs: dict[str, Any] = {
            "items": items,
            "partial": partial,
        }

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CreateService(self._vault).create_batch(kw["items"], partial=kw["partial"])

        return self._run_action("create_batch", kwargs, _invoke)
