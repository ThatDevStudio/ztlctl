"""Typed payload contracts for service and adapter boundaries.

These models validate operation payload shapes before they leave the
service layer so key regressions (for example ``results`` vs ``items``)
fail fast in tests and during development.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


def dump_validated[T: BaseModel](model_cls: type[T], data: dict[str, Any]) -> dict[str, Any]:
    """Validate *data* against *model_cls* and return a normalized payload dict."""
    model = model_cls.model_validate(data)
    return model.model_dump(mode="python")


class SearchItem(BaseModel):
    """One search result row."""

    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    type: str
    subtype: str | None = None
    status: str
    path: str
    created: str
    modified: str
    score: float
    topic: str | None = None
    maturity: str | None = None
    ranking: RankingExplanation | None = None


class SearchResultData(BaseModel):
    """Payload contract for ``QueryService.search``."""

    query: str
    count: int
    items: list[SearchItem]


class ListItem(BaseModel):
    """One list result row."""

    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    type: str
    subtype: str | None = None
    maturity: str | None = None
    status: str
    path: str
    topic: str | None = None
    created: str
    modified: str
    score: float | None = None


class ListItemsResultData(BaseModel):
    """Payload contract for ``QueryService.list_items``."""

    count: int
    items: list[ListItem]


class CheckIssue(BaseModel):
    """One integrity finding returned by ``CheckService.check``."""

    model_config = ConfigDict(extra="allow")

    category: str
    severity: Literal["warning", "error"]
    node_id: str | None = None
    message: str
    fix_action: str | None = None


class CheckResultData(BaseModel):
    """Payload contract for ``CheckService.check``."""

    issues: list[CheckIssue]
    count: int
    error_count: int
    warning_count: int
    healthy: bool


class SessionLayerSummary(BaseModel):
    """Active session summary embedded in context layer 1."""

    session_id: str
    topic: str
    status: str
    started: str


class DecisionContextItem(BaseModel):
    """Recent decision entry in context layer 1."""

    id: str
    title: str
    status: str


class WorkQueueItem(BaseModel):
    """Task row used in context and MCP fallback payloads."""

    model_config = ConfigDict(extra="allow")

    id: str
    title: str
    status: str
    path: str
    priority: str
    impact: str
    effort: str
    score: float
    created: str
    modified: str


class TagSummaryItem(BaseModel):
    """Aggregated tag row used by discovery and workflow tooling."""

    tag: str
    count: int
    domain: str
    scope: str


class ListTagsResultData(BaseModel):
    """Payload contract for ``QueryService.list_tags``."""

    count: int
    items: list[TagSummaryItem]


class LogEntryContextItem(BaseModel):
    """Session log entry in context layer 1."""

    model_config = ConfigDict(extra="allow")

    id: int
    type: str
    summary: str
    timestamp: str
    pinned: bool
    cost: int
    detail: str | None = None
    references: list[str] | None = None


class ContextContentItem(BaseModel):
    """Generic context item used by layers 2-4."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    title: str | None = None
    type: str | None = None
    subtype: str | None = None
    status: str | None = None
    path: str | None = None
    topic: str | None = None
    score: float | None = None
    ranking: RankingExplanation | None = None


class RankingExplanation(BaseModel):
    """Why an item was selected or ranked highly."""

    mode: str
    reasons: list[str] = Field(default_factory=list)
    signals: dict[str, float] = Field(default_factory=dict)


class PacketLink(BaseModel):
    """Typed relationship between packet items."""

    source_id: str
    target_id: str
    edge_type: str
    direction: Literal["outgoing", "incoming"]
    note: str | None = None


class EvidenceExcerpt(BaseModel):
    """Excerpt or summary fragment used as evidence."""

    content_id: str
    title: str
    source_type: str
    text: str
    locator: str | None = None


class SuggestedAction(BaseModel):
    """Follow-up action derived from a topic packet."""

    type: Literal["note", "task", "decision", "link", "review"]
    title: str
    rationale: str
    related_ids: list[str] = Field(default_factory=list)


class DraftSourceItem(BaseModel):
    """Source reference included in a generated draft."""

    id: str
    title: str
    type: str
    path: str | None = None


class TopicDraftData(BaseModel):
    """Payload contract for draft generation from a topic packet."""

    topic: str
    mode: Literal["learn", "review", "decision"]
    target: Literal["note", "task", "decision"]
    title: str
    body: str
    sources: list[DraftSourceItem] = Field(default_factory=list)
    packet: dict[str, Any] = Field(default_factory=dict)


class AgentContextLayers(BaseModel):
    """Layered session context payload."""

    identity: str | None = None
    methodology: str | None = None
    session: SessionLayerSummary
    recent_decisions: list[DecisionContextItem] = Field(default_factory=list)
    work_queue: list[WorkQueueItem] = Field(default_factory=list)
    log_entries: list[LogEntryContextItem] = Field(default_factory=list)
    topic_content: list[ContextContentItem] = Field(default_factory=list)
    graph_adjacent: list[ContextContentItem] = Field(default_factory=list)
    background: list[ContextContentItem] = Field(default_factory=list)


class AgentContextResultData(BaseModel):
    """Payload contract for ``SessionService.context``."""

    total_tokens: int
    budget: int
    remaining: int
    pressure: Literal["normal", "caution", "exceeded"]
    layers: AgentContextLayers


class AgentContextFallbackData(BaseModel):
    """Payload contract for MCP ``agent_context`` fallback mode."""

    total_items: int = 0
    recent: list[ListItem] = Field(default_factory=list)
    search_results: list[SearchItem] = Field(default_factory=list)
    work_queue: list[WorkQueueItem] = Field(default_factory=list)


class SessionStatusResultData(BaseModel):
    """Payload contract for ``SessionService.status``."""

    session: SessionLayerSummary | None = None


class ThemeCommunityMember(BaseModel):
    """One member of a graph theme community."""

    id: str
    title: str
    type: str


class ThemeCommunity(BaseModel):
    """One graph community returned by ``GraphService.themes``."""

    community_id: int
    size: int
    members: list[ThemeCommunityMember] = Field(default_factory=list)


class GraphRankItem(BaseModel):
    """Graph score row used for rank output."""

    id: str
    title: str
    type: str
    score: float


class GraphGapItem(BaseModel):
    """Graph structural hole row used for gaps output."""

    id: str
    title: str
    type: str
    constraint: float


class GraphBridgeItem(BaseModel):
    """Graph bridge row used for bridge output."""

    id: str
    title: str
    type: str
    centrality: float


class VaultOverviewData(BaseModel):
    """Compact vault overview embedded in review payloads."""

    vault_name: str | None = None
    counts: dict[str, int] = Field(default_factory=dict)
    total: int = 0
    recent: list[ListItem] = Field(default_factory=list)


class VaultReviewResultData(BaseModel):
    """Payload contract for ``QueryService.vault_review``."""

    overview: VaultOverviewData
    recent: list[ListItem] = Field(default_factory=list)
    work_queue: list[WorkQueueItem] = Field(default_factory=list)
    themes: list[ThemeCommunity] = Field(default_factory=list)
    gaps: list[GraphGapItem] = Field(default_factory=list)
    bridges: list[GraphBridgeItem] = Field(default_factory=list)
    important_items: list[GraphRankItem] = Field(default_factory=list)
    stale_seeds: list[ListItem] = Field(default_factory=list)
    orphan_notes: list[ListItem] = Field(default_factory=list)


class SourceProviderItem(BaseModel):
    """One registered source provider."""

    name: str
    description: str
    schemes: list[str] = Field(default_factory=list)


class SourceProvidersResultData(BaseModel):
    """Payload contract for source provider discovery."""

    count: int
    items: list[SourceProviderItem] = Field(default_factory=list)


class IngestPreviewData(BaseModel):
    """Payload contract for dry-run ingestion output."""

    input_kind: str
    target_type: str
    title: str
    body_preview: str
    provider: str | None = None
    source_kind: str | None = None
    modalities: list[str] = Field(default_factory=list)
    capture_agent: str | None = None
    capture_method: str | None = None
    provenance: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    excerpts: list[str] = Field(default_factory=list)


class IngestResultData(BaseModel):
    """Payload contract for ingestion output."""

    id: str
    path: str
    title: str
    type: str
    input_kind: str
    provider: str | None = None
    dry_run: bool = False
    source_kind: str | None = None
    modalities: list[str] = Field(default_factory=list)
    capture_agent: str | None = None
    capture_method: str | None = None


class SourceArtifactItem(BaseModel):
    """Agent-supplied source artifact metadata."""

    kind: str
    label: str | None = None
    uri: str | None = None
    mime_type: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TopicPacketData(BaseModel):
    """Payload contract for topic packet queries."""

    topic: str
    mode: Literal["learn", "review", "decision"]
    budget: int
    total_tokens: int
    notes: list[ContextContentItem] = Field(default_factory=list)
    references: list[ContextContentItem] = Field(default_factory=list)
    decisions: list[ContextContentItem] = Field(default_factory=list)
    tasks: list[ContextContentItem] = Field(default_factory=list)
    evidence: list[EvidenceExcerpt] = Field(default_factory=list)
    graph_adjacent: list[ContextContentItem] = Field(default_factory=list)
    gaps: list[ContextContentItem] = Field(default_factory=list)
    bridges: list[ContextContentItem] = Field(default_factory=list)
    bridge_candidates: list[ContextContentItem] = Field(default_factory=list)
    stale_items: list[ContextContentItem] = Field(default_factory=list)
    supporting_links: list[PacketLink] = Field(default_factory=list)
    conflicts: list[PacketLink] = Field(default_factory=list)
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    ranking_explanations: dict[str, RankingExplanation] = Field(default_factory=dict)
    provenance: dict[str, list[str]] = Field(default_factory=dict)
    provenance_map: dict[str, list[str]] = Field(default_factory=dict)
