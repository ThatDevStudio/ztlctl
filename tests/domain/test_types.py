"""Tests for domain type enums — parametrized."""

import pytest

from ztlctl.domain.types import ContentType, NoteSubtype, RefSubtype, Space

ENUM_CASES = [
    (
        ContentType,
        {"note", "reference", "log", "task"},
    ),
    (
        NoteSubtype,
        {"decision", "knowledge"},
    ),
    (
        RefSubtype,
        {"article", "tool", "spec"},
    ),
    (
        Space,
        {"self", "notes", "ops"},
    ),
]


@pytest.mark.parametrize(
    "enum_cls,expected_values",
    ENUM_CASES,
    ids=[cls.__name__ for cls, _ in ENUM_CASES],
)
def test_enum_members_and_values(enum_cls: type, expected_values: set[str]) -> None:
    """Each StrEnum has the expected members with matching string values."""
    actual_values = {e.value for e in enum_cls}
    assert actual_values == expected_values
    # StrEnum members compare equal to their string value
    for member in enum_cls:
        assert member == member.value
        assert isinstance(member, str)
