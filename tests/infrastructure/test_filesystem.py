"""Tests for filesystem operations — file I/O, path resolution, discovery."""

from pathlib import Path

import pytest

from ztlctl.domain.content import order_frontmatter, parse_frontmatter, render_frontmatter
from ztlctl.infrastructure.filesystem import (
    CONTENT_PATHS,
    find_content_files,
    read_content_file,
    resolve_content_path,
    write_content_file,
)


class TestParseFrontmatter:
    def test_basic_parse(self) -> None:
        content = "---\nid: ztl_abc12345\ntitle: Test\n---\nBody text here."
        fm, body = parse_frontmatter(content)
        assert fm["id"] == "ztl_abc12345"
        assert fm["title"] == "Test"
        assert body == "Body text here."

    def test_no_frontmatter(self) -> None:
        content = "Just plain text."
        fm, body = parse_frontmatter(content)
        assert fm == {}
        assert body == "Just plain text."

    def test_empty_content(self) -> None:
        fm, body = parse_frontmatter("")
        assert fm == {}
        assert body == ""

    def test_missing_closing_delimiter(self) -> None:
        content = "---\nid: test\nNo closing delimiter"
        fm, _body = parse_frontmatter(content)
        assert fm == {}  # Invalid, return as plain text

    def test_multiline_body(self) -> None:
        content = "---\nid: test\n---\nLine 1\nLine 2\nLine 3"
        fm, body = parse_frontmatter(content)
        assert fm["id"] == "test"
        assert "Line 1" in body
        assert "Line 3" in body

    def test_list_values(self) -> None:
        content = "---\ntags:\n  - a\n  - b\n---\nBody"
        fm, _body = parse_frontmatter(content)
        assert fm["tags"] == ["a", "b"]

    def test_nested_dict(self) -> None:
        content = "---\nlinks:\n  supports:\n    - ztl_abc\n---\nBody"
        fm, _body = parse_frontmatter(content)
        assert fm["links"]["supports"] == ["ztl_abc"]


class TestRenderFrontmatter:
    def test_basic_render(self) -> None:
        fm = {"id": "ztl_test", "type": "note", "title": "Test"}
        result = render_frontmatter(fm, "Body content")
        assert result.startswith("---\n")
        assert "id: ztl_test" in result
        assert result.endswith("Body content")

    def test_empty_body(self) -> None:
        fm = {"id": "test"}
        result = render_frontmatter(fm, "")
        assert result.count("---") == 2

    def test_canonical_ordering(self) -> None:
        fm = {"title": "Test", "id": "ztl_test", "type": "note"}
        result = render_frontmatter(fm, "")
        id_pos = result.index("id:")
        type_pos = result.index("type:")
        title_pos = result.index("title:")
        assert id_pos < type_pos < title_pos


class TestOrderFrontmatter:
    def test_canonical_order(self) -> None:
        fm = {"title": "Test", "id": "ztl_test", "type": "note", "status": "draft"}
        ordered = order_frontmatter(fm)
        keys = list(ordered.keys())
        assert keys.index("id") < keys.index("type")
        assert keys.index("type") < keys.index("status")
        assert keys.index("status") < keys.index("title")

    def test_unknown_keys_appended(self) -> None:
        fm = {"id": "test", "custom_field": "value"}
        ordered = order_frontmatter(fm)
        keys = list(ordered.keys())
        assert keys[-1] == "custom_field"

    def test_none_values_omitted(self) -> None:
        fm = {"id": "test", "subtype": None, "title": "Test"}
        ordered = order_frontmatter(fm)
        assert "subtype" not in ordered


class TestFileIO:
    def test_write_and_read_roundtrip(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        fm = {"id": "ztl_test", "type": "note", "title": "Test Note"}
        body = "This is the note body.\n"
        write_content_file(path, fm, body)
        read_fm, read_body = read_content_file(path)
        assert read_fm["id"] == "ztl_test"
        assert read_fm["title"] == "Test Note"
        assert "note body" in read_body

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        path = tmp_path / "deep" / "nested" / "dir" / "note.md"
        write_content_file(path, {"id": "test"}, "body")
        assert path.exists()

    def test_preserves_list_fields(self, tmp_path: Path) -> None:
        path = tmp_path / "test.md"
        fm = {"id": "test", "tags": ["a", "b", "c"]}
        write_content_file(path, fm, "")
        read_fm, _ = read_content_file(path)
        assert read_fm["tags"] == ["a", "b", "c"]


class TestResolveContentPath:
    def test_note_without_topic(self, vault_root: Path) -> None:
        path = resolve_content_path(vault_root, "note", "ztl_abc12345")
        assert path == vault_root / "notes" / "ztl_abc12345.md"

    def test_note_with_topic(self, vault_root: Path) -> None:
        path = resolve_content_path(vault_root, "note", "ztl_abc12345", topic="cognitive-science")
        assert path == vault_root / "notes" / "cognitive-science" / "ztl_abc12345.md"

    def test_reference(self, vault_root: Path) -> None:
        path = resolve_content_path(vault_root, "reference", "ref_abc12345")
        assert path == vault_root / "notes" / "ref_abc12345.md"

    def test_log_uses_jsonl(self, vault_root: Path) -> None:
        path = resolve_content_path(vault_root, "log", "LOG-0001")
        assert path == vault_root / "ops" / "logs" / "LOG-0001.jsonl"

    def test_task(self, vault_root: Path) -> None:
        path = resolve_content_path(vault_root, "task", "TASK-0001")
        assert path == vault_root / "ops" / "tasks" / "TASK-0001.md"

    def test_unknown_type_raises(self, vault_root: Path) -> None:
        with pytest.raises(ValueError, match="Unknown content type"):
            resolve_content_path(vault_root, "invalid", "id")


class TestFindContentFiles:
    def test_finds_markdown_files(self, vault_root: Path) -> None:
        (vault_root / "notes" / "ztl_abc.md").write_text("test")
        (vault_root / "notes" / "ref_def.md").write_text("test")
        results = find_content_files(vault_root)
        assert len(results) == 2

    def test_finds_jsonl_files(self, vault_root: Path) -> None:
        (vault_root / "ops" / "logs" / "LOG-0001.jsonl").write_text("{}")
        results = find_content_files(vault_root)
        assert len(results) == 1

    def test_filters_by_type(self, vault_root: Path) -> None:
        (vault_root / "notes" / "ztl_abc.md").write_text("test")
        (vault_root / "ops" / "tasks" / "TASK-0001.md").write_text("test")
        results = find_content_files(vault_root, content_type="task")
        assert len(results) == 1
        assert "TASK-0001" in results[0].name

    def test_empty_vault(self, vault_root: Path) -> None:
        results = find_content_files(vault_root)
        assert results == []

    def test_skips_dotfiles(self, vault_root: Path) -> None:
        (vault_root / "notes" / "ztl_abc.md").write_text("test")
        results = find_content_files(vault_root)
        assert all(".ztlctl" not in str(p) for p in results)

    def test_sorted_output(self, vault_root: Path) -> None:
        (vault_root / "notes" / "ztl_bbb.md").write_text("test")
        (vault_root / "notes" / "ztl_aaa.md").write_text("test")
        results = find_content_files(vault_root)
        assert results == sorted(results)

    def test_unknown_type_raises(self, vault_root: Path) -> None:
        with pytest.raises(ValueError, match="Unknown content type"):
            find_content_files(vault_root, content_type="invalid")


class TestContentPathsMapping:
    def test_all_types_mapped(self) -> None:
        assert set(CONTENT_PATHS.keys()) == {"note", "reference", "log", "task"}
