"""ServiceResult and ServiceError — the universal service contract.

INVARIANT: All service-layer methods return ServiceResult.
The CLI, MCP adapter, and any future interface consume this type.
(DESIGN.md Section 10)
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ServiceError(BaseModel):
    """Structured error payload within a ServiceResult."""

    model_config = {"frozen": True}

    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class ServiceResult(BaseModel):
    """Universal return type for all service operations.

    Attributes:
        ok: Whether the operation succeeded.
        op: Name of the operation (e.g. ``"create_note"``).
        data: Operation-specific payload on success.
        warnings: Non-fatal issues encountered during the operation.
        error: Structured error if ``ok`` is False.
        meta: Optional metadata (timing, counts, etc.).
    """

    model_config = {"frozen": True}

    ok: bool
    op: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    error: ServiceError | None = None
    meta: dict[str, Any] | None = None
