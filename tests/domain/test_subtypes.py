"""Tests for concrete subtype rules and the registry."""

from ztlctl.domain.subtypes import (
    SUBTYPE_REGISTRY,
    DecisionSubtypeRule,
    KnowledgeSubtypeRule,
    ReferenceSubtypeRule,
)


class TestSubtypeRegistry:
    def test_all_subtypes_registered(self) -> None:
        assert set(SUBTYPE_REGISTRY.keys()) == {
            "decision",
            "knowledge",
            "article",
            "tool",
            "spec",
        }

    def test_decision_is_decision_rule(self) -> None:
        assert isinstance(SUBTYPE_REGISTRY["decision"], DecisionSubtypeRule)

    def test_knowledge_is_knowledge_rule(self) -> None:
        assert isinstance(SUBTYPE_REGISTRY["knowledge"], KnowledgeSubtypeRule)

    def test_reference_subtypes_are_reference_rules(self) -> None:
        for name in ("article", "tool", "spec"):
            assert isinstance(SUBTYPE_REGISTRY[name], ReferenceSubtypeRule)


class TestDecisionSubtypeRule:
    def _valid_content(self) -> dict[str, object]:
        return {
            "id": "ztl_abcd1234",
            "type": "note",
            "subtype": "decision",
            "status": "proposed",
            "title": "Use PostgreSQL",
            "tags": ["engineering/databases"],
            "created": "2026-02-24",
        }

    def test_valid_create(self) -> None:
        rule = DecisionSubtypeRule()
        result = rule.validate_create(self._valid_content())
        assert result.valid
        assert result.errors == []

    def test_missing_required_field(self) -> None:
        rule = DecisionSubtypeRule()
        content = self._valid_content()
        del content["title"]
        result = rule.validate_create(content)
        assert not result.valid
        assert any("title" in e for e in result.errors)

    def test_wrong_subtype_rejected(self) -> None:
        rule = DecisionSubtypeRule()
        content = self._valid_content()
        content["subtype"] = "knowledge"
        result = rule.validate_create(content)
        assert not result.valid

    def test_non_proposed_status_rejected(self) -> None:
        rule = DecisionSubtypeRule()
        content = self._valid_content()
        content["status"] = "accepted"
        result = rule.validate_create(content)
        assert not result.valid

    def test_required_sections(self) -> None:
        rule = DecisionSubtypeRule()
        sections = rule.required_sections()
        assert sections == [
            "Context",
            "Choice",
            "Rationale",
            "Alternatives",
            "Consequences",
        ]

    def test_name_and_parent(self) -> None:
        rule = DecisionSubtypeRule()
        assert rule.name == "decision"
        assert rule.parent_type == "note"

    def test_update_blocks_body_change_after_accepted(self) -> None:
        """INVARIANT: Decisions are immutable after accepted."""
        rule = DecisionSubtypeRule()
        existing = {"status": "accepted", "title": "Use PostgreSQL"}
        changes = {"body": "Modified content"}
        result = rule.validate_update(existing, changes)
        assert not result.valid
        assert any("accepted" in e.lower() for e in result.errors)

    def test_update_allows_status_transition(self) -> None:
        rule = DecisionSubtypeRule()
        existing = {"status": "proposed"}
        changes = {"status": "accepted"}
        result = rule.validate_update(existing, changes)
        assert result.valid

    def test_update_blocks_invalid_transition(self) -> None:
        rule = DecisionSubtypeRule()
        existing = {"status": "proposed"}
        changes = {"status": "superseded"}
        result = rule.validate_update(existing, changes)
        assert not result.valid

    def test_update_allows_metadata_after_accepted(self) -> None:
        """Tags, aliases, topic should still be editable after acceptance."""
        rule = DecisionSubtypeRule()
        existing = {"status": "accepted"}
        changes = {"tags": ["new-tag"], "modified": "2026-02-25"}
        result = rule.validate_update(existing, changes)
        assert result.valid

    def test_allowed_transitions(self) -> None:
        rule = DecisionSubtypeRule()
        transitions = rule.allowed_status_transitions()
        assert transitions == {
            "proposed": ["accepted"],
            "accepted": ["superseded"],
            "superseded": [],
        }


class TestKnowledgeSubtypeRule:
    def test_valid_create(self) -> None:
        rule = KnowledgeSubtypeRule()
        content = {
            "subtype": "knowledge",
            "key_points": ["point 1"],
        }
        result = rule.validate_create(content)
        assert result.valid

    def test_warns_on_missing_key_points(self) -> None:
        rule = KnowledgeSubtypeRule()
        content = {"subtype": "knowledge"}
        result = rule.validate_create(content)
        assert result.valid  # advisory, not blocking
        assert len(result.warnings) > 0
        assert any("key_points" in w for w in result.warnings)

    def test_wrong_subtype_rejected(self) -> None:
        rule = KnowledgeSubtypeRule()
        content = {"subtype": "decision"}
        result = rule.validate_create(content)
        assert not result.valid

    def test_update_warns_on_empty_key_points(self) -> None:
        rule = KnowledgeSubtypeRule()
        result = rule.validate_update({}, {"key_points": []})
        assert result.valid  # still valid, just warned
        assert len(result.warnings) > 0

    def test_update_always_valid(self) -> None:
        """Knowledge updates are advisory — never blocking."""
        rule = KnowledgeSubtypeRule()
        result = rule.validate_update({}, {"body": "anything"})
        assert result.valid

    def test_name_and_parent(self) -> None:
        rule = KnowledgeSubtypeRule()
        assert rule.name == "knowledge"
        assert rule.parent_type == "note"


class TestReferenceSubtypeRule:
    def test_always_valid_on_create(self) -> None:
        rule = ReferenceSubtypeRule("article")
        result = rule.validate_create({})
        assert result.valid
        assert result.errors == []

    def test_always_valid_on_update(self) -> None:
        rule = ReferenceSubtypeRule("tool")
        result = rule.validate_update({}, {"url": "https://new.url"})
        assert result.valid

    def test_parameterized_name(self) -> None:
        assert ReferenceSubtypeRule("article").name == "article"
        assert ReferenceSubtypeRule("tool").name == "tool"
        assert ReferenceSubtypeRule("spec").name == "spec"

    def test_parent_type_is_reference(self) -> None:
        rule = ReferenceSubtypeRule("article")
        assert rule.parent_type == "reference"

    def test_no_required_sections(self) -> None:
        rule = ReferenceSubtypeRule("article")
        assert rule.required_sections() == []

    def test_transitions(self) -> None:
        rule = ReferenceSubtypeRule("article")
        assert rule.allowed_status_transitions() == {
            "captured": ["annotated"],
            "annotated": [],
        }
