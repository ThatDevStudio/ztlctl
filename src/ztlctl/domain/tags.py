"""Tag domain logic — parsing and structural rules."""

from __future__ import annotations


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
