"""ID patterns, validation, and generation contracts.

Two ID strategies from DESIGN.md Section 7:
- Content-hash (notes, references): SHA-256 of normalized title, 8 hex chars.
- Sequential (logs, tasks): Atomic counter from DB, minimum 4 digits.

INVARIANT: IDs are permanent. Once generated, an ID never changes.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata

ID_PATTERNS: dict[str, re.Pattern[str]] = {
    "note": re.compile(r"^ztl_[0-9a-f]{8}$"),
    "reference": re.compile(r"^ref_[0-9a-f]{8}$"),
    "log": re.compile(r"^LOG-\d{4,}$"),
    "task": re.compile(r"^TASK-\d{4,}$"),
}

TYPE_PREFIXES: dict[str, str] = {
    "note": "ztl_",
    "reference": "ref_",
    "log": "LOG-",
    "task": "TASK-",
}


def normalize_title(title: str) -> str:
    """Normalize a title for content-hash ID generation.

    Lowercases, applies NFKC normalization, strips punctuation,
    and collapses whitespace.
    """
    text = title.lower()
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_content_hash(title: str, prefix: str) -> str:
    """Generate a content-hash ID from a title.

    Returns ``{prefix}{8 hex chars}`` where the hex is derived from
    SHA-256 of the normalized title.
    """
    normalized = normalize_title(title)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
    return f"{prefix}{digest}"


def validate_id(content_id: str, content_type: str) -> bool:
    """Check whether *content_id* matches the expected pattern for *content_type*."""
    pattern = ID_PATTERNS.get(content_type)
    if pattern is None:
        return False
    return pattern.match(content_id) is not None
