"""Rich/JSON output helpers.

The CLI renders ServiceResult for humans (Rich output, colors, icons,
progress bars) or machines (--json).  The formatter layer adapts
ServiceResult to the requested output mode.

Three modes:
- **JSON** (``--json``): ``model_dump_json()`` — machine-parseable, no color.
- **Quiet** (``--quiet``): Minimal single-line or IDs-only output.
- **Default / Verbose**: Rich-formatted, operation-aware output.
  ``--verbose`` adds extra columns, error detail, and meta blocks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ztlctl.output.renderers import render_quiet, render_result

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


@dataclass(frozen=True)
class OutputSettings:
    """Presentation settings extracted from ZtlSettings for the formatter."""

    json_output: bool = False
    quiet: bool = False
    verbose: bool = False


def format_result(
    result: ServiceResult,
    *,
    settings: OutputSettings | None = None,
    json_output: bool = False,
) -> str:
    """Format a ServiceResult for display.

    Args:
        result: The service result to format.
        settings: Full output settings (preferred).
        json_output: Legacy shortcut — if True, return JSON.  Ignored
            when *settings* is provided.

    Returns:
        Formatted string ready for ``click.echo()``.
    """
    if settings is None:
        settings = OutputSettings(json_output=json_output)

    if settings.json_output:
        return result.model_dump_json(indent=2)

    if settings.quiet:
        return render_quiet(result)

    return render_result(result, verbose=settings.verbose)
