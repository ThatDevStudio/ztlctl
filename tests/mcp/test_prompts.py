"""Tests for MCP prompt implementations."""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.mcp.generator import tool_catalog
from ztlctl.mcp.prompts import (
    capture_multimodal_source_impl,
    capture_web_source_impl,
    decision_record_impl,
    knowledge_capture_impl,
    prompt_catalog,
    register_prompts,
    research_session_impl,
    topic_decision_impl,
    topic_learn_impl,
    topic_review_impl,
    vault_orientation_impl,
)
from ztlctl.mcp.resources import resource_catalog


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

    def test_includes_updated_review_resource_descriptions(self, vault: Vault):
        prompt = vault_orientation_impl(vault)
        assert "External review workbench snapshot" in prompt
        assert "Enrichment backlog signals focused on stale seeds and orphan notes." in prompt

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


class TestResearchAndWorkflowPrompts:
    """Tests for the remaining _impl prompt functions."""

    def test_research_session_impl_contains_topic(self) -> None:
        prompt = research_session_impl("machine learning")
        assert "machine learning" in prompt
        assert "create_log" in prompt
        assert "session_close" in prompt

    def test_knowledge_capture_impl_contains_workflow(self) -> None:
        prompt = knowledge_capture_impl()
        assert "create_note" in prompt
        assert "search" in prompt
        assert "reweave" in prompt

    def test_decision_record_impl_contains_topic(self) -> None:
        prompt = decision_record_impl("database selection")
        assert "database selection" in prompt
        assert "create_note" in prompt
        assert "Decision" in prompt

    def test_topic_learn_impl_contains_topic(self) -> None:
        prompt = topic_learn_impl("distributed systems")
        assert "distributed systems" in prompt
        assert "topic_packet" in prompt
        assert 'mode="learn"' in prompt

    def test_topic_review_impl_contains_topic(self) -> None:
        prompt = topic_review_impl("security")
        assert "security" in prompt
        assert "topic_packet" in prompt
        assert 'mode="review"' in prompt

    def test_topic_decision_impl_contains_topic(self) -> None:
        prompt = topic_decision_impl("api design")
        assert "api design" in prompt
        assert "topic_packet" in prompt
        assert 'mode="decision"' in prompt


class TestPromptCatalog:
    """Tests for prompt_catalog function."""

    def test_catalog_has_expected_prompts(self) -> None:
        catalog = prompt_catalog()
        names = {entry["name"] for entry in catalog}
        assert "research_session" in names
        assert "knowledge_capture" in names
        assert "vault_orientation" in names
        assert "decision_record" in names

    def test_catalog_returns_tuple(self) -> None:
        catalog = prompt_catalog()
        assert isinstance(catalog, tuple)
        assert len(catalog) >= 9

    def test_catalog_with_none_vault(self) -> None:
        catalog = prompt_catalog(vault=None)
        assert isinstance(catalog, tuple)
        assert len(catalog) == 9

    def test_capture_web_source_no_topic(self) -> None:
        prompt = capture_web_source_impl("https://example.com")
        assert "ztlctl://capture/spec" in prompt
        assert "source_bundle" in prompt
        # No topic scoping
        assert "topic" not in prompt or 'topic="' not in prompt

    def test_capture_multimodal_no_topic(self) -> None:
        prompt = capture_multimodal_source_impl("audio.mp3", modality="audio")
        assert "audio" in prompt
        assert "source_bundle" in prompt


_PROMPT_SAMPLE_ARGS: dict[str, dict[str, str]] = {
    "research_session": {"topic": "test-topic"},
    "knowledge_capture": {},
    "vault_orientation": {},
    "decision_record": {"topic": "test-decision"},
    "topic_learn": {"topic": "test-topic"},
    "topic_review": {"topic": "test-topic"},
    "topic_decision": {"topic": "test-topic"},
    "capture_web_source": {"source": "https://example.com"},
    "capture_multimodal_source": {"source": "file.pdf", "modality": "image"},
}


class TestRegisterPrompts:
    """Tests for register_prompts using a dummy server."""

    class DummyServer:
        def __init__(self, sample_args: dict) -> None:
            self.registered: list[str] = []
            self._sample_args = sample_args
            self.results: dict[str, str] = {}

        def prompt(self):
            def decorator(fn):
                self.registered.append(fn.__name__)
                # Invoke the handler to exercise the inner function body
                kwargs = self._sample_args.get(fn.__name__, {})
                try:
                    result = fn(**kwargs)
                    self.results[fn.__name__] = str(result)
                except Exception as exc:
                    self.results[fn.__name__] = f"ERROR:{exc}"
                return fn

            return decorator

    def test_register_prompts_registers_all_core_prompts(self, vault: Vault):
        server = self.DummyServer(_PROMPT_SAMPLE_ARGS)
        register_prompts(server, vault)

        expected = {
            "research_session",
            "knowledge_capture",
            "vault_orientation",
            "decision_record",
            "topic_learn",
            "topic_review",
            "topic_decision",
            "capture_web_source",
            "capture_multimodal_source",
        }
        assert expected.issubset(set(server.registered))

    def test_register_prompts_handlers_produce_strings(self, vault: Vault):
        server = self.DummyServer(_PROMPT_SAMPLE_ARGS)
        register_prompts(server, vault)

        for name, result in server.results.items():
            assert not result.startswith("ERROR:"), f"{name} raised: {result}"
            assert isinstance(result, str) and len(result) > 0

    def test_register_prompts_registers_correct_count(self, vault: Vault):
        server = self.DummyServer(_PROMPT_SAMPLE_ARGS)
        register_prompts(server, vault)
        assert len(server.registered) == 9
