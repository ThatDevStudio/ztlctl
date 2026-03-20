"""Tests for ZtlSettings — unified settings with TOML source."""

from pathlib import Path

import pytest

from ztlctl.config.settings import ZtlSettings


class TestZtlSettingsDefaults:
    def test_all_defaults(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """With no TOML and no env vars, all fields use code defaults."""
        monkeypatch.delenv("ZTLCTL_VAULT_ROOT", raising=False)
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.vault_root == tmp_path
        assert settings.json_output is False
        assert settings.quiet is False
        assert settings.verbose is False
        assert settings.vault.name == "my-vault"
        assert settings.workspace.profile == "core"
        assert settings.vault.client == "none"
        assert settings.agent.tone == "research-partner"
        assert settings.reweave.enabled is True

    def test_frozen(self, tmp_path: Path) -> None:
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        with pytest.raises(Exception):
            settings.quiet = True  # type: ignore[misc]


class TestTomlSource:
    def test_loads_from_toml(self, tmp_path: Path) -> None:
        toml = tmp_path / "ztlctl.toml"
        toml.write_text('[vault]\nname = "research-vault"\n[agent]\ntone = "minimal"\n')
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.vault.name == "research-vault"
        assert settings.agent.tone == "minimal"
        assert settings.reweave.enabled is True  # default preserved

    def test_sparse_override(self, tmp_path: Path) -> None:
        """Only overridden fields change — rest keeps defaults."""
        toml = tmp_path / "ztlctl.toml"
        toml.write_text("[reweave]\nmin_score_threshold = 0.4\n")
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.reweave.min_score_threshold == 0.4
        assert settings.reweave.max_links_per_note == 5  # default

    def test_empty_toml_uses_defaults(self, tmp_path: Path) -> None:
        toml = tmp_path / "ztlctl.toml"
        toml.write_text("")
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.vault.name == "my-vault"

    def test_explicit_config_path(self, tmp_path: Path) -> None:
        custom = tmp_path / "custom" / "my.toml"
        custom.parent.mkdir(parents=True)
        custom.write_text('[vault]\nname = "custom"\n')
        settings = ZtlSettings.from_cli(config_path=str(custom), vault_root=tmp_path)
        assert settings.vault.name == "custom"
        assert settings.config_path == custom

    def test_legacy_vanilla_client_normalizes_to_none(self, tmp_path: Path) -> None:
        toml = tmp_path / "ztlctl.toml"
        toml.write_text('[vault]\nname = "legacy"\nclient = "vanilla"\n')

        settings = ZtlSettings.from_cli(vault_root=tmp_path)

        assert settings.workspace.profile == "core"
        assert settings.vault.client == "none"

    def test_workspace_profile_is_canonical_runtime_source(self, tmp_path: Path) -> None:
        toml = tmp_path / "ztlctl.toml"
        toml.write_text('[workspace]\nprofile = "core"\n', encoding="utf-8")

        settings = ZtlSettings.from_cli(vault_root=tmp_path)

        assert settings.workspace.profile == "core"
        assert settings.vault.client == "none"

    def test_plugin_profile_maps_to_compatibility_client_none(self, tmp_path: Path) -> None:
        toml = tmp_path / "ztlctl.toml"
        toml.write_text('[workspace]\nprofile = "custom-plugin"\n', encoding="utf-8")

        settings = ZtlSettings.from_cli(vault_root=tmp_path)

        assert settings.workspace.profile == "custom-plugin"
        assert settings.vault.client == "none"

    def test_workspace_profile_wins_over_legacy_client(self, tmp_path: Path) -> None:
        toml = tmp_path / "ztlctl.toml"
        toml.write_text(
            '[vault]\nclient = "obsidian"\n\n[workspace]\nprofile = "core"\n',
            encoding="utf-8",
        )

        settings = ZtlSettings.from_cli(vault_root=tmp_path)

        assert settings.workspace.profile == "core"
        assert settings.vault.client == "none"

    def test_plugins_extra_keys_stored_for_config_injection(self, tmp_path: Path) -> None:
        """Extra [plugins.<name>] sections are stored via extra='allow' for PLUG-03."""
        toml = tmp_path / "ztlctl.toml"
        toml.write_text(
            "[plugins]\ngit = { enabled = true }\nobsidian = { enabled = true }\n",
            encoding="utf-8",
        )

        settings = ZtlSettings.from_cli(vault_root=tmp_path)

        # git is a declared field; obsidian is stored in model_extra via extra="allow"
        assert settings.plugins.git == {"enabled": True}
        assert settings.plugins.get_plugin_config("obsidian") == {"enabled": True}


class TestCliFlags:
    def test_cli_flags_override(self, tmp_path: Path) -> None:
        settings = ZtlSettings.from_cli(
            vault_root=tmp_path,
            json_output=True,
            quiet=True,
            verbose=True,
        )
        assert settings.json_output is True
        assert settings.quiet is True
        assert settings.verbose is True

    def test_cli_flags_override_toml(self, tmp_path: Path) -> None:
        """CLI flags take priority over TOML values."""
        toml = tmp_path / "ztlctl.toml"
        toml.write_text("no_reweave = true\n")
        settings = ZtlSettings.from_cli(vault_root=tmp_path, no_reweave=False)
        assert settings.no_reweave is False


class TestVaultRootResolution:
    def test_explicit_vault_root(self, tmp_path: Path) -> None:
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.vault_root == tmp_path

    def test_vault_root_from_toml_location(self, tmp_path: Path) -> None:
        """When no explicit root, use parent of discovered ztlctl.toml."""
        subdir = tmp_path / "sub" / "deep"
        subdir.mkdir(parents=True)
        (tmp_path / "ztlctl.toml").write_text("")
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.vault_root == tmp_path


class TestEnvVars:
    def test_env_var_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZTLCTL_QUIET", "true")
        settings = ZtlSettings.from_cli(vault_root=tmp_path)
        assert settings.quiet is True

    def test_nested_env_var_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ZTLCTL_REWEAVE__MIN_SCORE_THRESHOLD", "0.5")

        settings = ZtlSettings.from_cli(vault_root=tmp_path)

        assert settings.reweave.min_score_threshold == 0.5
