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
