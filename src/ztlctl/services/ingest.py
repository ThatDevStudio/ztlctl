"""Ingestion services for text-first capture workflows."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, cast
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
from ztlctl.services.create import CreateService
from ztlctl.services.result import ServiceError, ServiceResult
from ztlctl.services.source_bundles import (
    bundle_artifacts,
    bundle_citation_lines,
    bundle_excerpt_lines,
    bundle_paths,
    bundle_provenance_lines,
    normalize_source_bundle,
    persist_source_bundle,
)
from ztlctl.services.telemetry import traced
from ztlctl.services.transcription import TranscriptionService


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
        source_bundle: dict[str, Any] | None = None,
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
            source_bundle=source_bundle,
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
        source_bundle: dict[str, Any] | None = None,
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
            source_bundle=source_bundle,
            dry_run=dry_run,
            no_reweave=no_reweave,
            provenance=[
                "Input Kind: file",
                f"Source File: {source_path}",
            ],
        )

    @traced
    def ingest_media(
        self,
        path: Path,
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
        """Ingest a media file or transcript into a captured reference.

        Accepts audio/video files (transcribed via faster-whisper) and transcript
        files (.vtt, .srt, .txt parsed locally). Always produces a captured reference
        in the two-phase workflow: captured → annotated (by an agent in a follow-up).
        """
        source_path = path.resolve()
        if not source_path.is_file():
            return ServiceResult(
                ok=False,
                op="ingest_media",
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"Media file not found: {source_path}",
                ),
            )

        suffix = source_path.suffix.lower()
        if suffix not in TranscriptionService.SUPPORTED_EXTENSIONS:
            return ServiceResult(
                ok=False,
                op="ingest_media",
                error=ServiceError(
                    code="UNSUPPORTED_INPUT",
                    message=f"Unsupported media file type: {suffix or '<none>'}",
                    detail={"supported": sorted(TranscriptionService.SUPPORTED_EXTENSIONS)},
                ),
            )

        cfg = self._vault.settings.ingest.media
        transcription_svc = TranscriptionService(
            whisper_model=cfg.whisper_model,
            language=cfg.language,
            compute_type=cfg.compute_type,
        )
        transcription = transcription_svc.transcribe_file(source_path)
        if isinstance(transcription, ServiceError):
            return ServiceResult(
                ok=False,
                op="ingest_media",
                error=transcription,
            )

        resolved_title = (title or source_path.stem).strip()

        return self._ingest_normalized(
            input_kind="media",
            title=resolved_title,
            body_text=transcription.text,
            target_type="reference",
            topic=topic,
            tags=tags,
            session=session,
            subtype=subtype,
            summary=summary,
            source_kind="media",
            modalities=list(transcription.modalities),
            capture_agent=transcription.capture_agent,
            capture_method=None,
            dry_run=dry_run,
            no_reweave=no_reweave,
            provenance=[
                "Input Kind: media",
                f"Source File: {source_path}",
            ],
            source_bundle={"source_path": str(source_path)},
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
            source_bundle=source_bundle,
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
        source_bundle: dict[str, Any] | None = None,
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
        bundle_requested = target == "reference"

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
                    "source_bundle_version": 1 if bundle_requested else None,
                    "source_bundle_path": None,
                },
            )
            return ServiceResult(
                ok=True,
                op=f"ingest_{input_kind}",
                data=payload,
                warnings=provider_warnings,
            )

        create = CreateService(self._vault)
        dispatch_post_create = not (
            no_reweave
            or self._vault.settings.no_reweave
            or not self._vault.settings.ingest.auto_reweave
        )

        if target == "note":
            note_warnings = list(provider_warnings)
            if self._source_bundle_requested(
                source_bundle=source_bundle,
                source_kind=source_kind,
                modalities=modalities,
                capture_agent=capture_agent,
                capture_method=capture_method,
                citations=citations,
                excerpts=excerpts,
                artifacts=artifacts,
            ):
                note_warnings.append(
                    "Source bundles are only persisted for reference captures; "
                    "note ingest kept the normalized text only."
                )
            result = create.create_note(
                title,
                subtype=subtype,
                tags=tags,
                topic=topic,
                session=session,
                body=normalized_body,
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
                    "source_bundle_version": None,
                    "source_bundle_path": None,
                },
            )
            final_result = ServiceResult(
                ok=True,
                op=f"ingest_{input_kind}",
                data=payload,
                warnings=[*result.warnings, *note_warnings],
            )
            self._dispatch_post_action_event(
                action_name=f"ingest_{input_kind}",
                payload=payload,
                warnings=[*result.warnings, *note_warnings],
                result=final_result,
            )
            return final_result
        return self._create_reference_with_bundle(
            title=title,
            normalized_body=normalized_body,
            input_kind=input_kind,
            subtype=subtype,
            tags=tags,
            topic=topic,
            session=session,
            summary=summary,
            provider_name=provider_name,
            source_type=source_type or input_kind,
            source_kind=source_kind,
            canonical_url=canonical_url,
            language=language,
            key_points=key_points,
            provenance_items=provenance_items,
            citations=citations,
            excerpts=excerpts,
            artifacts=artifacts,
            source_bundle=source_bundle,
            modalities=modalities,
            capture_agent=capture_agent,
            capture_method=capture_method,
            content_hash=content_hash,
            dispatch_post_create=dispatch_post_create,
            provider_warnings=provider_warnings,
        )

    @staticmethod
    def _source_bundle_requested(
        *,
        source_bundle: dict[str, Any] | None,
        source_kind: str | None,
        modalities: list[str] | None,
        capture_agent: str | None,
        capture_method: str | None,
        citations: list[str] | None,
        excerpts: list[str] | None,
        artifacts: list[dict[str, object]] | None,
    ) -> bool:
        return any(
            (
                source_bundle,
                source_kind,
                modalities,
                capture_agent,
                capture_method,
                citations,
                excerpts,
                artifacts,
            )
        )

    def _create_reference_with_bundle(
        self,
        *,
        title: str,
        normalized_body: str,
        input_kind: str,
        subtype: str | None,
        tags: list[str] | None,
        topic: str | None,
        session: str | None,
        summary: str | None,
        provider_name: str | None,
        source_type: str | None,
        source_kind: str | None,
        canonical_url: str | None,
        language: str | None,
        key_points: list[str] | None,
        provenance_items: list[str],
        citations: list[str] | None,
        excerpts: list[str] | None,
        artifacts: list[dict[str, object]] | None,
        source_bundle: dict[str, Any] | None,
        modalities: list[str] | None,
        capture_agent: str | None,
        capture_method: str | None,
        content_hash: str,
        dispatch_post_create: bool,
        provider_warnings: list[str],
    ) -> ServiceResult:
        create = CreateService(self._vault)
        warnings: list[str] = []
        bundle_path_value: str | None = None
        bundle_version = 1

        with self._vault.transaction() as txn:
            pending_paths = bundle_paths("pending")
            normalized_bundle = normalize_source_bundle(
                input_kind=input_kind,
                title=title,
                normalized_text_path=pending_paths.normalized_text_path,
                normalized_text=normalized_body,
                content_hash=content_hash,
                captured_at=now_iso(),
                summary_hint=summary,
                source_type=source_type,
                source_kind=source_kind,
                canonical_url=canonical_url,
                provider_name=provider_name,
                language=language,
                key_points=key_points,
                provenance=provenance_items,
                citations=citations,
                excerpts=excerpts,
                artifacts=artifacts,
                modalities=modalities,
                capture_agent=capture_agent,
                capture_method=capture_method,
                source_bundle=source_bundle,
            )
            # Inject extra top-level fields from source_bundle (e.g. source_path for media)
            if source_bundle:
                _known_bundle_keys = {
                    "title",
                    "source_kind",
                    "modalities",
                    "capture_agent",
                    "capture_method",
                    "captured_at",
                    "summary_hint",
                    "key_points",
                    "provenance",
                    "source_title",
                    "url",
                    "canonical_url",
                    "provider",
                    "source_type",
                    "language",
                    "citations",
                    "excerpts",
                    "artifacts",
                    "metadata",
                }
                for _k, _v in source_bundle.items():
                    if _k not in _known_bundle_keys:
                        normalized_bundle[_k] = _v

            result, created = create._create_content_in_txn(
                txn,
                content_type="reference",
                title=title,
                subtype=subtype,
                tags=tags,
                topic=topic,
                session=session,
                key_points=list(normalized_bundle.get("key_points", [])),
                summary=normalized_bundle.get("summary_hint"),
                notes=normalized_body,
                excerpts=bundle_excerpt_lines(normalized_bundle),
                provenance=bundle_provenance_lines(normalized_bundle, include_paths=False),
                canonical_url=(
                    normalized_bundle.get("canonical_source", {}).get("canonical_url")
                    or normalized_bundle.get("canonical_source", {}).get("url")
                ),
                source_provider=normalized_bundle.get("canonical_source", {}).get("provider"),
                source_type=normalized_bundle.get("canonical_source", {}).get("source_type"),
                source_kind=normalized_bundle.get("source_kind"),
                modalities=list(normalized_bundle.get("modalities", [])),
                capture_agent=normalized_bundle.get("capture_agent"),
                capture_method=normalized_bundle.get("capture_method"),
                citations=bundle_citation_lines(normalized_bundle),
                artifacts=bundle_artifacts(normalized_bundle),
                retrieved_at=str(normalized_bundle.get("captured_at") or now_iso()),
                content_hash=content_hash,
                language=normalized_bundle.get("canonical_source", {}).get("language"),
            )
            if not result.ok or created is None:
                return result

            reference_id = str(result.data["id"])
            reference_relpath = str(result.data["path"])
            actual_paths = bundle_paths(reference_id)
            normalized_bundle["normalized_text"]["path"] = actual_paths.normalized_text_path
            persist_source_bundle(txn, reference_id, normalized_bundle, normalized_body)
            bundle_path_value = actual_paths.bundle_path

            content_path = self._vault.root / reference_relpath
            frontmatter, body = txn.read_content(content_path)
            frontmatter["source_bundle_path"] = bundle_path_value
            body_suffix = [
                f"- Source Bundle: {bundle_path_value}",
                f"- Normalized Text: {actual_paths.normalized_text_path}",
            ]
            updated_body = body.rstrip()
            if updated_body:
                updated_body += "\n"
            updated_body += "\n".join(body_suffix) + "\n"
            txn.write_content(content_path, frontmatter, updated_body)
            txn.upsert_fts(reference_id, created.title, updated_body)
            warnings.extend(result.warnings)

        if dispatch_post_create:
            create._dispatch_event(
                "post_create",
                {
                    "content_type": created.content_type,
                    "content_id": created.content_id,
                    "title": created.title,
                    "path": created.path,
                    "tags": created.tags,
                },
                warnings,
            )

        create._vector_index_created(created, warnings)
        payload = dump_validated(
            IngestResultData,
            {
                "id": created.content_id,
                "path": created.path,
                "title": created.title,
                "type": created.content_type,
                "input_kind": input_kind,
                "provider": provider_name,
                "dry_run": False,
                "source_kind": source_kind,
                "modalities": list(normalized_bundle.get("modalities", [])),
                "capture_agent": normalized_bundle.get("capture_agent"),
                "capture_method": normalized_bundle.get("capture_method"),
                "source_bundle_version": bundle_version,
                "source_bundle_path": bundle_path_value,
            },
        )
        final_result = ServiceResult(
            ok=True,
            op=f"ingest_{input_kind}",
            data=payload,
            warnings=[*warnings, *provider_warnings],
        )
        self._dispatch_post_action_event(
            action_name=f"ingest_{input_kind}",
            payload=payload,
            warnings=[*warnings, *provider_warnings],
            result=final_result,
        )
        return final_result
