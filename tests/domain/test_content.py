"""Tests for ContentModel — frontmatter, body, validation, and registry."""

from datetime import date
from pathlib import Path

import pytest

from ztlctl.domain.content import (
    CONTENT_REGISTRY,
    ContentModel,
    DecisionModel,
    KnowledgeModel,
    NoteModel,
    ReferenceModel,
    TaskModel,
    ValidationResult,
    get_content_model,
    parse_frontmatter,
    register_content_model,
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

    def test_note_body_uses_user_template_override(self, tmp_path: Path) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )
        template_dir = tmp_path / ".ztlctl" / "templates" / "content"
        template_dir.mkdir(parents=True)
        (template_dir / "note.md.j2").write_text("override body: {{ body }}\n", encoding="utf-8")

        body = model.write_body(body="Hello world", template_root=tmp_path)

        assert body == "override body: Hello world\n"

    def test_note_body_falls_back_to_bundled_template(self, tmp_path: Path) -> None:
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="Test",
            created=date(2025, 1, 15),
        )

        body = model.write_body(body="Hello world", template_root=tmp_path)

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
# parse_frontmatter edge cases
# ---------------------------------------------------------------------------


class TestParseFrontmatterEdgeCases:
    def test_crlf_line_endings(self) -> None:
        """Windows-style \\r\\n should be handled correctly."""
        content = "---\r\nid: test\r\ntitle: Hello\r\n---\r\nBody here."
        fm, body = parse_frontmatter(content)
        assert fm["id"] == "test"
        assert fm["title"] == "Hello"
        assert body == "Body here."


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
# Full creation flow: model -> frontmatter + body -> file -> model
# ---------------------------------------------------------------------------


class TestFullCreationFlow:
    def test_note_create_and_read(self, tmp_path: Path) -> None:
        """Simulate the full creation pipeline."""
        model = NoteModel(
            id="ztl_abc12345",
            type="note",
            status="draft",
            title="My Note",
            tags=["test"],
            created=date(2025, 1, 15),
        )
        fm = model.to_frontmatter()
        body = model.write_body(body="Content goes here.")
        content = render_frontmatter(fm, body)
        path = tmp_path / "ztl_abc12345.md"
        path.write_text(content, encoding="utf-8")

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


# ---------------------------------------------------------------------------
# Validation — Decision (strict)
# ---------------------------------------------------------------------------


class TestDecisionValidation:
    def test_valid_create(self) -> None:
        result = DecisionModel.validate_create({"status": "proposed"})
        assert result.valid
        assert result.errors == []

    def test_non_proposed_status_rejected(self) -> None:
        result = DecisionModel.validate_create({"status": "accepted"})
        assert not result.valid
        assert any("proposed" in e for e in result.errors)

    def test_required_sections(self) -> None:
        assert DecisionModel.required_sections() == [
            "Context",
            "Choice",
            "Rationale",
            "Alternatives",
            "Consequences",
        ]

    def test_status_transitions_from_lifecycle(self) -> None:
        """Transitions delegate to lifecycle.py — single source of truth."""
        transitions = DecisionModel.status_transitions()
        assert transitions == {
            "proposed": ["accepted"],
            "accepted": ["superseded"],
            "superseded": [],
        }

    def test_update_blocks_body_change_after_accepted(self) -> None:
        """INVARIANT: Decisions are immutable after accepted."""
        existing = {"status": "accepted", "title": "Use PostgreSQL"}
        changes = {"body": "Modified content"}
        result = DecisionModel.validate_update(existing, changes)
        assert not result.valid
        assert any("accepted" in e.lower() for e in result.errors)

    def test_update_allows_status_transition(self) -> None:
        existing = {"status": "proposed"}
        changes = {"status": "accepted"}
        result = DecisionModel.validate_update(existing, changes)
        assert result.valid

    def test_update_blocks_invalid_transition(self) -> None:
        existing = {"status": "proposed"}
        changes = {"status": "superseded"}
        result = DecisionModel.validate_update(existing, changes)
        assert not result.valid

    def test_update_allows_metadata_after_accepted(self) -> None:
        """Tags, aliases, topic should still be editable after acceptance."""
        existing = {"status": "accepted"}
        changes = {"tags": ["new-tag"], "modified": "2026-02-25"}
        result = DecisionModel.validate_update(existing, changes)
        assert result.valid


# ---------------------------------------------------------------------------
# Validation — Knowledge (advisory)
# ---------------------------------------------------------------------------


class TestKnowledgeValidation:
    def test_valid_create(self) -> None:
        result = KnowledgeModel.validate_create({"key_points": ["point 1"]})
        assert result.valid

    def test_warns_on_missing_key_points(self) -> None:
        result = KnowledgeModel.validate_create({})
        assert result.valid  # advisory, not blocking
        assert len(result.warnings) > 0
        assert any("key_points" in w for w in result.warnings)

    def test_update_warns_on_empty_key_points(self) -> None:
        result = KnowledgeModel.validate_update({}, {"key_points": []})
        assert result.valid  # still valid, just warned
        assert len(result.warnings) > 0

    def test_update_always_valid(self) -> None:
        """Knowledge updates are advisory — never blocking."""
        result = KnowledgeModel.validate_update({}, {"body": "anything"})
        assert result.valid


# ---------------------------------------------------------------------------
# Validation — base models (permissive)
# ---------------------------------------------------------------------------


class TestBaseValidation:
    def test_note_always_valid_on_create(self) -> None:
        result = NoteModel.validate_create({})
        assert result.valid

    def test_reference_always_valid_on_create(self) -> None:
        result = ReferenceModel.validate_create({})
        assert result.valid

    def test_task_always_valid_on_create(self) -> None:
        result = TaskModel.validate_create({})
        assert result.valid

    def test_note_always_valid_on_update(self) -> None:
        result = NoteModel.validate_update({}, {"title": "new"})
        assert result.valid

    def test_reference_always_valid_on_update(self) -> None:
        result = ReferenceModel.validate_update({}, {"url": "https://new.url"})
        assert result.valid


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------


class TestStatusTransitions:
    def test_note_transitions(self) -> None:
        t = NoteModel.status_transitions()
        assert t["draft"] == ["linked"]
        assert t["linked"] == ["connected"]

    def test_reference_transitions(self) -> None:
        t = ReferenceModel.status_transitions()
        assert t == {"captured": ["annotated"], "annotated": []}

    def test_task_transitions(self) -> None:
        t = TaskModel.status_transitions()
        assert "active" in t["inbox"]
        assert "done" in t["active"]

    def test_base_returns_empty(self) -> None:
        assert ContentModel.status_transitions() == {}


# ---------------------------------------------------------------------------
# Content registry
# ---------------------------------------------------------------------------


class TestContentRegistry:
    def test_all_types_registered(self) -> None:
        assert set(CONTENT_REGISTRY.keys()) == {
            "note",
            "knowledge",
            "decision",
            "reference",
            "task",
        }

    def test_get_by_type(self) -> None:
        assert get_content_model("note") is NoteModel
        assert get_content_model("reference") is ReferenceModel
        assert get_content_model("task") is TaskModel

    def test_get_by_subtype(self) -> None:
        assert get_content_model("note", "decision") is DecisionModel
        assert get_content_model("note", "knowledge") is KnowledgeModel

    def test_subtype_takes_priority(self) -> None:
        """When subtype is registered, it wins over the base type."""
        cls = get_content_model("note", "decision")
        assert cls is DecisionModel

    def test_unknown_type_raises(self) -> None:
        with pytest.raises(KeyError):
            get_content_model("unknown")

    def test_unknown_subtype_falls_back_to_type(self) -> None:
        cls = get_content_model("note", "custom")
        assert cls is NoteModel

    def test_register_custom_subtype(self) -> None:
        original_registry = CONTENT_REGISTRY.copy()

        class FlashcardModel(NoteModel):
            _subtype_name = "flashcard"

        try:
            register_content_model("flashcard", FlashcardModel)
            assert get_content_model("note", "flashcard") is FlashcardModel
        finally:
            CONTENT_REGISTRY.clear()
            CONTENT_REGISTRY.update(original_registry)

    def test_register_rejects_builtin_name_collision(self) -> None:
        class PluginDecisionModel(NoteModel):
            _subtype_name = "decision"

        with pytest.raises(ValueError, match="built-in"):
            register_content_model("decision", PluginDecisionModel)

    def test_register_requires_concrete_content_type(self) -> None:
        class InvalidModel(ContentModel):
            _subtype_name = "invalid"

        with pytest.raises(ValueError, match="_content_type"):
            register_content_model("invalid", InvalidModel)


# ---------------------------------------------------------------------------
# ValidationResult
# ---------------------------------------------------------------------------


class TestValidationResult:
    def test_valid_result(self) -> None:
        r = ValidationResult(valid=True)
        assert r.valid
        assert r.errors == []
        assert r.warnings == []

    def test_invalid_result(self) -> None:
        r = ValidationResult(valid=False, errors=["bad"], warnings=["warn"])
        assert not r.valid
        assert r.errors == ["bad"]
        assert r.warnings == ["warn"]

    def test_frozen(self) -> None:
        r = ValidationResult(valid=True)
        with pytest.raises(Exception):
            r.valid = False  # type: ignore[misc]
