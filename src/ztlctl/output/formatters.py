"""Rich/JSON output helpers.

The CLI renders ServiceResult for humans (Rich output, colors, icons,
progress bars) or machines (--json). The formatter layer adapts
ServiceResult to the requested output mode.
"""

from __future__ import annotations

import json as _json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


def _format_data_human(data: dict[str, Any]) -> str:
    """Format result data as indented key-value pairs."""
    lines: list[str] = []
    for key, value in data.items():
        if isinstance(value, (dict, list)):
            lines.append(f"  {key}: {_json.dumps(value, separators=(',', ':'))}")
        else:
            lines.append(f"  {key}: {value}")
    return "\n".join(lines)


def format_result(result: ServiceResult, *, json_output: bool = False) -> str:
    """Format a ServiceResult for display.

    Args:
        result: The service result to format.
        json_output: If True, return JSON; otherwise return human-readable text.
    """
    if json_output:
        return result.model_dump_json(indent=2)
    if result.ok:
        parts = [f"OK: {result.op}"]
        if result.data:
            parts.append(_format_data_human(result.data))
        return "\n".join(parts)
    error_msg = result.error.message if result.error else "Unknown error"
    return f"ERROR: {result.op} — {error_msg}"
