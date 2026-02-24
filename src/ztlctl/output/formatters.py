"""Rich/JSON output helpers.

The CLI renders ServiceResult for humans (Rich output, colors, icons,
progress bars) or machines (--json). The formatter layer adapts
ServiceResult to the requested output mode.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


def format_result(result: ServiceResult, *, json_output: bool = False) -> str:
    """Format a ServiceResult for display.

    Args:
        result: The service result to format.
        json_output: If True, return JSON; otherwise return human-readable text.
    """
    if json_output:
        return result.model_dump_json(indent=2)
    # Rich formatting deferred to output feature implementation
    if result.ok:
        return f"OK: {result.op}"
    error_msg = result.error.message if result.error else "Unknown error"
    return f"ERROR: {result.op} — {error_msg}"
