"""Tests for MCP prompt implementations."""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.mcp.prompts import (
    capture_multimodal_source_impl,
    capture_web_source_impl,
    vault_orientation_impl,
)
from ztlctl.mcp.resources import resource_catalog
from ztlctl.mcp.tools import tool_catalog


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Vault directory structure."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    """Vault for MCP prompt tests."""
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    return Vault(settings)


class TestVaultOrientation:
    """Tests for vault_orientation_impl."""

    def test_includes_every_tool_category(self, vault: Vault):
        prompt = vault_orientation_impl(vault)
        categories = {entry["category"] for entry in tool_catalog()}
        for category in categories:
            assert category.replace("_", " ").title() in prompt

    def test_includes_every_resource_uri(self, vault: Vault):
        prompt = vault_orientation_impl(vault)
        for resource in resource_catalog():
            assert resource["uri"] in prompt

    def test_includes_discovery_rule(self, vault: Vault):
        prompt = vault_orientation_impl(vault)
        assert "start with `discover_tools`" in prompt
        assert "call `describe_tool`" in prompt


class TestCapturePrompts:
    def test_capture_web_prompt_mentions_capture_spec_and_source_bundle(self) -> None:
        prompt = capture_web_source_impl("https://example.com", topic="architecture")
        assert "ztlctl://capture/spec" in prompt
        assert "source_bundle" in prompt
        assert 'topic="architecture"' in prompt

    def test_capture_multimodal_prompt_mentions_modality(self) -> None:
        prompt = capture_multimodal_source_impl("slides.pdf", modality="image")
        assert "source_bundle" in prompt
        assert "image" in prompt
