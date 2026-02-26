"""Link extraction — parse frontmatter and body wikilinks.

Pure functions, no infrastructure dependencies. Consumed by services
during the INDEX stage of the create pipeline and by check --rebuild.
(DESIGN.md Section 3)
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# [[Title]] or [[Title|Display Text]] — captures content between brackets.
_WIKILINK_PATTERN = re.compile(r"\[\[([^\[\]]+)\]\]")


@dataclass(frozen=True)
class WikiLink:
    """A wikilink extracted from body text."""

    raw: str  # original text between [[ ]] (target portion)
    display: str | None = None  # display text after | if present


@dataclass(frozen=True)
class FrontmatterLink:
    """A typed link extracted from frontmatter."""

    target_id: str
    edge_type: str  # "relates", "supports", "supersedes", etc.


def extract_wikilinks(body: str) -> list[WikiLink]:
    """Extract all ``[[wikilinks]]`` from markdown body text.

    Handles both ``[[Target]]`` and ``[[Target|Display Text]]`` formats.
    Returns an empty list if no wikilinks are found.
    """
    results: list[WikiLink] = []
    for match in _WIKILINK_PATTERN.finditer(body):
        inner = match.group(1)
        parts = inner.split("|", 1)
        target = parts[0].strip()
        display = parts[1].strip() if len(parts) > 1 else None
        results.append(WikiLink(raw=target, display=display))
    return results


def extract_frontmatter_links(links: dict[str, list[str]]) -> list[FrontmatterLink]:
    """Extract typed links from a frontmatter ``links`` dict.

    Frontmatter format::

        links:
          relates: [ztl_b3f2a1, ref_c4d5e6]
          supersedes: [ztl_old123]

    Returns an empty list if *links* is empty.
    """
    results: list[FrontmatterLink] = []
    for edge_type, targets in links.items():
        for target_id in targets:
            results.append(FrontmatterLink(target_id=str(target_id), edge_type=edge_type))
    return results
