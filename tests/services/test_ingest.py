"""Tests for IngestService."""

from __future__ import annotations

from pathlib import Path

import pluggy

from ztlctl.domain.content import parse_frontmatter
from ztlctl.plugins.contracts import SourceFetchResult, SourceProviderContribution
from ztlctl.services.ingest import IngestService

hookimpl = pluggy.HookimplMarker("ztlctl")


class _MockSourceProviderPlugin:
    @hookimpl
    def register_source_providers(self) -> list[SourceProviderContribution]:
        return [
            SourceProviderContribution(
                name="mock-web",
                description="Mock web provider.",
                schemes=("https",),
                fetch=lambda request: SourceFetchResult(
                    body_text="Fetched source body",
                    title="Fetched Article",
                    canonical_url=request.content,
                    content_type="text/html",
                    source_type="web",
                    summary_hint="Provider summary",
                    key_points=("point one", "point two"),
                    citations=("Citation: example",),
                ),
            )
        ]


class TestIngestService:
    def test_ingest_text_creates_structured_reference(self, vault) -> None:
        result = IngestService(vault).ingest_text(
            "OAuth Notes",
            "Primary source body",
            target_type="reference",
            summary="Short summary",
        )

        assert result.ok
        path = vault.root / result.data["path"]
        content = path.read_text(encoding="utf-8")
        assert "## Summary" in content
        assert "Short summary" in content
        assert "## Notes" in content
        assert "Primary source body" in content
        assert "## Provenance" in content

    def test_ingest_file_creates_note(self, vault, tmp_path: Path) -> None:
        source = tmp_path / "capture.md"
        source.write_text("# Imported\n\nBody text", encoding="utf-8")

        result = IngestService(vault).ingest_file(source, target_type="note", title="Imported Note")

        assert result.ok
        path = vault.root / result.data["path"]
        assert "Imported" in path.read_text(encoding="utf-8")

    def test_ingest_dry_run_does_not_write_files(self, vault) -> None:
        notes_before = list((vault.root / "notes").rglob("*.md"))

        result = IngestService(vault).ingest_text(
            "Preview Only",
            "Body preview",
            target_type="reference",
            dry_run=True,
        )

        assert result.ok
        assert result.data["title"] == "Preview Only"
        assert list((vault.root / "notes").rglob("*.md")) == notes_before

    def test_ingest_url_without_provider_returns_no_provider(self, vault) -> None:
        result = IngestService(vault).ingest_url(
            "https://example.com/article", target_type="reference"
        )

        assert not result.ok
        assert result.error is not None
        assert result.error.code == "NO_PROVIDER"

    def test_ingest_url_with_provider_populates_provenance(self, vault) -> None:
        vault.init_event_bus(sync=True)
        assert vault.plugin_manager is not None
        vault.plugin_manager.register_plugin(_MockSourceProviderPlugin(), name="mock-provider")

        result = IngestService(vault).ingest_url(
            "https://example.com/article",
            provider="mock-web",
            target_type="reference",
        )

        assert result.ok
        path = vault.root / result.data["path"]
        frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        assert frontmatter["canonical_url"] == "https://example.com/article"
        assert frontmatter["source_provider"] == "mock-web"
        assert frontmatter["source_type"] == "web"
        assert frontmatter.get("language") is None
        assert "Citation: example" in body
        assert "Fetched source body" in body
