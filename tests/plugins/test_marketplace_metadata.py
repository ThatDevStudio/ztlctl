"""Tests for plugin marketplace metadata convention (PLUG-07)."""

from __future__ import annotations

import pytest

from ztlctl.plugins.contracts import PluginMetadata
from ztlctl.plugins.metadata import read_plugin_metadata

# ---------------------------------------------------------------------------
# PluginMetadata dataclass
# ---------------------------------------------------------------------------


class TestPluginMetadataDataclass:
    def test_metadata_frozen(self) -> None:
        """PluginMetadata is immutable (frozen dataclass)."""
        meta = PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            author="Alice",
            capabilities=("register_note_types",),
            ztlctl_api_version=1,
        )
        with pytest.raises((AttributeError, TypeError)):
            meta.name = "changed"  # type: ignore[misc]

    def test_metadata_default_description(self) -> None:
        """PluginMetadata has empty string default for description."""
        meta = PluginMetadata(
            name="my-plugin",
            version="1.0.0",
            author="Alice",
            capabilities=(),
            ztlctl_api_version=1,
        )
        assert meta.description == ""

    def test_metadata_all_fields(self) -> None:
        """PluginMetadata stores all fields correctly."""
        meta = PluginMetadata(
            name="my-plugin",
            version="2.1.0",
            author="Bob",
            capabilities=("register_note_types", "register_cli_commands"),
            ztlctl_api_version=1,
            description="A great plugin",
        )
        assert meta.name == "my-plugin"
        assert meta.version == "2.1.0"
        assert meta.author == "Bob"
        assert meta.capabilities == ("register_note_types", "register_cli_commands")
        assert meta.ztlctl_api_version == 1
        assert meta.description == "A great plugin"


# ---------------------------------------------------------------------------
# read_plugin_metadata helper
# ---------------------------------------------------------------------------


_VALID_PYPROJECT = """\
[tool.ztlctl-plugin]
name = "my-sprint-plugin"
version = "1.2.3"
author = "Acme Corp"
capabilities = ["register_note_types", "register_cli_commands"]
ztlctl_api_version = 1
description = "Adds sprint note type to ztlctl"
"""

_MINIMAL_PYPROJECT = """\
[tool.ztlctl-plugin]
name = "minimal-plugin"
version = "0.1.0"
author = "Dev"
ztlctl_api_version = 1
"""

_NO_SECTION_PYPROJECT = """\
[tool.pytest.ini_options]
addopts = "-q"

[project]
name = "some-other-tool"
"""

_MISSING_NAME_PYPROJECT = """\
[tool.ztlctl-plugin]
version = "1.0.0"
author = "Dev"
ztlctl_api_version = 1
"""

_INVALID_TOML = "this is not valid toml {{ }"


class TestReadPluginMetadata:
    def test_metadata_read(self, tmp_path: pytest.TempPathFactory) -> None:
        """Valid pyproject.toml with [tool.ztlctl-plugin] returns PluginMetadata."""
        pyproject = tmp_path / "pyproject.toml"  # type: ignore[operator]
        pyproject.write_text(_VALID_PYPROJECT)
        meta = read_plugin_metadata(pyproject)
        assert meta is not None
        assert meta.name == "my-sprint-plugin"
        assert meta.version == "1.2.3"
        assert meta.author == "Acme Corp"
        assert meta.capabilities == ("register_note_types", "register_cli_commands")
        assert meta.ztlctl_api_version == 1
        assert meta.description == "Adds sprint note type to ztlctl"

    def test_metadata_missing_section(self, tmp_path: pytest.TempPathFactory) -> None:
        """pyproject.toml without [tool.ztlctl-plugin] returns None."""
        pyproject = tmp_path / "pyproject.toml"  # type: ignore[operator]
        pyproject.write_text(_NO_SECTION_PYPROJECT)
        assert read_plugin_metadata(pyproject) is None  # type: ignore[arg-type]

    def test_metadata_missing_required_field(self, tmp_path: pytest.TempPathFactory) -> None:
        """Section missing required field 'name' returns None."""
        pyproject = tmp_path / "pyproject.toml"  # type: ignore[operator]
        pyproject.write_text(_MISSING_NAME_PYPROJECT)
        assert read_plugin_metadata(pyproject) is None  # type: ignore[arg-type]

    def test_metadata_default_description_via_helper(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """Section without 'description' field yields default empty string."""
        pyproject = tmp_path / "pyproject.toml"  # type: ignore[operator]
        pyproject.write_text(_MINIMAL_PYPROJECT)
        meta = read_plugin_metadata(pyproject)  # type: ignore[arg-type]
        assert meta is not None
        assert meta.description == ""
        # capabilities defaults to empty tuple when missing
        assert meta.capabilities == ()

    def test_metadata_file_not_found(self, tmp_path: pytest.TempPathFactory) -> None:
        """Non-existent file returns None (does not raise)."""
        missing = tmp_path / "nonexistent.toml"  # type: ignore[operator]
        assert read_plugin_metadata(missing) is None  # type: ignore[arg-type]

    def test_metadata_invalid_toml(self, tmp_path: pytest.TempPathFactory) -> None:
        """Invalid TOML returns None (does not raise)."""
        pyproject = tmp_path / "pyproject.toml"  # type: ignore[operator]
        pyproject.write_text(_INVALID_TOML)
        assert read_plugin_metadata(pyproject) is None  # type: ignore[arg-type]
