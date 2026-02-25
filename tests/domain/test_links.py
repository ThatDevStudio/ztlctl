"""Tests for link extraction — wikilinks and frontmatter links."""

from __future__ import annotations

from ztlctl.domain.links import (
    FrontmatterLink,
    WikiLink,
    extract_frontmatter_links,
    extract_wikilinks,
)

# ---------------------------------------------------------------------------
# extract_wikilinks
# ---------------------------------------------------------------------------


class TestExtractWikilinks:
    def test_single_link(self) -> None:
        body = "This relates to [[Transformer Architectures]]."
        links = extract_wikilinks(body)
        assert len(links) == 1
        assert links[0] == WikiLink(raw="Transformer Architectures", display=None)

    def test_multiple_links(self) -> None:
        body = "See [[Note A]] and also [[Note B]] for context."
        links = extract_wikilinks(body)
        assert len(links) == 2
        assert links[0].raw == "Note A"
        assert links[1].raw == "Note B"

    def test_link_with_display_text(self) -> None:
        body = "Refer to [[ztl_a1b2c3d4|the original note]]."
        links = extract_wikilinks(body)
        assert len(links) == 1
        assert links[0].raw == "ztl_a1b2c3d4"
        assert links[0].display == "the original note"

    def test_link_with_id(self) -> None:
        body = "This contradicts [[ztl_a1b2c3d4]]."
        links = extract_wikilinks(body)
        assert len(links) == 1
        assert links[0].raw == "ztl_a1b2c3d4"
        assert links[0].display is None

    def test_no_links(self) -> None:
        body = "This is plain text with no wikilinks."
        links = extract_wikilinks(body)
        assert links == []

    def test_empty_body(self) -> None:
        links = extract_wikilinks("")
        assert links == []

    def test_strips_whitespace(self) -> None:
        body = "See [[ Padded Title | Display ]]."
        links = extract_wikilinks(body)
        assert len(links) == 1
        assert links[0].raw == "Padded Title"
        assert links[0].display == "Display"

    def test_multiple_links_on_same_line(self) -> None:
        body = "Between [[A]] and [[B]] there is a gap."
        links = extract_wikilinks(body)
        assert len(links) == 2
        assert links[0].raw == "A"
        assert links[1].raw == "B"

    def test_link_across_lines(self) -> None:
        body = "First line with [[Link One]].\nSecond line with [[Link Two]]."
        links = extract_wikilinks(body)
        assert len(links) == 2

    def test_ignores_single_brackets(self) -> None:
        body = "This has [single brackets] but no wikilinks."
        links = extract_wikilinks(body)
        assert links == []

    def test_frozen_dataclass(self) -> None:
        link = WikiLink(raw="test", display=None)
        assert link.raw == "test"
        assert link.display is None


# ---------------------------------------------------------------------------
# extract_frontmatter_links
# ---------------------------------------------------------------------------


class TestExtractFrontmatterLinks:
    def test_single_type_single_target(self) -> None:
        links = extract_frontmatter_links({"relates": ["ztl_abc12345"]})
        assert len(links) == 1
        assert links[0] == FrontmatterLink(target_id="ztl_abc12345", edge_type="relates")

    def test_single_type_multiple_targets(self) -> None:
        links = extract_frontmatter_links({"relates": ["ztl_abc12345", "ref_def67890"]})
        assert len(links) == 2
        assert links[0].target_id == "ztl_abc12345"
        assert links[1].target_id == "ref_def67890"
        assert all(link.edge_type == "relates" for link in links)

    def test_multiple_types(self) -> None:
        links = extract_frontmatter_links(
            {
                "relates": ["ztl_aaa11111"],
                "supersedes": ["ztl_bbb22222"],
            }
        )
        assert len(links) == 2
        types = {link.edge_type for link in links}
        assert types == {"relates", "supersedes"}

    def test_empty_dict(self) -> None:
        links = extract_frontmatter_links({})
        assert links == []

    def test_empty_target_list(self) -> None:
        links = extract_frontmatter_links({"relates": []})
        assert links == []

    def test_coerces_target_to_string(self) -> None:
        """Target IDs should be coerced to strings."""
        links = extract_frontmatter_links({"relates": [12345]})  # type: ignore[dict-item]
        assert links[0].target_id == "12345"

    def test_frozen_dataclass(self) -> None:
        link = FrontmatterLink(target_id="ztl_test", edge_type="relates")
        assert link.target_id == "ztl_test"
        assert link.edge_type == "relates"
