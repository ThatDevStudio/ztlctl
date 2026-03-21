"""Domain event types for the ztlctl action/event system.

ActionEvent carries the committed state of a completed action, dispatched
to plugins via the EventBus after a successful service operation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel


class ActionEvent(BaseModel):
    """Immutable event representing a completed action.

    Attributes:
        action_name: The registry action name (e.g. ``"create_note"``).
        side_effect: Whether the action mutated state (``"write"``) or
            was read-only (``"read"``).
        payload: Committed state snapshot — id, type, title, path, etc.
        warnings: Non-fatal warnings produced during the action.
        result: The full ServiceResult for plugins that need it.
    """

    model_config = {"frozen": True}

    action_name: str
    side_effect: Literal["write", "read"] = "write"
    payload: dict[str, Any]
    warnings: list[str] = []
    result: Any = None
