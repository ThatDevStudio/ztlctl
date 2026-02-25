"""Tests for ExportService — markdown, indexes, and graph export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from ztlctl.services.export import ExportService

if TYPE_CHECKING:
    from ztlctl.infrastructure.vault import Vault


class TestExportMarkdown:
    """Tests for ExportService.export_markdown()."""

    def test_export_empty_vault(self, vault: Vault, tmp_path: Path) -> None:
        output = tmp_path / "export"
        result = ExportService(vault).export_markdown(output)
        assert result.ok
        assert result.op == "export_markdown"
        assert result.data["file_count"] == 0

    def test_export_with_notes(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note

        create_note(vault, "First Note")
        create_note(vault, "Second Note")

        output = tmp_path / "export"
        result = ExportService(vault).export_markdown(output)
        assert result.ok
        assert result.data["file_count"] == 2
        assert output.is_dir()

    def test_export_preserves_relative_paths(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note

        data = create_note(vault, "Topical Note", topic="research")
        # data["path"] is relative to vault root (e.g. "notes/research/ztl_xxx.md")
        rel_path = Path(data["path"])

        output = tmp_path / "export"
        ExportService(vault).export_markdown(output)
        assert (output / rel_path).is_file()

    def test_export_mixed_content_types(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note, create_reference, create_task

        create_note(vault, "A Note")
        create_reference(vault, "A Reference")
        create_task(vault, "A Task")

        output = tmp_path / "export"
        result = ExportService(vault).export_markdown(output)
        assert result.ok
        assert result.data["file_count"] == 3

    def test_export_creates_output_dir(self, vault: Vault, tmp_path: Path) -> None:
        output = tmp_path / "nested" / "export"
        result = ExportService(vault).export_markdown(output)
        assert result.ok
        assert output.is_dir()

    def test_export_output_dir_in_result(self, vault: Vault, tmp_path: Path) -> None:
        output = tmp_path / "export"
        result = ExportService(vault).export_markdown(output)
        assert str(output) in result.data["output_dir"]


class TestExportIndexes:
    """Tests for ExportService.export_indexes()."""

    def test_indexes_empty_vault(self, vault: Vault, tmp_path: Path) -> None:
        output = tmp_path / "indexes"
        result = ExportService(vault).export_indexes(output)
        assert result.ok
        assert result.op == "export_indexes"
        assert result.data["node_count"] == 0
        assert (output / "index.md").is_file()

    def test_indexes_master_index(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note, create_reference

        create_note(vault, "Note One")
        create_reference(vault, "Ref One")

        output = tmp_path / "indexes"
        ExportService(vault).export_indexes(output)
        index_content = (output / "index.md").read_text()
        assert "Vault Index" in index_content
        assert "Total: 2 items" in index_content

    def test_indexes_by_type(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note, create_task

        create_note(vault, "Note A")
        create_task(vault, "Task A")

        output = tmp_path / "indexes"
        ExportService(vault).export_indexes(output)
        assert (output / "by-type" / "note.md").is_file()
        assert (output / "by-type" / "task.md").is_file()
        note_index = (output / "by-type" / "note.md").read_text()
        assert "Note A" in note_index

    def test_indexes_by_topic(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note

        create_note(vault, "Topical Note", topic="research")

        output = tmp_path / "indexes"
        ExportService(vault).export_indexes(output)
        assert (output / "by-topic" / "research.md").is_file()
        topic_content = (output / "by-topic" / "research.md").read_text()
        assert "Topical Note" in topic_content

    def test_indexes_files_created_list(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note

        create_note(vault, "Index Test")

        output = tmp_path / "indexes"
        result = ExportService(vault).export_indexes(output)
        assert "index.md" in result.data["files_created"]
        assert "by-type/note.md" in result.data["files_created"]

    def test_indexes_wikilinks(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note

        data = create_note(vault, "Linked Note")
        output = tmp_path / "indexes"
        ExportService(vault).export_indexes(output)
        type_content = (output / "by-type" / "note.md").read_text()
        assert f"[[{data['id']}]]" in type_content

    def test_indexes_with_tags(self, vault: Vault, tmp_path: Path) -> None:
        from tests.conftest import create_note

        create_note(vault, "Tagged Note", tags=["ai/ml"])
        output = tmp_path / "indexes"
        ExportService(vault).export_indexes(output)
        type_content = (output / "by-type" / "note.md").read_text()
        assert "ai/ml" in type_content


class TestExportGraph:
    """Tests for ExportService.export_graph()."""

    def test_graph_dot_empty(self, vault: Vault) -> None:
        result = ExportService(vault).export_graph(fmt="dot")
        assert result.ok
        assert result.op == "export_graph"
        assert result.data["format"] == "dot"
        assert "digraph vault" in result.data["content"]
        assert result.data["node_count"] == 0

    def test_graph_json_empty(self, vault: Vault) -> None:
        result = ExportService(vault).export_graph(fmt="json")
        assert result.ok
        d3 = json.loads(result.data["content"])
        assert d3["nodes"] == []
        assert d3["links"] == []

    def test_graph_dot_with_nodes(self, vault: Vault) -> None:
        from tests.conftest import create_note

        create_note(vault, "Node A")
        create_note(vault, "Node B")

        # Invalidate cached graph so it picks up new nodes
        vault.graph.invalidate()
        result = ExportService(vault).export_graph(fmt="dot")
        assert result.ok
        assert result.data["node_count"] == 2
        content = result.data["content"]
        assert "Node A" in content
        assert "Node B" in content

    def test_graph_json_with_nodes(self, vault: Vault) -> None:
        from tests.conftest import create_note

        create_note(vault, "JSON Node")
        vault.graph.invalidate()
        result = ExportService(vault).export_graph(fmt="json")
        d3 = json.loads(result.data["content"])
        assert len(d3["nodes"]) == 1
        assert d3["nodes"][0]["title"] == "JSON Node"

    def test_graph_dot_with_edges(self, vault: Vault) -> None:
        from sqlalchemy import text

        from tests.conftest import create_note

        data_a = create_note(vault, "Alpha")
        data_b = create_note(vault, "Beta")

        # Insert edge directly
        with vault.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO edges (source_id, target_id, edge_type, weight, created) "
                    "VALUES (:s, :t, 'relates', 1.0, '2024-01-01')"
                ),
                {"s": data_b["id"], "t": data_a["id"]},
            )

        vault.graph.invalidate()
        result = ExportService(vault).export_graph(fmt="dot")
        content = result.data["content"]
        assert "->" in content
        assert result.data["edge_count"] > 0

    def test_graph_json_with_edges(self, vault: Vault) -> None:
        from sqlalchemy import text

        from tests.conftest import create_note

        data_a = create_note(vault, "Source")
        data_b = create_note(vault, "Target")

        with vault.engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO edges (source_id, target_id, edge_type, weight, created) "
                    "VALUES (:s, :t, 'relates', 1.0, '2024-01-01')"
                ),
                {"s": data_b["id"], "t": data_a["id"]},
            )

        vault.graph.invalidate()
        result = ExportService(vault).export_graph(fmt="json")
        d3 = json.loads(result.data["content"])
        assert len(d3["links"]) > 0
        assert "source" in d3["links"][0]
        assert "target" in d3["links"][0]

    def test_graph_invalid_format(self, vault: Vault) -> None:
        result = ExportService(vault).export_graph(fmt="svg")
        assert not result.ok
        assert result.error is not None
        assert result.error.code == "INVALID_FORMAT"

    def test_graph_default_format(self, vault: Vault) -> None:
        result = ExportService(vault).export_graph()
        assert result.ok
        assert result.data["format"] == "dot"
