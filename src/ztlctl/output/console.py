"""Rich Console factory and theme for ztlctl output.

Creates Console instances that render to a StringIO buffer, preserving
the ``format_result() -> str`` contract.  In non-TTY environments
(tests, pipes) Rich automatically disables color codes.
"""

from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.theme import Theme

ZTL_THEME = Theme(
    {
        "ztl.ok": "bold green",
        "ztl.error": "bold red",
        "ztl.warning": "bold yellow",
        "ztl.op": "bold cyan",
        "ztl.key": "dim",
        "ztl.id": "bold blue",
        "ztl.path": "dim",
        "ztl.title": "bold",
        "ztl.type.note": "green",
        "ztl.type.reference": "blue",
        "ztl.type.task": "yellow",
        "ztl.type.log": "cyan",
        "ztl.score": "magenta",
    }
)

_TYPE_STYLES: dict[str, str] = {
    "note": "ztl.type.note",
    "reference": "ztl.type.reference",
    "task": "ztl.type.task",
    "log": "ztl.type.log",
}


def create_console(*, no_color: bool = False, width: int | None = None) -> Console:
    """Create a Console that renders to a StringIO buffer.

    Args:
        no_color: Disable ANSI escape codes (used in tests).
        width: Override terminal width (useful for consistent test output).
    """
    return Console(
        file=StringIO(),
        theme=ZTL_THEME,
        no_color=no_color,
        highlight=False,
        width=width or 120,
    )


def get_output(console: Console) -> str:
    """Extract rendered text from a StringIO-backed Console."""
    assert isinstance(console.file, StringIO)
    return console.file.getvalue()


def style_for_type(content_type: str) -> str:
    """Return the Rich style name for a content type."""
    return _TYPE_STYLES.get(content_type, "")
