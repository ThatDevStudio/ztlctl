"""Tests for ContentModel — frontmatter schema + body methods."""

from datetime import date
from pathlib import Path

import pytest

from ztlctl.domain.content import (
    ContentModel,
    DecisionModel,
    KnowledgeModel,
    NoteModel,
    ReferenceModel,
    TaskModel,
    render_frontmatter,
)

# ---------------------------------------------------------------------------
# ContentModel base
# ---------------------------------------------------------------------------


class TestContentModelAttributes:
    """Attributes map 1:1 to frontmatter keys."""

    def test_required_fields(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test Note",
            created=date(2025, 1, 15),
        )
        assert model.id == "ztl_abc12345"
        assert model.type == "note"
        assert model.status == "draft"
        assert model.title == "Test Note"
        assert model.created == date(2025, 1, 15)

    def test_optional_fields_default(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        assert model.session is None
        assert model.tags == []
        assert model.modified is None

    def test_frozen(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        with pytest.raises(Exception):
            model.title = "Changed"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# to_frontmatter
# ---------------------------------------------------------------------------


class TestToFrontmatter:
    def test_returns_ordered_dict(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test Note",
            tags=["python", "testing"],
            created=date(2025, 1, 15),
        )
        fm = model.to_frontmatter()
        keys = list(fm.keys())
        assert keys.index("id") < keys.index("type")
        assert keys.index("type") < keys.index("status")
        assert keys.index("status") < keys.index("title")

    def test_excludes_none_values(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        fm = model.to_frontmatter()
        assert "session" not in fm
        assert "modified" not in fm
        assert "subtype" not in fm

    def test_includes_set_values(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            tags=["a", "b"],
            session="LOG-0001",
            created=date(2025, 1, 15),
        )
        fm = model.to_frontmatter()
        assert fm["tags"] == ["a", "b"]
        assert fm["session"] == "LOG-0001"

    def test_json_serialization_mode(self) -> None:
        """Dates serialize to ISO strings in JSON mode."""
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        fm = model.to_frontmatter()
        assert fm["created"] == "2025-01-15"


# ---------------------------------------------------------------------------
# write_body
# ---------------------------------------------------------------------------


class TestWriteBody:
    def test_note_body(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        body = model.write_body(body="Hello world")
        assert "Hello world" in body

    def test_note_empty_body(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        body = model.write_body()
        assert body.strip() == ""

    def test_decision_body_sections(self) -> None:
        model = DecisionModel(
            id="ztl_abc12345",
            type="note",
            subtype="decision",
            status="proposed",
            title="Use SQLite",
            created=date(2025, 1, 15),
        )
        body = model.write_body(
            context="We need a database",
            choice="SQLite",
            rationale="Simple, embedded",
            alternatives="PostgreSQL",
            consequences="Single-writer",
        )
        assert "## Context" in body
        assert "We need a database" in body
        assert "## Choice" in body
        assert "SQLite" in body
        assert "## Rationale" in body
        assert "Simple, embedded" in body
        assert "## Alternatives" in body
        assert "PostgreSQL" in body
        assert "## Consequences" in body
        assert "Single-writer" in body

    def test_decision_empty_sections(self) -> None:
        model = DecisionModel(
            id="ztl_abc12345",
            type="note",
            subtype="decision",
            status="proposed",
            title="Test",
            created=date(2025, 1, 15),
        )
        body = model.write_body()
        assert "## Context" in body
        assert "## Consequences" in body

    def test_task_body(self) -> None:
        model = TaskModel(
            id="TASK-0001",
            type="task",
            status="inbox",
            title="Fix bug",
            created=date(2025, 1, 15),
        )
        body = model.write_body(body="Steps to reproduce...")
        assert "Steps to reproduce..." in body

    def test_reference_body(self) -> None:
        model = ReferenceModel(
            id="ref_abc12345",
            type="reference",
            status="captured",
            title="Cool Article",
            url="https://example.com",
            created=date(2025, 1, 15),
        )
        body = model.write_body(body="Key takeaways...")
        assert "Key takeaways..." in body


# ---------------------------------------------------------------------------
# read_body
# ---------------------------------------------------------------------------


class TestReadBody:
    def test_returns_raw_string(self) -> None:
        raw = "## Context\n\nSome content\n\n## Choice\n\nSQLite"
        assert ContentModel.read_body(raw) == raw

    def test_empty_body(self) -> None:
        assert ContentModel.read_body("") == ""


# ---------------------------------------------------------------------------
# from_file
# ---------------------------------------------------------------------------


class TestFromFile:
    def test_note_roundtrip(self, tmp_path: Path) -> None:
        """Write a file with render_frontmatter, read it back with from_file."""
        fm = {
            "id": "ztl_abc12345",
            "type": "note",
            "status": "draft",
            "title": "Test Note",
            "tags": ["python"],
            "created": "2025-01-15",
        }
        body = "This is the body.\n"
        content = render_frontmatter(fm, body)
        path = tmp_path / "test.md"
        path.write_text(content, encoding="utf-8")

        model, read_body = NoteModel.from_file(path)
        assert model.id == "ztl_abc12345"
        assert model.title == "Test Note"
        assert model.tags == ["python"]
        assert "body" in read_body

    def test_decision_from_file(self, tmp_path: Path) -> None:
        fm = {
            "id": "ztl_dec12345",
            "type": "note",
            "subtype": "decision",
            "status": "proposed",
            "title": "Use SQLite",
            "tags": [],
            "created": "2025-01-15",
        }
        body = "## Context\n\nNeed a DB\n\n## Choice\n\nSQLite\n"
        content = render_frontmatter(fm, body)
        path = tmp_path / "decision.md"
        path.write_text(content, encoding="utf-8")

        model, read_body = DecisionModel.from_file(path)
        assert model.subtype == "decision"
        assert model.status == "proposed"
        assert "## Context" in read_body
        assert "Need a DB" in read_body

    def test_task_from_file(self, tmp_path: Path) -> None:
        fm = {
            "id": "TASK-0001",
            "type": "task",
            "status": "inbox",
            "title": "Fix bug",
            "priority": "high",
            "created": "2025-01-15",
        }
        body = "Reproduce and fix.\n"
        content = render_frontmatter(fm, body)
        path = tmp_path / "task.md"
        path.write_text(content, encoding="utf-8")

        model, read_body = TaskModel.from_file(path)
        assert model.priority == "high"
        assert "Reproduce" in read_body

    def test_reference_with_url(self, tmp_path: Path) -> None:
        fm = {
            "id": "ref_abc12345",
            "type": "reference",
            "status": "captured",
            "title": "Good Article",
            "url": "https://example.com/article",
            "created": "2025-01-15",
        }
        content = render_frontmatter(fm, "Summary here.\n")
        path = tmp_path / "ref.md"
        path.write_text(content, encoding="utf-8")

        model, _ = ReferenceModel.from_file(path)
        assert model.url == "https://example.com/article"

    def test_knowledge_with_key_points(self, tmp_path: Path) -> None:
        fm = {
            "id": "ztl_kno12345",
            "type": "note",
            "subtype": "knowledge",
            "status": "draft",
            "title": "Learning Note",
            "key_points": ["point 1", "point 2"],
            "created": "2025-01-15",
        }
        content = render_frontmatter(fm, "Details.\n")
        path = tmp_path / "knowledge.md"
        path.write_text(content, encoding="utf-8")

        model, _ = KnowledgeModel.from_file(path)
        assert model.key_points == ["point 1", "point 2"]


# ---------------------------------------------------------------------------
# Concrete model specific fields
# ---------------------------------------------------------------------------


class TestConcreteModels:
    def test_note_extra_fields(self) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            aliases=["alt-name"],
            topic="cognitive-science",
            links={"supports": ["ztl_def12345"]},
            created=date(2025, 1, 15),
        )
        assert model.aliases == ["alt-name"]
        assert model.topic == "cognitive-science"
        assert model.links == {"supports": ["ztl_def12345"]}

    def test_knowledge_inherits_note(self) -> None:
        model = KnowledgeModel(
            id="ztl_abc12345",
            type="note",
            subtype="knowledge",
            status="draft",
            title="Test",
            key_points=["kp1"],
            topic="math",
            created=date(2025, 1, 15),
        )
        assert model.key_points == ["kp1"]
        assert model.topic == "math"  # inherited from NoteModel

    def test_decision_inherits_note(self) -> None:
        model = DecisionModel(
            id="ztl_abc12345",
            type="note",
            subtype="decision",
            status="proposed",
            title="Test",
            supersedes="ztl_old12345",
            created=date(2025, 1, 15),
        )
        assert model.supersedes == "ztl_old12345"
        assert model.superseded_by is None

    def test_reference_extra_fields(self) -> None:
        model = ReferenceModel(
            id="ref_abc12345",
            type="reference",
            status="captured",
            title="Test",
            subtype="article",
            url="https://example.com",
            created=date(2025, 1, 15),
        )
        assert model.subtype == "article"
        assert model.url == "https://example.com"

    def test_task_extra_fields(self) -> None:
        model = TaskModel(
            id="TASK-0001",
            type="task",
            status="inbox",
            title="Test",
            priority="high",
            impact="low",
            effort="small",
            created=date(2025, 1, 15),
        )
        assert model.priority == "high"
        assert model.impact == "low"
        assert model.effort == "small"

    def test_task_defaults(self) -> None:
        model = TaskModel(
            id="TASK-0001",
            type="task",
            status="inbox",
            title="Test",
            created=date(2025, 1, 15),
        )
        assert model.priority == "medium"
        assert model.impact == "medium"
        assert model.effort == "medium"


# ---------------------------------------------------------------------------
# Full creation flow: model → frontmatter + body → file → model
# ---------------------------------------------------------------------------


class TestFullCreationFlow:
    def test_note_create_and_read(self, tmp_path: Path) -> None:
        """Simulate the full creation pipeline."""
        # 1. Create model
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="My Note",
            tags=["test"],
            created=date(2025, 1, 15),
        )
        # 2. Generate frontmatter + body
        fm = model.to_frontmatter()
        body = model.write_body(body="Content goes here.")
        # 3. Write to file
        content = render_frontmatter(fm, body)
        path = tmp_path / "ztl_abc12345.md"
        path.write_text(content, encoding="utf-8")
        # 4. Read back
        loaded, loaded_body = NoteModel.from_file(path)
        assert loaded.id == model.id
        assert loaded.title == model.title
        assert "Content goes here" in loaded_body

    def test_decision_create_and_read(self, tmp_path: Path) -> None:
        model = DecisionModel(
            id="ztl_dec12345",
            type="note",
            subtype="decision",
            status="proposed",
            title="Architecture Choice",
            tags=["arch"],
            created=date(2025, 1, 15),
        )
        fm = model.to_frontmatter()
        body = model.write_body(
            context="We need X",
            choice="Option A",
            rationale="Because reasons",
            alternatives="Option B, C",
            consequences="Must maintain A",
        )
        content = render_frontmatter(fm, body)
        path = tmp_path / "decision.md"
        path.write_text(content, encoding="utf-8")

        loaded, loaded_body = DecisionModel.from_file(path)
        assert loaded.subtype == "decision"
        assert "## Context" in loaded_body
        assert "We need X" in loaded_body
        assert "## Consequences" in loaded_body
