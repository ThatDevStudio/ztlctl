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
    "ACTION_REJECTED": (
        "A plugin rejected this action. Check the error detail for the rejecting plugin and "
        "reason. Retry with different parameters or disable the plugin."
    ),
    "INVALID_TRANSITION": "Inspect the current item with get_document() before changing status.",
    "EMPTY_QUERY": "Provide a non-empty search string or use list_items() for browsing.",
    "UNKNOWN_TYPE": "Use a supported content type/subtype combination or omit subtype if unsure.",
    "NO_PATH": "Confirm both IDs exist and are connected before requesting a graph path.",
    "ALREADY_OPEN": (
        "The session is already open. Use session_status() to inspect it or close() to end it."
    ),
    "NO_ENTRIES": "The session has no entries. Add notes or references before closing.",
    "NO_HISTORY": (
        "No undo history exists for this note. Call reweave() without undo to create a new "
        "suggestion."
    ),
    "NO_LINK": "No link exists between these nodes. Use link() to create a connection first.",
    "BATCH_PARTIAL": (
        "Some items in the batch failed. Check the data.results list for per-item status."
    ),
    "BATCH_FAILED": (
        "All batch items failed. Validate your input list and retry individual creates."
    ),
    "INIT_STEP_FAILED": (
        "An init step failed. Check the error detail for the step name and retry init."
    ),
    "INVALID_PROFILE": (
        "The profile name is not recognized. Call list_profiles to see valid options."
    ),
    "VAULT_EXISTS": (
        "A vault already exists at this path. Use a different directory or remove the existing "
        "vault."
    ),
    "NO_CONFIG": "No ztlctl.toml found. Run ztlctl init to create a vault configuration first.",
    "PROFILE_NOT_FOUND": (
        "The requested profile is not installed. Check available profiles with list_profiles."
    ),
    "NOT_A_VAULT": (
        "This directory is not a ztlctl vault. Run ztlctl init first or change to your vault "
        "directory."
    ),
    "WORKFLOW_EXISTS": "Workflow is already initialized. Use workflow_update to modify it.",
    "WORKFLOW_NOT_INITIALIZED": "Workflow is not initialized. Run workflow_init first.",
    "WORKFLOW_INIT_FAILED": (
        "Copier template application failed. Check that the vault directory is writable."
    ),
    "WORKFLOW_UPDATE_FAILED": (
        "Copier update failed. Try running workflow_init with force to reinitialize."
    ),
    "WORKFLOW_VALIDATION_FAILED": (
        "Workflow asset validation failed. Run workflow_export to regenerate assets."
    ),
    "CHECK_FAILED": (
        "Schema check failed. Run check() to inspect vault integrity before upgrading."
    ),
    "BACKUP_FAILED": (
        "Backup creation failed. Ensure the vault directory is writable before upgrading."
    ),
    "MIGRATION_FAILED": "Migration failed. Restore from backup with check_restore() and retry.",
    "STAMP_FAILED": "Schema stamp failed. Run check_pending() to inspect migration state.",
    "INVALID_FORMAT": "Unknown export format. Use one of: markdown, indexes, dot, json.",
    "INVALID_VIEWER": "Unknown viewer. Use one of: vanilla, claude, codex.",
    "NO_BACKUPS": "No backups found. Run check_backup() to create one.",
    "SEMANTIC_UNAVAILABLE": (
        "Semantic search is unavailable. Install the vector extra: pip install ztlctl[vector]."
    ),
    "UNSUPPORTED_INPUT": "Unsupported input kind. Use text or url.",
    "NO_PROVIDER": (
        "No source provider found for this URL scheme. Install a plugin that supports this scheme."
    ),
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
    recovery: str | None = None


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
            recovery = result.error.recovery or COMMON_ERROR_RECOVERY.get(result.error.code)
            error = McpError(
                code=result.error.code,
                message=result.error.message,
                recovery=recovery,
                detail=result.error.detail,
            )
        return cls(
            ok=result.ok,
            op=result.op,
            data=result.data,
            warnings=result.warnings if result.warnings else None,
            error=error,
        )
