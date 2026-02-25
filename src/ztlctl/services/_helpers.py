"""Shared service-layer helper functions."""

from __future__ import annotations

from datetime import UTC, datetime


def today_iso() -> str:
    """Today's date as YYYY-MM-DD."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


def now_iso() -> str:
    """Current UTC time as standard ISO 8601 (for audit trails, session logs)."""
    return datetime.now(UTC).isoformat()


def now_compact() -> str:
    """Current UTC time as compact ISO (YYYYMMDDTHHmmss, for backup filenames)."""
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%S")


def estimate_tokens(text: str) -> int:
    """Rough token count estimate (chars/4). No external dependency.

    This is a heuristic — real token counts come from the workflow layer
    via the ``cost`` parameter on log_entry(). This is only used for
    budget enforcement in context assembly.
    """
    return max(1, len(text) // 4)


def parse_tag_parts(tag: str) -> tuple[str, str]:
    """Split 'domain/scope' tag into (domain, scope).

    Unscoped tags get domain='unscoped'.

    Examples:
        >>> parse_tag_parts("math/algebra")
        ('math', 'algebra')
        >>> parse_tag_parts("general")
        ('unscoped', 'general')
        >>> parse_tag_parts("a/b/c")
        ('a', 'b/c')
    """
    parts = tag.split("/", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return "unscoped", parts[0]
