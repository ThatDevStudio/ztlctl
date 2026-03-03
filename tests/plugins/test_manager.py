"""Tests for PluginManager — discovery, registration, and hook relay."""

from __future__ import annotations

from pathlib import Path

import click
import pluggy
import pytest

from ztlctl.domain.content import CONTENT_REGISTRY, NoteModel, get_content_model
from ztlctl.plugins.contracts import (
    CliCommandContribution,
    McpPromptContribution,
    McpResourceContribution,
    McpToolContribution,
    SourceFetchResult,
    SourceProviderContribution,
    VaultInitContext,
    VaultInitInstruction,
    VaultInitStepContribution,
    VaultInitStepResult,
    WorkflowModuleContribution,
    WorkspaceProfileContribution,
)
from ztlctl.plugins.manager import PluginManager

hookimpl = pluggy.HookimplMarker("ztlctl")


class _DummyPlugin:
    """Minimal plugin for registration tests."""

    @hookimpl
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        pass


class _CustomSubtypeModel(NoteModel):
    _subtype_name = "plugin_note"


class _ClassBasedPlugin:
    @hookimpl
    def post_check(self, issues_found: int, issues_fixed: int) -> None:
        pass


class _ContentModelPlugin:
    @hookimpl
    def register_content_models(self) -> dict[str, type[NoteModel]]:
        return {"plugin_note": _CustomSubtypeModel}


class _ConflictingContentModelPlugin:
    @hookimpl
    def register_content_models(self) -> dict[str, type[NoteModel]]:
        return {"decision": _CustomSubtypeModel}


class _ContributionPlugin:
    @hookimpl
    def register_cli_commands(self) -> list[CliCommandContribution]:
        return [CliCommandContribution(name="plugin-hello", command=click.Command("plugin-hello"))]

    @hookimpl
    def register_mcp_tools(self) -> list[McpToolContribution]:
        return [
            McpToolContribution(
                name="plugin_tool",
                handler=lambda vault: {
                    "ok": True,
                    "op": "plugin_tool",
                    "data": {"root": str(vault.root)},
                },
                catalog_entry={
                    "name": "plugin_tool",
                    "category": "query",
                    "description": "Plugin tool.",
                    "when_to_use": "Testing plugin MCP tool registration.",
                    "avoid_when": "The core surface is sufficient.",
                    "side_effect": "read",
                    "common_errors": (),
                    "args_guidance": {},
                },
            )
        ]

    @hookimpl
    def register_mcp_resources(self) -> list[McpResourceContribution]:
        return [
            McpResourceContribution(
                uri="ztlctl://plugin/resource",
                description="Plugin resource.",
                handler=lambda vault: {"vault": str(vault.root)},
            )
        ]

    @hookimpl
    def register_mcp_prompts(self) -> list[McpPromptContribution]:
        return [
            McpPromptContribution(
                name="plugin_prompt",
                description="Plugin prompt.",
                handler=lambda vault: f"Vault: {vault.root}",
            )
        ]

    @hookimpl
    def register_workflow_modules(self) -> list[WorkflowModuleContribution]:
        return [
            WorkflowModuleContribution(
                name="plugin_module",
                render=lambda context: f"# Plugin Module\n\nVault: {context['vault_name']}",
            )
        ]

    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [
            WorkspaceProfileContribution(
                profile_id="plugin-profile",
                description="Plugin profile.",
                aliases=("plugin-alias",),
                managed_paths=(".plugin",),
            )
        ]

    @hookimpl
    def register_vault_init_steps(self) -> list[VaultInitStepContribution]:
        return [
            VaultInitStepContribution(
                step_id="plugin-init-step",
                description="Plugin init step.",
                order=250,
                profiles=("plugin-profile",),
                run=lambda context: VaultInitStepResult(
                    files_created=(".plugin/config.json",),
                    instructions=(
                        VaultInitInstruction(
                            instruction_id="plugin.verify",
                            title="Verify plugin setup",
                            body=f"Profile: {context.profile}",
                        ),
                    ),
                ),
            )
        ]

    @hookimpl
    def register_source_providers(self) -> list[SourceProviderContribution]:
        return [
            SourceProviderContribution(
                name="mock-provider",
                description="Mock provider.",
                schemes=("https",),
                fetch=lambda request: SourceFetchResult(
                    body_text=request.content,
                    title="Fetched",
                ),
            )
        ]


class _DuplicateContributionPlugin:
    @hookimpl
    def register_cli_commands(self) -> list[CliCommandContribution]:
        return [CliCommandContribution(name="plugin-hello", command=click.Command("plugin-hello"))]

    @hookimpl
    def register_workspace_profiles(self) -> list[WorkspaceProfileContribution]:
        return [WorkspaceProfileContribution(profile_id="plugin-profile", description="Duplicate.")]

    @hookimpl
    def register_vault_init_steps(self) -> list[VaultInitStepContribution]:
        return [
            VaultInitStepContribution(
                step_id="plugin-init-step",
                description="Duplicate init step.",
                run=lambda _context: VaultInitStepResult(),
            )
        ]


class _MalformedContributionPlugin:
    @hookimpl
    def register_source_providers(self) -> list[object]:
        return ["bad-provider"]

    @hookimpl
    def register_vault_init_steps(self) -> list[object]:
        return ["bad-step"]


class TestPluginManager:
    """Tests for the PluginManager class."""

    def test_hook_relay_accessible(self):
        pm = PluginManager()
        assert hasattr(pm.hook, "post_create")
        assert hasattr(pm.hook, "post_session_close")

    def test_register_plugin(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin, name="dummy")
        assert "dummy" in pm.list_plugin_names()

    def test_register_plugin_default_name(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin)
        assert "_DummyPlugin" in pm.list_plugin_names()

    def test_unregister_plugin(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin, name="dummy")
        pm.unregister(plugin)
        assert "dummy" not in pm.list_plugin_names()

    def test_discover_loads_entry_points(self):
        """Discover loads the shipped built-in entry-point plugins."""
        pm = PluginManager()
        names = pm.discover_and_load()
        assert pm.is_loaded is True
        assert any("git" in n.lower() or "Git" in n for n in names)
        assert any("obsidian" in n.lower() or "Obsidian" in n for n in names)

    def test_is_loaded_false_before_discover(self):
        pm = PluginManager()
        assert pm.is_loaded is False

    def test_get_plugins_returns_registered(self):
        pm = PluginManager()
        plugin = _DummyPlugin()
        pm.register_plugin(plugin, name="test")
        plugins = pm.get_plugins()
        assert plugin in plugins

    @pytest.mark.parametrize(
        "hook_name",
        [
            "post_create",
            "post_update",
            "post_close",
            "post_reweave",
            "post_session_start",
            "post_session_close",
            "post_check",
            "post_init",
            "post_init_profile",
            "register_content_models",
            "register_workspace_profiles",
            "register_vault_init_steps",
        ],
    )
    def test_all_hookspecs_registered(self, hook_name: str):
        """All lifecycle and setup hookspecs should be available on the hook relay."""
        pm = PluginManager()
        assert hasattr(pm.hook, hook_name)

    def test_discover_registers_plugin_content_models(self) -> None:
        pm = PluginManager()
        original_registry = CONTENT_REGISTRY.copy()
        pm.register_plugin(_ContentModelPlugin(), name="content-models")

        try:
            pm.discover_and_load(local_dir=None)
            assert get_content_model("note", "plugin_note") is _CustomSubtypeModel
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

    def test_conflicting_plugin_content_models_warn_and_skip(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        pm = PluginManager()
        original_registry = CONTENT_REGISTRY.copy()
        pm.register_plugin(_ConflictingContentModelPlugin(), name="conflicting-models")

        try:
            with caplog.at_level("WARNING"):
                pm.discover_and_load(local_dir=None)
            assert get_content_model("note", "decision").__name__ == "DecisionModel"
            assert "Skipping content model registration" in caplog.text
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

    def test_register_plugin_after_load_registers_content_models(self) -> None:
        pm = PluginManager()
        original_registry = CONTENT_REGISTRY.copy()

        try:
            pm.discover_and_load(local_dir=None)
            pm.register_plugin(_ContentModelPlugin(), name="runtime-content-models")
            assert get_content_model("note", "plugin_note") is _CustomSubtypeModel
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

    def test_collects_vault_init_step_contributions(self) -> None:
        pm = PluginManager()
        pm.register_plugin(_ContributionPlugin(), name="contrib")
        pm.discover_and_load(local_dir=None, include_entrypoints=False)

        steps = pm.vault_init_step_contributions()

        assert len(steps) == 1
        assert steps[0].step_id == "plugin-init-step"
        result = steps[0].run(
            VaultInitContext(
                vault_root=Path("/tmp/vault"),
                vault_name="vault",
                profile="plugin-profile",
                tone="research-partner",
            )
        )
        assert result.files_created == (".plugin/config.json",)
        assert result.instructions[0].title == "Verify plugin setup"

    def test_duplicate_vault_init_steps_warn_and_skip(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        pm = PluginManager()
        pm.register_plugin(_ContributionPlugin(), name="contrib")
        pm.register_plugin(_DuplicateContributionPlugin(), name="dup")
        pm.discover_and_load(local_dir=None, include_entrypoints=False)

        with caplog.at_level("WARNING"):
            steps = pm.vault_init_step_contributions()

        assert [step.step_id for step in steps] == ["plugin-init-step"]
        assert "Skipping duplicate plugin contribution 'plugin-init-step'" in caplog.text

    def test_invalid_vault_init_steps_warn_and_skip(self, caplog: pytest.LogCaptureFixture) -> None:
        pm = PluginManager()
        pm.register_plugin(_MalformedContributionPlugin(), name="bad-steps")
        pm.discover_and_load(local_dir=None, include_entrypoints=False)

        with caplog.at_level("WARNING"):
            steps = pm.vault_init_step_contributions()

        assert steps == []
        assert "Skipping invalid register_vault_init_steps contribution" in caplog.text

    def test_normalize_plugin_instances_instantiates_registered_classes(self) -> None:
        pm = PluginManager()
        pm._pm.register(_ClassBasedPlugin, name="class-based")

        pm._normalize_plugin_instances()

        plugins = [p for p in pm.get_plugins() if pm._pm.get_name(p) == "class-based"]
        assert len(plugins) == 1
        assert isinstance(plugins[0], _ClassBasedPlugin)

    def test_collects_public_contributions(self) -> None:
        pm = PluginManager()
        pm.register_plugin(_ContributionPlugin(), name="contrib")
        pm.discover_and_load(local_dir=None)

        cli = pm.cli_command_contributions()
        tools = pm.mcp_tool_contributions()
        resources = pm.mcp_resource_contributions()
        prompts = pm.mcp_prompt_contributions()
        modules = pm.workflow_module_contributions()
        profiles = pm.workspace_profile_contributions()
        providers = pm.source_provider_contributions()

        assert any(item.name == "plugin-hello" for item in cli)
        assert any(item.name == "plugin_tool" for item in tools)
        assert any(item.uri == "ztlctl://plugin/resource" for item in resources)
        assert any(item.name == "plugin_prompt" for item in prompts)
        assert any(item.name == "plugin_module" for item in modules)
        assert any(item.profile_id == "plugin-profile" for item in profiles)
        assert any(item.name == "mock-provider" for item in providers)

    def test_duplicate_contributions_warn_and_skip(self, caplog: pytest.LogCaptureFixture) -> None:
        pm = PluginManager()
        pm.register_plugin(_ContributionPlugin(), name="contrib-a")
        pm.register_plugin(_DuplicateContributionPlugin(), name="contrib-b")
        pm.discover_and_load(local_dir=None)

        with caplog.at_level("WARNING"):
            commands = pm.cli_command_contributions()

        assert [item.name for item in commands].count("plugin-hello") == 1
        assert "Skipping duplicate plugin contribution" in caplog.text

    def test_reserved_workspace_profiles_warn_and_skip(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        pm = PluginManager()
        pm.register_plugin(_ContributionPlugin(), name="contrib")
        pm.discover_and_load(local_dir=None)

        with caplog.at_level("WARNING"):
            profiles = pm.workspace_profile_contributions(reserved_names={"plugin-profile"})

        assert all(item.profile_id != "plugin-profile" for item in profiles)
        assert "Skipping reserved plugin contribution" in caplog.text

    def test_duplicate_workspace_profiles_warn_and_skip(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        pm = PluginManager()
        pm.register_plugin(_ContributionPlugin(), name="contrib-a")
        pm.register_plugin(_DuplicateContributionPlugin(), name="contrib-b")
        pm.discover_and_load(local_dir=None)

        with caplog.at_level("WARNING"):
            profiles = pm.workspace_profile_contributions()

        assert [item.profile_id for item in profiles].count("plugin-profile") == 1
        assert "Skipping duplicate plugin contribution" in caplog.text

    def test_malformed_contribution_warns_and_skips(self, caplog: pytest.LogCaptureFixture) -> None:
        pm = PluginManager()
        pm.register_plugin(_MalformedContributionPlugin(), name="bad")
        pm.discover_and_load(local_dir=None)

        with caplog.at_level("WARNING"):
            providers = pm.source_provider_contributions()

        assert providers == []
        assert "Skipping invalid register_source_providers contribution" in caplog.text
