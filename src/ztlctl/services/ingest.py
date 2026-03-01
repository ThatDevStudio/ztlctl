"""Ingestion services for text-first capture workflows."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import cast
from urllib.parse import urlparse

from ztlctl.plugins.contracts import SourceFetchRequest, SourceProviderContribution
from ztlctl.services._helpers import now_iso
from ztlctl.services.base import BaseService
from ztlctl.services.contracts import (
    IngestPreviewData,
    IngestResultData,
    SourceProvidersResultData,
    dump_validated,
)
from ztlctl.services.result import ServiceError, ServiceResult


class IngestService(BaseService):
    """Normalize external text input into durable vault artifacts."""

    def list_providers(self) -> ServiceResult:
        """List registered source providers."""
        items = [
            {
                "name": provider.name,
                "description": provider.description,
                "schemes": sorted(provider.schemes),
            }
            for provider in self._providers()
        ]
        return ServiceResult(
            ok=True,
            op="ingest_providers",
            data=dump_validated(SourceProvidersResultData, {"count": len(items), "items": items}),
        )

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
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest raw text into a note or reference."""
        normalized_title = title.strip()
        if not normalized_title:
            return ServiceResult(
                ok=False,
                op="ingest_text",
                error=ServiceError(code="VALIDATION_FAILED", message="Title cannot be empty"),
            )
        return self._ingest_normalized(
            input_kind="text",
            title=normalized_title,
            body_text=body_text,
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
            dry_run=dry_run,
            no_reweave=no_reweave,
            provenance=["Input Kind: text"],
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
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest a plain text or markdown file."""
        source_path = path.resolve()
        if not source_path.is_file():
            return ServiceResult(
                ok=False,
                op="ingest_file",
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"Source file not found: {source_path}",
                ),
            )

        suffix = source_path.suffix.lower()
        if suffix not in {".md", ".txt"}:
            return ServiceResult(
                ok=False,
                op="ingest_file",
                error=ServiceError(
                    code="UNSUPPORTED_INPUT",
                    message=f"Unsupported ingest file type: {suffix or '<none>'}",
                    detail={"supported": [".md", ".txt"]},
                ),
            )

        body_text = source_path.read_text(encoding="utf-8")
        resolved_title = (title or source_path.stem).strip()
        return self._ingest_normalized(
            input_kind="file",
            title=resolved_title,
            body_text=body_text,
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
            dry_run=dry_run,
            no_reweave=no_reweave,
            provenance=[
                "Input Kind: file",
                f"Source File: {source_path}",
            ],
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
        dry_run: bool = False,
        no_reweave: bool = False,
    ) -> ServiceResult:
        """Ingest a URL through a registered source provider."""
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()
        if not scheme:
            return ServiceResult(
                ok=False,
                op="ingest_url",
                error=ServiceError(code="VALIDATION_FAILED", message="URL must include a scheme"),
            )

        selected = self._select_provider(scheme, provider)
        if selected is None:
            return ServiceResult(
                ok=False,
                op="ingest_url",
                error=ServiceError(
                    code="NO_PROVIDER",
                    message=f"No source provider available for scheme '{scheme}'",
                    detail={
                        "hint": "Run `ztlctl ingest providers` to inspect available providers."
                    },
                ),
            )

        fetched = selected.fetch(
            SourceFetchRequest(
                content=url,
                input_kind="url",
                summary=summary,
                provider=provider,
            )
        )
        normalized_title = (title or fetched.title or url).strip()
        provenance = [
            "Input Kind: url",
            f"Provider: {selected.name}",
            f"URL: {url}",
        ]
        if fetched.canonical_url and fetched.canonical_url != url:
            provenance.append(f"Canonical URL: {fetched.canonical_url}")

        return self._ingest_normalized(
            input_kind="url",
            title=normalized_title,
            body_text=fetched.body_text,
            target_type=target_type,
            topic=topic,
            tags=tags,
            session=session,
            subtype=subtype,
            summary=summary or fetched.summary_hint,
            dry_run=dry_run,
            no_reweave=no_reweave,
            provider_name=selected.name,
            source_type=fetched.source_type or fetched.content_type,
            source_kind=source_kind or fetched.source_type or "web",
            canonical_url=fetched.canonical_url or url,
            language=fetched.language,
            key_points=list(fetched.key_points),
            provenance=provenance + list(fetched.citations),
            citations=(citations or []) + list(fetched.citations),
            excerpts=excerpts,
            artifacts=artifacts,
            modalities=modalities,
            capture_agent=capture_agent,
            capture_method=capture_method,
            warnings=list(fetched.warnings),
        )

    def _providers(self) -> list[SourceProviderContribution]:
        pm = self._vault.plugin_manager
        if pm is None:
            return []
        return cast(list[SourceProviderContribution], pm.source_provider_contributions())

    def _select_provider(
        self,
        scheme: str,
        explicit_name: str | None,
    ) -> SourceProviderContribution | None:
        providers = self._providers()
        if explicit_name is not None:
            for provider in providers:
                if provider.name == explicit_name:
                    return provider
            return None
        for provider in providers:
            if scheme in provider.schemes:
                return provider
        return None

    def _ingest_normalized(
        self,
        *,
        input_kind: str,
        title: str,
        body_text: str,
        target_type: str | None,
        topic: str | None,
        tags: list[str] | None,
        session: str | None,
        subtype: str | None,
        summary: str | None,
        dry_run: bool,
        no_reweave: bool,
        provider_name: str | None = None,
        source_type: str | None = None,
        source_kind: str | None = None,
        canonical_url: str | None = None,
        language: str | None = None,
        key_points: list[str] | None = None,
        provenance: list[str] | None = None,
        citations: list[str] | None = None,
        excerpts: list[str] | None = None,
        artifacts: list[dict[str, object]] | None = None,
        modalities: list[str] | None = None,
        capture_agent: str | None = None,
        capture_method: str | None = None,
        warnings: list[str] | None = None,
    ) -> ServiceResult:
        target = (target_type or self._vault.settings.ingest.default_target_type).strip().lower()
        if target not in {"reference", "note"}:
            return ServiceResult(
                ok=False,
                op=f"ingest_{input_kind}",
                error=ServiceError(
                    code="UNKNOWN_TYPE",
                    message=f"Unsupported ingest target type: {target}",
                ),
            )

        normalized_body = body_text.strip()
        content_hash = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()[:16]
        provenance_items = provenance or [f"Input Kind: {input_kind}"]
        provider_warnings = warnings or []

        if dry_run:
            preview = normalized_body[:280]
            payload = dump_validated(
                IngestPreviewData,
                {
                    "input_kind": input_kind,
                    "target_type": target,
                    "title": title,
                    "body_preview": preview,
                    "provider": provider_name,
                    "source_kind": source_kind,
                    "modalities": modalities or [],
                    "capture_agent": capture_agent,
                    "capture_method": capture_method,
                    "provenance": provenance_items,
                    "key_points": key_points or [],
                    "citations": citations or [],
                    "excerpts": excerpts or [],
                },
            )
            return ServiceResult(
                ok=True,
                op=f"ingest_{input_kind}",
                data=payload,
                warnings=provider_warnings,
            )

        from ztlctl.services.create import CreateService

        create = CreateService(self._vault)
        dispatch_post_create = not (
            no_reweave
            or self._vault.settings.no_reweave
            or not self._vault.settings.ingest.auto_reweave
        )

        if target == "note":
            result = create.create_note(
                title,
                subtype=subtype,
                tags=tags,
                topic=topic,
                session=session,
                body=normalized_body,
                dispatch_post_create=dispatch_post_create,
            )
        else:
            result = create.create_reference(
                title,
                subtype=subtype,
                tags=tags,
                topic=topic,
                session=session,
                key_points=key_points or [],
                summary=summary,
                notes=normalized_body,
                excerpts=excerpts,
                provenance=provenance_items,
                canonical_url=canonical_url,
                source_provider=provider_name,
                source_type=source_type or input_kind,
                source_kind=source_kind,
                modalities=modalities,
                capture_agent=capture_agent,
                capture_method=capture_method,
                citations=citations,
                artifacts=[dict(item) for item in (artifacts or [])],
                retrieved_at=now_iso(),
                content_hash=content_hash,
                language=language,
                dispatch_post_create=dispatch_post_create,
            )

        if not result.ok:
            return result

        payload = dump_validated(
            IngestResultData,
            {
                "id": result.data["id"],
                "path": result.data["path"],
                "title": result.data["title"],
                "type": result.data["type"],
                "input_kind": input_kind,
                "provider": provider_name,
                "dry_run": False,
                "source_kind": source_kind,
                "modalities": modalities or [],
                "capture_agent": capture_agent,
                "capture_method": capture_method,
            },
        )
        return ServiceResult(
            ok=True,
            op=f"ingest_{input_kind}",
            data=payload,
            warnings=[*result.warnings, *provider_warnings],
        )
