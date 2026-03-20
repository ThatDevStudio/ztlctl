"""Pure documentation search functions.

No CLI or MCP coupling. Called from commands/docs.py and mcp/resources.py.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import TypedDict


class DocResult(TypedDict):
    """A single search result from the docs corpus."""

    title: str
    path: str
    score: float
    excerpt: str


class DocError(TypedDict):
    """Error sentinel returned when the docs path cannot be resolved."""

    error: str


# ---------------------------------------------------------------------------
# Module-level regex constants
# ---------------------------------------------------------------------------

_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)
_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------


def _resolve_docs_path() -> Path | None:
    """Resolve the docs/ directory.

    Checks ZTLCTL_DOCS_PATH env var first, then package-relative path.
    Returns None if not found — caller handles the error.
    """
    env_override = os.environ.get("ZTLCTL_DOCS_PATH")
    if env_override:
        p = Path(env_override)
        return p if p.is_dir() else None

    # Package-relative: src/ztlctl/services/docs.py
    #   -> parent: src/ztlctl/services/
    #   -> parent: src/ztlctl/
    #   -> parent: src/
    #   -> parent: <repo_root>/
    #   -> / "docs"
    candidate = Path(__file__).parent.parent.parent.parent / "docs"
    return candidate if candidate.is_dir() else None


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _score_page(text: str, title: str, terms: list[str]) -> float:
    """Weighted term frequency: title=3x, headings=2x, body=1x."""
    text_lower = text.lower()
    title_lower = title.lower()
    headings = [m.group(1).lower() for m in _HEADING_RE.finditer(text)]

    score = 0.0
    for term in terms:
        t = term.lower()
        title_count = title_lower.count(t)
        heading_count = sum(h.count(t) for h in headings)
        body_count = text_lower.count(t)
        score += title_count * 3 + heading_count * 2 + body_count * 1

    return score


def _check_and_logic(text: str, title: str, terms: list[str]) -> bool:
    """Return True only if ALL terms appear somewhere in title or text."""
    text_lower = text.lower()
    title_lower = title.lower()
    for term in terms:
        t = term.lower()
        if t not in title_lower and t not in text_lower:
            return False
    return True


def _extract_excerpt(text: str, terms: list[str]) -> str:
    """Return first paragraph containing any search term, max 200 chars."""
    body = _FRONTMATTER_RE.sub("", text)
    paragraphs = re.split(r"\n\n+", body)
    for para in paragraphs:
        para_stripped = para.strip()
        if not para_stripped or para_stripped.startswith("#"):
            continue
        para_lower = para_stripped.lower()
        if any(t.lower() in para_lower for t in terms):
            excerpt = re.sub(r"[*_`#\[\]()]", "", para_stripped)
            return excerpt[:200].strip()
    return ""


def _extract_title(text: str, stem: str) -> str:
    """Extract title from first H1 heading, or fall back to file stem."""
    match = _HEADING_RE.search(text)
    if match:
        return match.group(1).strip()
    return stem


# ---------------------------------------------------------------------------
# Docs corpus collector
# ---------------------------------------------------------------------------


def _collect_docs_files(docs_path: Path) -> list[Path]:
    """Return list of .md files from docs/, docs/guide/, docs/dev/."""
    files: list[Path] = []
    for pattern in ("*.md", "guide/*.md", "dev/*.md"):
        files.extend(sorted(docs_path.glob(pattern)))
    return files


# ---------------------------------------------------------------------------
# Public _impl functions
# ---------------------------------------------------------------------------


def _docs_search_impl(
    query: str,
    limit: int = 5,
    docs_path: Path | None = None,
) -> list[DocResult | DocError]:
    """Search the docs corpus. Pure function — no MCP or CLI coupling.

    Returns a list of ``DocResult`` dicts with keys: title, path, score, excerpt.
    Returns ``[DocError(error="...")]`` if the docs path cannot be resolved.

    AND logic: multi-word queries only return pages where ALL terms appear.
    Scoring: title match = 3x, heading match = 2x, body match = 1x.
    Results sorted descending by score, capped at ``limit``.
    """
    query = query.strip()
    if not query:
        return []

    resolved = docs_path if docs_path is not None else _resolve_docs_path()
    if resolved is None:
        return [
            DocError(
                error=(
                    "docs/ directory not found. "
                    "Set ZTLCTL_DOCS_PATH to the path of your docs/ directory."
                )
            )
        ]

    terms = query.split()
    candidates: list[DocResult | DocError] = []

    for md_file in _collect_docs_files(resolved):
        try:
            text = md_file.read_text(encoding="utf-8")
        except OSError:
            continue

        title = _extract_title(text, md_file.stem)

        # AND gate: skip pages missing any term
        if not _check_and_logic(text, title, terms):
            continue

        score = _score_page(text, title, terms)
        if score <= 0:
            continue

        excerpt = _extract_excerpt(text, terms)
        candidates.append(
            DocResult(
                title=title,
                path=str(md_file),
                score=float(score),
                excerpt=excerpt,
            )
        )

    candidates.sort(key=lambda r: r["score"] if "score" in r else 0.0, reverse=True)  # type: ignore[typeddict-item]
    return candidates[:limit]


def _docs_index_impl(docs_path: Path | None = None) -> str:
    """Return the content of docs/llms.txt as a string.

    Returns an error string if llms.txt is not found or docs path cannot be resolved.
    """
    resolved = docs_path if docs_path is not None else _resolve_docs_path()
    if resolved is None:
        return (
            "error: docs/ directory not found. "
            "Set the ZTLCTL_DOCS_PATH environment variable to the path of your docs/ directory."
        )

    llms_txt = resolved / "llms.txt"
    if not llms_txt.is_file():
        return f"error: llms.txt not found in {resolved}"

    return llms_txt.read_text(encoding="utf-8")
