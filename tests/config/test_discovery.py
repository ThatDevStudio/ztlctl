"""Tests for config discovery and loading."""

from pathlib import Path

from ztlctl.config.discovery import CONFIG_FILENAME, find_config, load_config
from ztlctl.config.models import ZtlConfig


class TestFindConfig:
    def test_finds_in_current_dir(self, tmp_path: Path) -> None:
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text('[vault]\nname = "test"\n')
        result = find_config(tmp_path)
        assert result == config_file

    def test_walks_up(self, tmp_path: Path) -> None:
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text('[vault]\nname = "test"\n')
        child = tmp_path / "a" / "b" / "c"
        child.mkdir(parents=True)
        result = find_config(child)
        assert result == config_file

    def test_returns_none_when_not_found(self, tmp_path: Path) -> None:
        child = tmp_path / "empty"
        child.mkdir()
        result = find_config(child)
        assert result is None

    def test_env_var_override(self, tmp_path: Path, monkeypatch: object) -> None:
        config_file = tmp_path / "custom.toml"
        config_file.write_text('[vault]\nname = "env"\n')
        import pytest

        mp = pytest.MonkeyPatch()
        mp.setenv("ZTLCTL_CONFIG", str(config_file))
        try:
            result = find_config(tmp_path)
            assert result == config_file
        finally:
            mp.undo()


class TestLoadConfig:
    def test_loads_from_file(self, tmp_path: Path) -> None:
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text(
            '[vault]\nname = "loaded"\nclient = "vanilla"\n[reweave]\nmin_score_threshold = 0.4\n'
        )
        cfg = load_config(config_file)
        assert cfg.vault.name == "loaded"
        assert cfg.vault.client == "vanilla"
        assert cfg.reweave.min_score_threshold == 0.4
        assert cfg.agent.tone == "research-partner"  # default

    def test_returns_defaults_when_no_file(self, tmp_path: Path) -> None:
        cfg = load_config(cwd=tmp_path)
        assert cfg == ZtlConfig()

    def test_empty_file_returns_defaults(self, tmp_path: Path) -> None:
        config_file = tmp_path / CONFIG_FILENAME
        config_file.write_text("")
        cfg = load_config(config_file)
        assert cfg == ZtlConfig()
