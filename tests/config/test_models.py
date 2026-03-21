"""Tests for config section models — defaults and sparse overrides."""

import pytest

from ztlctl.config.models import EventBusConfig, ReweaveConfig, VaultConfig, WorkspaceConfig


class TestSectionDefaults:
    def test_vault_defaults(self) -> None:
        cfg = VaultConfig()
        assert cfg.name == "my-vault"
        assert cfg.client == "none"

    def test_vault_frozen(self) -> None:
        cfg = VaultConfig()
        try:
            cfg.name = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass

    def test_vault_normalizes_vanilla_client_alias(self) -> None:
        cfg = VaultConfig.model_validate({"client": "vanilla"})
        assert cfg.client == "none"

    def test_workspace_defaults(self) -> None:
        cfg = WorkspaceConfig()
        assert cfg.profile == "core"

    def test_workspace_normalizes_none_alias_to_core(self) -> None:
        cfg = WorkspaceConfig.model_validate({"profile": "none"})
        assert cfg.profile == "core"


class TestReweaveConfig:
    def test_weights_sum(self) -> None:
        """Default weights should sum to 1.0."""
        cfg = ReweaveConfig()
        total = cfg.lexical_weight + cfg.tag_weight + cfg.graph_weight + cfg.topic_weight
        assert abs(total - 1.0) < 1e-9

    def test_override_threshold(self) -> None:
        cfg = ReweaveConfig.model_validate({"min_score_threshold": 0.4})
        assert cfg.min_score_threshold == 0.4
        assert cfg.max_links_per_note == 5  # default preserved


class TestEventBusConfig:
    def test_defaults(self) -> None:
        cfg = EventBusConfig()
        assert cfg.shutdown_timeout_seconds == 5.0
        assert cfg.max_retries == 3
        assert cfg.dead_letter_retention_days == 30
        assert cfg.per_future_timeout_seconds == 30.0

    def test_override_single_field(self) -> None:
        cfg = EventBusConfig(shutdown_timeout_seconds=10.0)
        assert cfg.shutdown_timeout_seconds == 10.0
        # Other fields preserve defaults
        assert cfg.max_retries == 3
        assert cfg.dead_letter_retention_days == 30
        assert cfg.per_future_timeout_seconds == 30.0

    def test_frozen(self) -> None:
        cfg = EventBusConfig()
        with pytest.raises(Exception):
            cfg.max_retries = 99  # type: ignore[misc]

    def test_all_fields_overridable(self) -> None:
        cfg = EventBusConfig(
            shutdown_timeout_seconds=1.0,
            max_retries=5,
            dead_letter_retention_days=7,
            per_future_timeout_seconds=60.0,
        )
        assert cfg.shutdown_timeout_seconds == 1.0
        assert cfg.max_retries == 5
        assert cfg.dead_letter_retention_days == 7
        assert cfg.per_future_timeout_seconds == 60.0


class TestZtlSettingsEventbus:
    def test_eventbus_field_exists_with_defaults(self) -> None:
        from ztlctl.config.settings import ZtlSettings

        settings = ZtlSettings()
        assert hasattr(settings, "eventbus")
        assert isinstance(settings.eventbus, EventBusConfig)
        assert settings.eventbus.shutdown_timeout_seconds == 5.0
        assert settings.eventbus.max_retries == 3

    def test_eventbus_populated_from_toml(self, tmp_path) -> None:

        from ztlctl.config.settings import ZtlSettings, _tls

        toml_content = "[eventbus]\nshutdown_timeout_seconds = 15.0\nmax_retries = 5\n"
        toml_file = tmp_path / "ztlctl.toml"
        toml_file.write_text(toml_content)

        _tls.toml_path = toml_file
        try:
            settings = ZtlSettings(vault_root=tmp_path)
        finally:
            _tls.toml_path = None

        assert settings.eventbus.shutdown_timeout_seconds == 15.0
        assert settings.eventbus.max_retries == 5
        # Unset fields preserve defaults
        assert settings.eventbus.dead_letter_retention_days == 30
