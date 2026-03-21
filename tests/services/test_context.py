"""Tests for ContextAssembler polaris integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.context import ContextAssembler


@pytest.fixture
def vault(tmp_path: Path) -> Vault:
    """A minimal vault for context assembly tests."""
    from ztlctl.services.init import InitService

    InitService.init_vault(tmp_path, name="ctx-test-vault")
    settings = ZtlSettings.from_cli(vault_root=tmp_path)
    return Vault(settings)


@pytest.fixture
def session_row(vault: Vault) -> Any:
    """An open session row for use with assemble()."""
    from ztlctl.services.session import SessionService

    result = SessionService(vault).start("polaris test topic")
    assert result.ok
    session_id = result.data["id"]

    from ztlctl.infrastructure.database.schema import nodes
    from sqlalchemy import select

    with vault.engine.connect() as conn:
        row = conn.execute(
            select(nodes).where(nodes.c.id == session_id)
        ).fetchone()
    return row


class TestContextAssemblerPolaris:
    """Tests for polaris integration in ContextAssembler.assemble() Layer 1."""

    def test_assemble_includes_polaris_key_when_file_exists(
        self, vault: Vault, session_row: Any
    ) -> None:
        """assemble() includes 'polaris' key in layers when polaris file exists."""
        polaris_dir = vault.root / "garden" / "groves"
        polaris_dir.mkdir(parents=True, exist_ok=True)
        (polaris_dir / "polaris.md").write_text(
            "## Mission\nBuild tools.\n## Current Priorities\n1. Ship.\n",
            encoding="utf-8",
        )

        assembler = ContextAssembler(vault)
        result = assembler.assemble(session_row)

        assert result.ok
        layers = result.data["layers"]
        assert "polaris" in layers
        assert layers["polaris"] is not None
        assert "Mission" in layers["polaris"]

    def test_assemble_polaris_none_when_file_missing(
        self, vault: Vault, session_row: Any
    ) -> None:
        """assemble() sets polaris to None when garden/groves/polaris.md does not exist."""
        # Ensure the polaris file does not exist
        polaris_path = vault.root / "garden" / "groves" / "polaris.md"
        if polaris_path.exists():
            polaris_path.unlink()

        assembler = ContextAssembler(vault)
        result = assembler.assemble(session_row)

        assert result.ok
        layers = result.data["layers"]
        assert "polaris" in layers
        assert layers["polaris"] is None

    def test_assemble_polaris_truncated_when_exceeds_500_tokens(
        self, vault: Vault, session_row: Any
    ) -> None:
        """Polaris content is truncated to ~500 tokens when it exceeds the budget."""
        polaris_dir = vault.root / "garden" / "groves"
        polaris_dir.mkdir(parents=True, exist_ok=True)
        # Write more than 2000 characters (roughly > 500 tokens at 4 chars/token)
        large_content = "## Mission\n" + ("x " * 1500) + "\n## Current Priorities\n1. Stuff.\n"
        (polaris_dir / "polaris.md").write_text(large_content, encoding="utf-8")

        assembler = ContextAssembler(vault)
        result = assembler.assemble(session_row)

        assert result.ok
        layers = result.data["layers"]
        assert "polaris" in layers
        assert layers["polaris"] is not None
        assert "[... polaris truncated" in layers["polaris"]

    def test_assemble_polaris_tokens_counted_in_layer_1(
        self, vault: Vault, session_row: Any
    ) -> None:
        """Polaris tokens are included in the total token count."""
        polaris_dir = vault.root / "garden" / "groves"
        polaris_dir.mkdir(parents=True, exist_ok=True)
        polaris_content = "## Mission\nBuild things.\n## Current Priorities\n1. Ship.\n"
        (polaris_dir / "polaris.md").write_text(polaris_content, encoding="utf-8")

        # Assemble without polaris
        polaris_path = vault.root / "garden" / "groves" / "polaris.md"
        polaris_path.unlink()
        assembler_no_polaris = ContextAssembler(vault)
        result_without = assembler_no_polaris.assemble(session_row)
        tokens_without = result_without.data["total_tokens"]

        # Write polaris back
        polaris_path.write_text(polaris_content, encoding="utf-8")
        assembler_with = ContextAssembler(vault)
        result_with = assembler_with.assemble(session_row)
        tokens_with = result_with.data["total_tokens"]

        # Having polaris should increase token count
        assert tokens_with > tokens_without
