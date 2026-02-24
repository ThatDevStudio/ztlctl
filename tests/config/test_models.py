"""Tests for config models — defaults and sparse overrides."""

from ztlctl.config.models import (
    AppContext,
    ReweaveConfig,
    ZtlConfig,
)


class TestAppContext:
    def test_defaults(self) -> None:
        ctx = AppContext()
        assert ctx.json_output is False
        assert ctx.quiet is False
        assert ctx.verbose is False
        assert ctx.no_interact is False
        assert ctx.no_reweave is False
        assert ctx.sync is False
        assert ctx.config_path is None

    def test_frozen(self) -> None:
        ctx = AppContext(json_output=True)
        try:
            ctx.json_output = False  # type: ignore[misc]
            raise AssertionError("Should have raised")
        except Exception:
            pass


class TestZtlConfig:
    def test_full_defaults(self) -> None:
        """Fresh ZtlConfig has sensible defaults for all sections."""
        cfg = ZtlConfig()
        assert cfg.vault.name == "my-vault"
        assert cfg.vault.client == "obsidian"
        assert cfg.agent.tone == "research-partner"
        assert cfg.agent.context.default_budget == 8000
        assert cfg.reweave.enabled is True
        assert cfg.reweave.min_score_threshold == 0.6
        assert cfg.garden.seed_age_warning_days == 7
        assert cfg.search.semantic_enabled is False
        assert cfg.session.close_reweave is True
        assert cfg.tags.auto_register is True
        assert cfg.check.backup_retention_days == 30
        assert cfg.git.batch_commits is True
        assert cfg.mcp.transport == "stdio"
        assert cfg.workflow.template == "claude-driven"

    def test_sparse_override(self) -> None:
        """Only override fields you care about — rest keeps defaults."""
        cfg = ZtlConfig.model_validate(
            {
                "vault": {"name": "my-research"},
                "agent": {"tone": "minimal"},
            }
        )
        assert cfg.vault.name == "my-research"
        assert cfg.vault.client == "obsidian"  # default preserved
        assert cfg.agent.tone == "minimal"
        assert cfg.agent.context.default_budget == 8000  # nested default preserved

    def test_json_round_trip(self) -> None:
        cfg = ZtlConfig()
        raw = cfg.model_dump_json()
        restored = ZtlConfig.model_validate_json(raw)
        assert restored == cfg


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
