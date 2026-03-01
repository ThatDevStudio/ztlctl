"""Helpers for durable source bundle normalization and persistence."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ztlctl.services.contracts import SourceBundleData, dump_validated

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import VaultTransaction


@dataclass(frozen=True)
class SourceBundlePaths:
    """Filesystem paths for one persisted source bundle."""

    bundle_path: str
    normalized_text_path: str


def bundle_paths(reference_id: str) -> SourceBundlePaths:
    """Return vault-relative paths for a reference bundle."""
    base = Path("sources") / reference_id
    return SourceBundlePaths(
        bundle_path=str(base / "bundle.json"),
        normalized_text_path=str(base / "normalized.md"),
    )


def persist_source_bundle(
    txn: VaultTransaction,
    reference_id: str,
    bundle_data: dict[str, Any],
    normalized_text: str,
) -> SourceBundlePaths:
    """Persist bundle metadata and normalized text inside the active transaction."""
    paths = bundle_paths(reference_id)
    txn.write_file(
        txn._vault.root / paths.bundle_path,
        json.dumps(bundle_data, indent=2) + "\n",
    )
    txn.write_file(
        txn._vault.root / paths.normalized_text_path,
        normalized_text.rstrip() + "\n",
    )
    return paths


def load_source_bundle(vault_root: Path, source_bundle_path: str | None) -> dict[str, Any] | None:
    """Load a persisted source bundle if the pointer exists."""
    if not source_bundle_path:
        return None
    path = vault_root / source_bundle_path
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def normalize_source_bundle(
    *,
    input_kind: str,
    title: str,
    normalized_text_path: str,
    normalized_text: str,
    content_hash: str,
    captured_at: str,
    summary_hint: str | None,
    source_type: str | None,
    source_kind: str | None,
    canonical_url: str | None,
    provider_name: str | None,
    language: str | None,
    key_points: list[str] | None,
    provenance: list[str] | None,
    citations: list[str] | None,
    excerpts: list[str] | None,
    artifacts: list[dict[str, object]] | None,
    modalities: list[str] | None,
    capture_agent: str | None,
    capture_method: str | None,
    source_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    """Build a validated durable source bundle from ingest inputs."""
    raw = dict(source_bundle or {})

    normalized = dump_validated(
        SourceBundleData,
        {
            "version": 1,
            "input_kind": input_kind,
            "title": str(raw.get("title") or title),
            "source_kind": str(raw.get("source_kind") or source_kind or "") or None,
            "modalities": _modalities(raw.get("modalities"), modalities),
            "capture_agent": str(raw.get("capture_agent") or capture_agent or "") or None,
            "capture_method": str(raw.get("capture_method") or capture_method or "") or None,
            "captured_at": str(raw.get("captured_at") or captured_at),
            "summary_hint": str(raw.get("summary_hint") or summary_hint or "") or None,
            "key_points": _string_list(raw.get("key_points"), key_points),
            "provenance": _string_list(raw.get("provenance"), provenance),
            "canonical_source": {
                "title": str(raw.get("source_title") or raw.get("title") or title),
                "url": str(raw.get("url") or canonical_url or "") or None,
                "canonical_url": str(raw.get("canonical_url") or canonical_url or "") or None,
                "provider": str(raw.get("provider") or provider_name or "") or None,
                "source_type": str(raw.get("source_type") or source_type or "") or None,
                "language": str(raw.get("language") or language or "") or None,
            },
            "normalized_text": {
                "path": normalized_text_path,
                "content_hash": content_hash,
                "line_count": len(normalized_text.splitlines()),
            },
            "citations": _citations(raw.get("citations"), citations),
            "excerpts": _excerpts(raw.get("excerpts"), excerpts),
            "artifacts": _artifacts(raw.get("artifacts"), artifacts),
            "metadata": _metadata(raw.get("metadata")),
        },
    )
    return normalized


def bundle_citation_lines(bundle_data: dict[str, Any]) -> list[str]:
    """Flatten bundle citations into short reference-friendly strings."""
    lines: list[str] = []
    for item in bundle_data.get("citations", []):
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            locator = str(item.get("locator") or "").strip()
            if text and locator:
                lines.append(f"{text} [{locator}]")
            elif text:
                lines.append(text)
    return lines


def bundle_excerpt_lines(bundle_data: dict[str, Any]) -> list[str]:
    """Flatten bundle excerpts into note-friendly strings."""
    lines: list[str] = []
    for item in bundle_data.get("excerpts", []):
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            if text:
                lines.append(text)
    return lines


def bundle_artifacts(bundle_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return structured artifact metadata from a loaded bundle."""
    items: list[dict[str, Any]] = []
    for item in bundle_data.get("artifacts", []):
        if isinstance(item, dict) and str(item.get("kind") or "").strip():
            items.append(dict(item))
    return items


def bundle_provenance_lines(
    bundle_data: dict[str, Any], *, include_paths: bool = True
) -> list[str]:
    """Build packet/export provenance lines from a source bundle."""
    lines = [str(item).strip() for item in bundle_data.get("provenance", []) if str(item).strip()]
    canonical = bundle_data.get("canonical_source")
    if isinstance(canonical, dict):
        if canonical.get("canonical_url"):
            lines.append(f"Canonical URL: {canonical['canonical_url']}")
        elif canonical.get("url"):
            lines.append(f"URL: {canonical['url']}")
        if canonical.get("provider"):
            lines.append(f"Provider: {canonical['provider']}")
        if canonical.get("source_type"):
            lines.append(f"Source Type: {canonical['source_type']}")
    if include_paths:
        normalized = bundle_data.get("normalized_text")
        if isinstance(normalized, dict) and normalized.get("path"):
            lines.append(f"Normalized Text: {normalized['path']}")
    if bundle_data.get("capture_agent"):
        lines.append(f"Capture Agent: {bundle_data['capture_agent']}")
    if bundle_data.get("capture_method"):
        lines.append(f"Capture Method: {bundle_data['capture_method']}")
    return lines


def _metadata(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _string_list(primary: Any, fallback: list[str] | None) -> list[str]:
    source = primary if primary is not None else fallback
    if not isinstance(source, list):
        return []
    values: list[str] = []
    for item in source:
        text = str(item).strip()
        if text:
            values.append(text)
    return values


def _modalities(primary: Any, fallback: list[str] | None) -> list[str]:
    values = _string_list(primary, fallback)
    if values:
        return values
    return ["text"]


def _citations(primary: Any, fallback: list[str] | None) -> list[dict[str, Any]]:
    source = primary if primary is not None else fallback
    if not isinstance(source, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in source:
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            if text:
                normalized.append(
                    {
                        "text": text,
                        "locator": str(item.get("locator") or "").strip() or None,
                        "source": str(item.get("source") or "").strip() or None,
                    }
                )
            continue
        text = str(item).strip()
        if text:
            normalized.append({"text": text, "locator": None, "source": None})
    return normalized


def _excerpts(primary: Any, fallback: list[str] | None) -> list[dict[str, Any]]:
    source = primary if primary is not None else fallback
    if not isinstance(source, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in source:
        if isinstance(item, dict):
            text = str(item.get("text") or "").strip()
            if text:
                normalized.append(
                    {
                        "text": text,
                        "locator": str(item.get("locator") or "").strip() or None,
                        "modality": str(item.get("modality") or "").strip() or None,
                        "citation": str(item.get("citation") or "").strip() or None,
                    }
                )
            continue
        text = str(item).strip()
        if text:
            normalized.append({"text": text, "locator": None, "modality": None, "citation": None})
    return normalized


def _artifacts(primary: Any, fallback: list[dict[str, object]] | None) -> list[dict[str, Any]]:
    source = primary if primary is not None else fallback
    if not isinstance(source, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in source:
        if not isinstance(item, dict):
            continue
        kind = str(item.get("kind") or "").strip()
        if not kind:
            continue
        normalized.append(
            {
                "kind": kind,
                "label": str(item.get("label") or "").strip() or None,
                "uri": str(item.get("uri") or "").strip() or None,
                "mime_type": str(item.get("mime_type") or "").strip() or None,
                "metadata": _metadata(item.get("metadata")),
            }
        )
    return normalized
