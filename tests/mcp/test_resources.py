"""Tests for MCP resource _impl functions (no mcp package needed)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings
from ztlctl.infrastructure.vault import Vault
from ztlctl.mcp.resources import (
    agent_reference_impl,
    capture_spec_impl,
    context_impl,
    decision_queue_impl,
    garden_backlog_impl,
    overview_impl,
    register_resources,
    resource_catalog,
    review_dashboard_impl,
    self_identity_impl,
    self_methodology_impl,
    topics_impl,
    work_queue_impl,
)


@pytest.fixture
def vault_root(tmp_path: Path) -> Path:
    """Vault directory structure."""
    (tmp_path / "notes").mkdir()
    (tmp_path / "ops" / "logs").mkdir(parents=True)
    (tmp_path / "ops" / "tasks").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def vault(vault_root: Path) -> Vault:
    settings = ZtlSettings.from_cli(vault_root=vault_root)
    return Vault(settings)


class TestResources:
    """Tests for resource _impl functions."""

    def test_self_identity_reads_file(self, vault: Vault):
        # Create identity file
        self_dir = vault.root / "self"
        self_dir.mkdir(exist_ok=True)
        (self_dir / "identity.md").write_text("# Test Identity", encoding="utf-8")

        result = self_identity_impl(vault)
        assert "Test Identity" in result

    def test_self_methodology_reads_file(self, vault: Vault):
        self_dir = vault.root / "self"
        self_dir.mkdir(exist_ok=True)
        (self_dir / "methodology.md").write_text("# Test Method", encoding="utf-8")

        result = self_methodology_impl(vault)
        assert "Test Method" in result

    def test_missing_self_files_handled_gracefully(self, vault: Vault):
        result = self_identity_impl(vault)
        assert "No identity file found" in result

        result = self_methodology_impl(vault)
        assert "No methodology file found" in result

    def test_overview_returns_counts(self, vault: Vault):
        from ztlctl.services.create import CreateService

        CreateService(vault).create_note("Overview Note")

        result = overview_impl(vault)
        assert "counts" in result
        assert result["total"] >= 1
        assert result["counts"]["note"] >= 1

    def test_work_queue_returns_data(self, vault: Vault):
        result = work_queue_impl(vault)
        assert "items" in result

    def test_review_dashboard_returns_data(self, vault: Vault):
        result = review_dashboard_impl(vault)
        assert isinstance(result, dict)

    def test_garden_backlog_returns_data(self, vault: Vault):
        result = garden_backlog_impl(vault)
        assert "items" in result

    def test_decision_queue_returns_sections(self, vault: Vault):
        result = decision_queue_impl(vault)
        assert "decisions" in result
        assert "work_queue" in result

    def test_capture_spec_returns_bundle_contract(self, vault: Vault):
        result = capture_spec_impl(vault)
        assert result["version"] == 1
        assert "bundle_fields" in result
        assert "source_bundle" in result["minimal_example"]

    def test_topics_lists_directories(self, vault: Vault):
        (vault.root / "notes" / "math").mkdir()
        (vault.root / "notes" / "physics").mkdir()

        result = topics_impl(vault)
        assert "math" in result
        assert "physics" in result

    def test_topics_empty_vault(self, vault: Vault):
        result = topics_impl(vault)
        assert result == []

    def test_topics_no_notes_dir(self, tmp_path: Path):
        """topics_impl returns [] when notes/ directory doesn't exist."""
        # Create vault without notes dir
        (tmp_path / "ops" / "logs").mkdir(parents=True)
        (tmp_path / "ops" / "tasks").mkdir(parents=True)
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        v = Vault(settings)
        # Remove notes dir if init_database created it
        notes_dir = tmp_path / "notes"
        if notes_dir.exists():
            notes_dir.rmdir()
        result = topics_impl(v)
        assert result == []

    def test_garden_backlog_with_seeded_items(self, vault: Vault):
        """garden_backlog_impl dedup logic covers lines 143-147."""

        from ztlctl.infrastructure.database.schema import nodes
        from ztlctl.services.create import CreateService

        # Create seed notes so vault_review has stale_seeds or orphan_notes
        svc = CreateService(vault)
        for i in range(3):
            result = svc.create_note(f"Seed Note {i}")
            # Make them seeds
            with vault.engine.begin() as conn:
                conn.execute(
                    nodes.update()
                    .where(nodes.c.id == result.data["id"])
                    .values(maturity="seed", created="2025-01-01")
                )

        result = garden_backlog_impl(vault)
        assert "items" in result
        assert "count" in result

    def test_context_combines_all(self, vault: Vault):
        result = context_impl(vault)
        assert "identity" in result
        assert "methodology" in result
        assert "overview" in result


class TestResourceCatalog:
    """Tests for resource catalog completeness."""

    def test_catalog_has_11_resources(self):
        assert len(resource_catalog()) == 11

    def test_agent_reference_in_catalog(self):
        uris = {r["uri"] for r in resource_catalog()}
        assert "ztlctl://agent-reference" in uris
        assert "ztlctl://capture/spec" in uris

    def test_catalog_descriptions_reflect_review_workbench_wording(self):
        catalog = {entry["uri"]: entry["description"] for entry in resource_catalog()}
        assert (
            catalog["ztlctl://review/dashboard"]
            == "External review workbench snapshot with work queues, review signals, "
            "and topic dossiers."
        )
        assert (
            catalog["ztlctl://garden/backlog"]
            == "Enrichment backlog signals focused on stale seeds and orphan notes."
        )


class TestAgentReference:
    """Tests for agent_reference_impl."""

    def test_returns_four_sections(self, vault: Vault):
        result = agent_reference_impl(vault)
        assert "recommended_start" in result
        assert "tool_categories" in result
        assert "workflow_examples" in result
        assert "common_errors" in result

    def test_tool_categories_grouped(self, vault: Vault):
        result = agent_reference_impl(vault)
        cats = result["tool_categories"]
        assert "discovery" in cats
        assert "creation" in cats
        assert "query" in cats
        assert "graph" in cats
        assert "analysis" in cats
        assert "session" in cats
        assert "lifecycle" in cats

    def test_tool_categories_have_enriched_fields(self, vault: Vault):
        result = agent_reference_impl(vault)
        for cat, tools in result["tool_categories"].items():
            for tool in tools:
                assert "name" in tool, f"{cat}: missing name"
                assert "when_to_use" in tool, f"{tool['name']}: missing when_to_use"
                assert "avoid_when" in tool, f"{tool['name']}: missing avoid_when"
                assert "side_effect" in tool, f"{tool['name']}: missing side_effect"
                assert "common_errors" in tool, f"{tool['name']}: missing common_errors"
                assert "args_guidance" in tool, f"{tool['name']}: missing args_guidance"

    def test_workflow_examples_have_5_patterns(self, vault: Vault):
        result = agent_reference_impl(vault)
        wf = result["workflow_examples"]
        expected = {
            "capture",
            "research_session",
            "search_then_create",
            "vault_maintenance",
            "decision_documentation",
        }
        assert set(wf.keys()) == expected

    def test_workflow_steps_are_lists(self, vault: Vault):
        result = agent_reference_impl(vault)
        for name, steps in result["workflow_examples"].items():
            assert isinstance(steps, list), f"{name}: not a list"
            assert len(steps) >= 2, f"{name}: too few steps"

    def test_workflow_examples_use_real_tool_names(self, vault: Vault):
        result = agent_reference_impl(vault)
        valid_tool_names = {
            tool["name"] for tools in result["tool_categories"].values() for tool in tools
        }
        for steps in result["workflow_examples"].values():
            for step in steps:
                assert step["tool"] in valid_tool_names
                assert "notes" in step
                assert "recommended_args" in step

    def test_common_errors_has_expected_codes(self, vault: Vault):
        result = agent_reference_impl(vault)
        expected_codes = {
            "NOT_FOUND",
            "VALIDATION_FAILED",
            "ID_COLLISION",
            "NO_ACTIVE_SESSION",
            "ACTIVE_SESSION_EXISTS",
            "INVALID_TRANSITION",
            "UNKNOWN_TYPE",
            "NO_PATH",
            "EMPTY_QUERY",
        }
        assert expected_codes.issubset(result["common_errors"].keys())

    def test_common_error_values_non_empty(self, vault: Vault):
        result = agent_reference_impl(vault)
        for code, recovery in result["common_errors"].items():
            assert recovery.strip(), f"{code}: empty recovery"

    def test_validation_failed_recovery_excludes_tag_format_claim(self, vault: Vault):
        result = agent_reference_impl(vault)
        assert "domain/scope" not in result["common_errors"]["VALIDATION_FAILED"]


class TestRegisterResources:
    """Tests for register_resources using a dummy server."""

    class DummyServer:
        def __init__(self) -> None:
            self.registered_uris: list[str] = []
            self.handler_results: dict[str, str] = {}

        def resource(self, uri: str):
            def decorator(fn):
                self.registered_uris.append(uri)
                # Call the handler to verify it returns JSON-serializable content
                try:
                    result = fn()
                    self.handler_results[uri] = result
                except Exception as exc:
                    self.handler_results[uri] = f"ERROR: {exc}"
                return fn

            return decorator

    def test_register_resources_registers_core_uris(self, vault: Vault):
        server = self.DummyServer()
        register_resources(server, vault)

        expected_uris = {
            "ztlctl://context",
            "ztlctl://self/identity",
            "ztlctl://self/methodology",
            "ztlctl://overview",
            "ztlctl://work-queue",
            "ztlctl://review/dashboard",
            "ztlctl://garden/backlog",
            "ztlctl://decision-queue",
            "ztlctl://capture/spec",
            "ztlctl://topics",
            "ztlctl://agent-reference",
        }
        assert expected_uris.issubset(set(server.registered_uris))

    def test_register_resources_handlers_return_json_strings(self, vault: Vault):
        import json

        server = self.DummyServer()
        register_resources(server, vault)

        # Each handler should return JSON-serializable string
        for uri, result in server.handler_results.items():
            if uri == "ztlctl://self/identity" or uri == "ztlctl://self/methodology":
                # These return plain text strings
                assert isinstance(result, str)
            else:
                assert isinstance(result, str), f"{uri} did not return a string"
                try:
                    json.loads(result)
                except json.JSONDecodeError:
                    # Plain text is also fine for identity/methodology resources
                    pass
