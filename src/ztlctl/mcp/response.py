"""McpResponse and McpError — Pydantic MCP response models.

McpResponse.from_result() converts any ServiceResult into a validated
MCP response dict.  ``COMMON_ERROR_RECOVERY`` is the shared recovery
guidance for MCP-exposed error codes.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from ztlctl.services.result import ServiceResult

# ---------------------------------------------------------------------------
# Common error recovery guidance
# ---------------------------------------------------------------------------

COMMON_ERROR_RECOVERY: dict[str, str] = {
    "NOT_FOUND": "Verify the target ID with search(), list_items(), or get_document().",
    "VALIDATION_FAILED": (
        "Check required params and field types. Titles must be non-empty and statuses must use "
        "supported values."
    ),
    "ID_COLLISION": (
        "Search for the existing item first, then update it or choose a different title."
    ),
    "NO_ACTIVE_SESSION": "Start a session with create_log(topic) before calling session tools.",
    "ACTIVE_SESSION_EXISTS": (
        "Use session_status() to inspect the active session or close it before starting another."
    ),
    "INVALID_TRANSITION": "Inspect the current item with get_document() before changing status.",
    "EMPTY_QUERY": "Provide a non-empty search string or use list_items() for browsing.",
    "UNKNOWN_TYPE": "Use a supported content type/subtype combination or omit subtype if unsure.",
    "NO_PATH": "Confirm both IDs exist and are connected before requesting a graph path.",
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class McpError(BaseModel):
    """Structured MCP error payload."""

    model_config = {"frozen": True}

    code: str
    message: str
    detail: dict[str, Any] = Field(default_factory=dict)


class McpResponse(BaseModel):
    """Universal MCP tool response model.

    Attributes:
        ok: Whether the operation succeeded.
        op: Name of the operation (e.g. ``"create_note"``).
        data: Operation-specific payload on success.
        warnings: Non-fatal issues encountered during the operation.
        error: Structured error if ``ok`` is False.

    Note: ``ServiceResult.meta`` is intentionally NOT forwarded — it
    contains internal timing/diagnostic data not intended for MCP consumers.
    """

    model_config = {"frozen": True}

    ok: bool
    op: str
    data: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] | None = None
    error: McpError | None = None

    @classmethod
    def from_result(cls, result: ServiceResult) -> McpResponse:
        """Convert a ServiceResult to an McpResponse.

        Maps ``result.ok``, ``result.op``, ``result.data``, and
        ``result.warnings`` (set to ``None`` when empty so that
        ``model_dump(exclude_none=True)`` omits the key).
        Converts ``result.error`` to an McpError.
        Explicitly drops ``result.meta`` (internal diagnostic data).
        """
        error: McpError | None = None
        if result.error is not None:
            error = McpError(
                code=result.error.code,
                message=result.error.message,
            )
        return cls(
            ok=result.ok,
            op=result.op,
            data=result.data,
            warnings=result.warnings if result.warnings else None,
            error=error,
        )
