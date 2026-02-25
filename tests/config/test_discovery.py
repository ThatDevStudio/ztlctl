"""Tests for config discovery."""

from pathlib import Path

from ztlctl.config.discovery import CONFIG_FILENAME, find_config


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
