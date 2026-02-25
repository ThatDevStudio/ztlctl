"""Tests for config section models — defaults and sparse overrides."""

from ztlctl.config.models import ReweaveConfig, VaultConfig


class TestSectionDefaults:
    def test_vault_defaults(self) -> None:
        cfg = VaultConfig()
        assert cfg.name == "my-vault"
        assert cfg.client == "obsidian"

    def test_vault_frozen(self) -> None:
        cfg = VaultConfig()
        try:
            cfg.name = "changed"  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass


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
