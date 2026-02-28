"""Unified settings — CLI flags, env vars, and TOML config in one object.

Priority chain (highest to lowest):
  1. Init kwargs  — CLI flags passed by Click
  2. Env vars     — ``ZTLCTL_*`` prefix
  3. TOML file    — ``ztlctl.toml`` discovered via walk-up
  4. Code defaults — baked into the section models

Uses Pydantic Settings v2 with a custom :class:`TomlSettingsSource` that
reuses the existing ``find_config`` walk-up discovery from
:mod:`ztlctl.config.discovery`.
"""

from __future__ import annotations

import threading
import tomllib
from pathlib import Path
from typing import Any, ClassVar

from pydantic import Field
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from ztlctl.config.discovery import find_config
from ztlctl.config.models import (
    AgentConfig,
    CheckConfig,
    GardenConfig,
    GitConfig,
    McpConfig,
    PluginsConfig,
    ReweaveConfig,
    SearchConfig,
    SessionConfig,
    TagsConfig,
    VaultConfig,
    WorkflowConfig,
)


class TomlSettingsSource(PydanticBaseSettingsSource):
    """Read settings from a ``ztlctl.toml`` file discovered via walk-up."""

    def __init__(self, settings_cls: type[BaseSettings], toml_path: Path | None) -> None:
        super().__init__(settings_cls)
        self._data: dict[str, Any] = {}
        if toml_path and toml_path.is_file():
            raw = toml_path.read_text(encoding="utf-8")
            try:
                self._data = tomllib.loads(raw)
            except tomllib.TOMLDecodeError as exc:
                import click

                msg = f"Invalid TOML in {toml_path}: {exc}"
                raise click.ClickException(msg) from exc

    def get_field_value(self, field: Any, field_name: str) -> tuple[Any, str, bool]:
        """Return ``(value, field_name, value_is_complex)``."""
        val = self._data.get(field_name)
        return val, field_name, field_name in self._data

    def __call__(self) -> dict[str, Any]:
        """Return the full TOML data dict for Pydantic to merge."""
        return self._data


# Thread-local storage for TOML path during construction.
_tls = threading.local()


class ZtlSettings(BaseSettings):
    """Unified settings for the entire ztlctl CLI.

    Merges CLI flags, environment variables, TOML config sections,
    and code-baked defaults into a single frozen object.  Stored in
    ``click.Context.obj`` at the CLI root level.

    Attributes:
        vault_root: Resolved vault directory (parent of ``ztlctl.toml``,
            or CWD if no config found).
        config_path: Explicit ``--config`` override, or None for discovery.
    """

    model_config = {
        "frozen": True,
        "env_prefix": "ZTLCTL_",
        "env_nested_delimiter": "__",
    }

    # --- Resolved path (not in TOML — derived from config location) ---
    vault_root: Path = Field(default_factory=Path.cwd)
    config_path: Path | None = None

    # --- CLI flags ---
    json_output: bool = False
    quiet: bool = False
    verbose: bool = False
    log_json: bool = False
    no_interact: bool = False
    no_reweave: bool = False
    sync: bool = False

    # --- TOML sections (reuse existing frozen models) ---
    vault: VaultConfig = Field(default_factory=VaultConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    reweave: ReweaveConfig = Field(default_factory=ReweaveConfig)
    garden: GardenConfig = Field(default_factory=GardenConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    session: SessionConfig = Field(default_factory=SessionConfig)
    tags: TagsConfig = Field(default_factory=TagsConfig)
    check: CheckConfig = Field(default_factory=CheckConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    mcp: McpConfig = Field(default_factory=McpConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)

    # Retained for type-checker visibility; not used at runtime.
    _toml_path: ClassVar[Path | None] = None

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Insert TOML source between env vars and defaults."""
        toml_path = getattr(_tls, "toml_path", None)
        return (
            init_settings,
            env_settings,
            TomlSettingsSource(settings_cls, toml_path),
        )

    @classmethod
    def from_cli(
        cls,
        *,
        config_path: str | None = None,
        vault_root: Path | None = None,
        **cli_flags: Any,
    ) -> ZtlSettings:
        """Construct settings from CLI invocation.

        Discovers ``ztlctl.toml`` via walk-up (or explicit *config_path*),
        resolves *vault_root* from the config file's parent directory,
        and merges CLI flags as highest-priority overrides.
        """
        toml_path: Path | None = None
        if config_path:
            p = Path(config_path)
            if p.is_file():
                toml_path = p
        else:
            toml_path = find_config(vault_root)

        resolved_root = vault_root
        if resolved_root is None:
            resolved_root = toml_path.parent if toml_path else Path.cwd()

        _tls.toml_path = toml_path
        try:
            return cls(
                vault_root=resolved_root,
                config_path=toml_path,
                **cli_flags,
            )
        finally:
            _tls.toml_path = None
