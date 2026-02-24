"""Pydantic configuration models with code-baked defaults.

Sparse TOML contract: defaults baked here, ztlctl.toml only contains overrides.
A fresh vault needs only [vault] name and [agent] tone.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# --- CLI context (passed via click ctx.obj) ---


class AppContext(BaseModel):
    """Global CLI flags, frozen after construction."""

    model_config = {"frozen": True}

    json_output: bool = False
    quiet: bool = False
    verbose: bool = False
    no_interact: bool = False
    no_reweave: bool = False
    sync: bool = False
    config_path: str | None = None


# --- ztlctl.toml sections ---


class VaultConfig(BaseModel):
    """[vault] section."""

    model_config = {"frozen": True}

    name: str = "my-vault"
    client: str = "obsidian"


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
    obsidian: dict[str, Any] = Field(default_factory=lambda: {"enabled": True})


class GitConfig(BaseModel):
    """[git] section."""

    model_config = {"frozen": True}

    enabled: bool = True
    branch: str = "main"
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


class ZtlConfig(BaseModel):
    """Root configuration composing all sections.

    Matches the full ztlctl.toml schema from DESIGN.md Section 17.
    """

    model_config = {"frozen": True}

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
