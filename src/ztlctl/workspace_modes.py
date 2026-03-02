"""Canonical workspace client/viewer modes and deprecated aliases."""

from __future__ import annotations

from typing import Literal, cast

CanonicalClient = Literal["obsidian", "none"]
CanonicalViewer = Literal["obsidian", "none"]

CLIENT_CHOICES = ("obsidian", "none")
VIEWER_CHOICES = ("obsidian", "none")
_DEPRECATED_ALIAS = "vanilla"
_ALIAS_TARGET = "none"


def _normalize_mode(
    value: str,
    *,
    kind: str,
    allowed: tuple[str, ...],
) -> tuple[str, str | None]:
    candidate = value.strip().lower()
    if candidate == _DEPRECATED_ALIAS:
        warning = (
            f"`{_DEPRECATED_ALIAS}` is deprecated for {kind} selection and will be removed "
            f"after the next release; use `{_ALIAS_TARGET}` instead."
        )
        return _ALIAS_TARGET, warning
    if candidate in allowed:
        return candidate, None
    valid = ", ".join(f"`{item}`" for item in allowed)
    msg = f"Unsupported {kind}: {value!r}. Valid values: {valid}."
    raise ValueError(msg)


def normalize_client(value: str) -> tuple[CanonicalClient, str | None]:
    """Normalize a vault client value to the canonical Phase 0 surface."""
    normalized, warning = _normalize_mode(value, kind="client", allowed=CLIENT_CHOICES)
    return cast(CanonicalClient, normalized), warning


def normalize_viewer(value: str) -> tuple[CanonicalViewer, str | None]:
    """Normalize a viewer value to the canonical Phase 0 surface."""
    normalized, warning = _normalize_mode(value, kind="viewer", allowed=VIEWER_CHOICES)
    return cast(CanonicalViewer, normalized), warning
