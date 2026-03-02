"""Pydantic configuration section models with code-baked defaults.

Sparse TOML contract: defaults baked here, ztlctl.toml only contains overrides.
A fresh vault needs only [vault] name and [agent] tone.

These section models are composed by :class:`~ztlctl.config.settings.ZtlSettings`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

from ztlctl.workspace_profiles import (
    legacy_client_to_profile,
    normalize_profile,
    profile_to_legacy_client,
)

# --- ztlctl.toml sections ---


class VaultConfig(BaseModel):
    """[vault] section."""

    model_config = {"frozen": True}

    name: str = "my-vault"
    client: str = "obsidian"

    @field_validator("client")
    @classmethod
    def _normalize_client(cls, value: str) -> str:
        normalized_profile, _warning = legacy_client_to_profile(value)
        return profile_to_legacy_client(normalized_profile)


class WorkspaceConfig(BaseModel):
    """[workspace] section."""

    model_config = {"frozen": True}

    profile: str = "obsidian"

    @field_validator("profile")
    @classmethod
    def _normalize_profile(cls, value: str) -> str:
        normalized, _warning = normalize_profile(value)
        return normalized


class AgentContextConfig(BaseModel):
    """[agent.context] section."""

    model_config = {"frozen": True}

    default_budget: int = 8000
    layer_0_min: int = 500
    layer_1_min: int = 1000
    layer_2_max_notes: int = 10
    layer_3_max_hops: int = 1


class AgentConfig(BaseModel):
    """[agent] section."""

    model_config = {"frozen": True}

    tone: str = "research-partner"
    context: AgentContextConfig = Field(default_factory=AgentContextConfig)


class ReweaveConfig(BaseModel):
    """[reweave] section."""

    model_config = {"frozen": True}

    enabled: bool = True
    min_score_threshold: float = 0.6
    max_links_per_note: int = 5
    lexical_weight: float = 0.35
    tag_weight: float = 0.25
    graph_weight: float = 0.25
    topic_weight: float = 0.15


class GardenConfig(BaseModel):
    """[garden] section."""

    model_config = {"frozen": True}

    seed_age_warning_days: int = 7
    evergreen_min_key_points: int = 5
    evergreen_min_bidirectional_links: int = 3


class SearchConfig(BaseModel):
    """[search] section."""

    model_config = {"frozen": True}

    semantic_enabled: bool = False
    embedding_model: str = "local"
    embedding_dim: int = 384
    half_life_days: float = 30.0
    semantic_weight: float = 0.5


class IngestConfig(BaseModel):
    """[ingest] section."""

    model_config = {"frozen": True}

    enabled: bool = True
    auto_reweave: bool = True
    default_target_type: str = "reference"
    providers: dict[str, Any] = Field(default_factory=dict)


class SessionConfig(BaseModel):
    """[session] section."""

    model_config = {"frozen": True}

    close_reweave: bool = True
    close_orphan_sweep: bool = True
    close_integrity_check: bool = True
    orphan_reweave_threshold: float = 0.2


class TagsConfig(BaseModel):
    """[tags] section."""

    model_config = {"frozen": True}

    auto_register: bool = True


class CheckConfig(BaseModel):
    """[check] section."""

    model_config = {"frozen": True}

    backup_retention_days: int = 30
    backup_max_count: int = 10


class PluginsConfig(BaseModel):
    """[plugins] section."""

    model_config = {"frozen": True}

    git: dict[str, Any] = Field(default_factory=lambda: {"enabled": True})


class GitConfig(BaseModel):
    """[git] section."""

    model_config = {"frozen": True}

    enabled: bool = True
    branch: str = "develop"
    auto_push: bool = True
    commit_style: str = "conventional"
    batch_commits: bool = True
    auto_ignore: bool = True


class McpConfig(BaseModel):
    """[mcp] section."""

    model_config = {"frozen": True}

    enabled: bool = True
    transport: str = "stdio"


class WorkflowConfig(BaseModel):
    """[workflow] section."""

    model_config = {"frozen": True}

    template: str = "claude-driven"
    skill_set: str = "research"


class DashboardExportConfig(BaseModel):
    """[exports.dashboard] section."""

    model_config = {"frozen": True}

    include_work_queue: bool = True
    include_recent_decisions: bool = True
    include_garden_backlog: bool = True
    topic_dossier_limit: int = 5


class ExportsConfig(BaseModel):
    """[exports] section."""

    model_config = {"frozen": True}

    dashboard: DashboardExportConfig = Field(default_factory=DashboardExportConfig)
