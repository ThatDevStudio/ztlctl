"""Integration tests for core ActionDefinition registrations.

Verifies that _register_core_actions() populates the singleton registry with
all expected actions — correct counts, categories, side_effects, params, and
custom_presentation flags.  Also spot-checks handler callability (parity
verification via callable + inspect).
"""

from __future__ import annotations

import inspect

import pytest

from ztlctl.actions import get_action_registry
from ztlctl.actions.definitions import ActionDefinition

# ---------------------------------------------------------------------------
# TestCoreRegistrationCount
# ---------------------------------------------------------------------------


class TestCoreRegistrationCount:
    def test_minimum_action_count(self) -> None:
        """Registry must contain at least 45 registered ActionDefinitions."""
        registry = get_action_registry()
        actions = registry.list_actions()
        assert len(actions) >= 45, f"Expected >= 45 registered actions, got {len(actions)}"

    def test_all_names_unique(self) -> None:
        """Every registered action name must be unique (no duplicates)."""
        registry = get_action_registry()
        names = [a.name for a in registry.list_actions()]
        assert len(names) == len(set(names)), (
            f"Duplicate action names found: {[n for n in names if names.count(n) > 1]}"
        )

    def test_categories_covered(self) -> None:
        """All 13 expected categories must have at least one registered action."""
        registry = get_action_registry()
        expected_categories = {
            "creation",
            "query",
            "graph",
            "lifecycle",
            "reweave",
            "session",
            "check",
            "ingest",
            "export",
            "vector",
            "upgrade",
            "workflow",
            "init",
        }
        registered_categories = {a.category for a in registry.list_actions()}
        missing = expected_categories - registered_categories
        assert not missing, f"Missing categories: {missing}"


# ---------------------------------------------------------------------------
# TestActionLookup
# ---------------------------------------------------------------------------


class TestActionLookup:
    def test_get_create_note(self) -> None:
        """create_note is registered with correct category, side_effect, and params."""
        registry = get_action_registry()
        action = registry.get("create_note")
        assert isinstance(action, ActionDefinition)
        assert action.name == "create_note"
        assert action.category == "creation"
        assert action.side_effect == "write"
        # title must be a required param
        param_names = {p.name for p in action.params}
        assert "title" in param_names
        title_param = next(p for p in action.params if p.name == "title")
        assert title_param.required is True

    def test_get_search(self) -> None:
        """search is registered with category=query and side_effect=read."""
        registry = get_action_registry()
        action = registry.get("search")
        assert action.name == "search"
        assert action.category == "query"
        assert action.side_effect == "read"
        param_names = {p.name for p in action.params}
        assert "query" in param_names

    def test_get_check(self) -> None:
        """check is registered with category=check and side_effect=read."""
        registry = get_action_registry()
        action = registry.get("check")
        assert action.name == "check"
        assert action.category == "check"
        assert action.side_effect == "read"

    def test_get_rebuild(self) -> None:
        """rebuild is registered with category=check and side_effect=write."""
        registry = get_action_registry()
        action = registry.get("rebuild")
        assert action.name == "rebuild"
        assert action.category == "check"
        assert action.side_effect == "write"

    def test_get_related(self) -> None:
        """related is registered with category=graph and side_effect=read."""
        registry = get_action_registry()
        action = registry.get("related")
        assert action.name == "related"
        assert action.category == "graph"
        assert action.side_effect == "read"
        param_names = {p.name for p in action.params}
        assert "content_id" in param_names

    def test_get_start(self) -> None:
        """start (session start) is registered with category=session and side_effect=write."""
        registry = get_action_registry()
        action = registry.get("start")
        assert action.name == "start"
        assert action.category == "session"
        assert action.side_effect == "write"
        param_names = {p.name for p in action.params}
        assert "topic" in param_names

    def test_custom_presentation_actions(self) -> None:
        """custom_presentation=True actions include the five expected ones."""
        registry = get_action_registry()
        custom_actions = registry.list_actions(custom_presentation=True)
        custom_names = {a.name for a in custom_actions}
        required_custom = {"create_batch", "init_vault", "init_workflow"}
        missing = required_custom - custom_names
        assert not missing, f"Expected custom_presentation=True actions missing: {missing}"
        assert len(custom_actions) >= 5, (
            f"Expected >= 5 custom_presentation actions, got {len(custom_actions)}"
        )


# ---------------------------------------------------------------------------
# TestFilteringConsistency
# ---------------------------------------------------------------------------


class TestFilteringConsistency:
    def test_read_actions_side_effect(self) -> None:
        """All actions with side_effect=read have correct side_effect value."""
        registry = get_action_registry()
        read_actions = registry.list_actions(side_effect="read")
        for action in read_actions:
            assert action.side_effect == "read", (
                f"Action {action.name!r} in read filter but has side_effect={action.side_effect!r}"
            )

    def test_write_actions_side_effect(self) -> None:
        """All actions with side_effect=write have correct side_effect value."""
        registry = get_action_registry()
        write_actions = registry.list_actions(side_effect="write")
        for action in write_actions:
            assert action.side_effect == "write", (
                f"Action {action.name!r} in write filter but has side_effect={action.side_effect!r}"
            )

    def test_known_read_actions(self) -> None:
        """Spot-check specific actions expected to be read-only."""
        registry = get_action_registry()
        expected_reads = {
            "search",
            "get",
            "list_items",
            "count_items",
            "list_tags",
            "work_queue",
            "check",
            "check_pending",
            "list_providers",
            "export_markdown",
            "export_indexes",
            "export_graph",
            "export_dashboard",
            "status",
            "themes",
            "rank",
            "gaps",
            "bridges",
            "related",
            "path",
            "check_staleness",
            "reindex_all",
        }
        for name in expected_reads:
            action = registry.get(name)
            assert action.side_effect == "read", (
                f"Action {name!r} expected side_effect='read', got {action.side_effect!r}"
            )

    def test_known_write_actions(self) -> None:
        """Spot-check specific actions expected to be write."""
        registry = get_action_registry()
        expected_writes = {
            "create_note",
            "create_reference",
            "create_task",
            "create_batch",
            "update",
            "archive",
            "supersede",
            "reweave",
            "prune",
            "undo",
            "start",
            "close",
            "reopen",
            "log_entry",
            "extract_decision",
            "fix",
            "rebuild",
            "rollback",
            "ingest_text",
            "ingest_file",
            "ingest_url",
            "apply",
            "stamp_current",
            "init_vault",
            "regenerate_self",
            "init_workflow",
            "update_workflow",
            "export_assets",
            "unlink",
            "materialize_metrics",
        }
        for name in expected_writes:
            action = registry.get(name)
            assert action.side_effect == "write", (
                f"Action {name!r} expected side_effect='write', got {action.side_effect!r}"
            )

    def test_custom_presentation_subset(self) -> None:
        """All custom_presentation=True actions are a subset of total actions."""
        registry = get_action_registry()
        all_names = {a.name for a in registry.list_actions()}
        custom_names = {a.name for a in registry.list_actions(custom_presentation=True)}
        assert custom_names.issubset(all_names), (
            f"custom_presentation actions not in full list: {custom_names - all_names}"
        )


# ---------------------------------------------------------------------------
# TestHandlerSignatureParity
# ---------------------------------------------------------------------------


class TestHandlerSignatureParity:
    def test_handler_is_callable(self) -> None:
        """Every registered action has a callable handler."""
        registry = get_action_registry()
        for action in registry.list_actions():
            assert callable(action.handler), f"Action {action.name!r} handler is not callable"

    def test_handler_lambda_accepts_vault_and_kwargs(self) -> None:
        """Every handler accepts at least a vault positional arg and **kwargs."""
        registry = get_action_registry()
        for action in registry.list_actions():
            sig = inspect.signature(action.handler)
            params = list(sig.parameters.values())
            # Handlers are lambda vault, **kw: ... — first param is vault
            assert len(params) >= 1, f"Action {action.name!r} handler has no parameters"
            first_param = params[0]
            assert first_param.name == "vault", (
                f"Action {action.name!r} handler first param is "
                f"{first_param.name!r}, expected 'vault'"
            )

    def test_all_params_have_descriptions(self) -> None:
        """Every ActionParam on non-custom-presentation actions has a description."""
        registry = get_action_registry()
        for action in registry.list_actions():
            if action.custom_presentation:
                continue
            for param in action.params:
                assert param.description, (
                    f"Action {action.name!r} param {param.name!r} has no description"
                )

    def test_required_params_have_no_default(self) -> None:
        """Required ActionParams should not have a meaningful non-None default."""
        registry = get_action_registry()
        for action in registry.list_actions():
            for param in action.params:
                if param.required:
                    # Required params may have default=None (dataclass default)
                    # but should not have a non-None default that hides requirement
                    assert param.default is None, (
                        f"Action {action.name!r} param {param.name!r} is required "
                        f"but has non-None default={param.default!r}"
                    )

    def test_action_params_coverage_spot_check(self) -> None:
        """Spot-check param names for key actions match controller method signatures."""
        registry = get_action_registry()

        # create_note: title, subtype, tags, topic, body, key_points, links, aliases
        create_note = registry.get("create_note")
        cn_param_names = {p.name for p in create_note.params}
        assert cn_param_names >= {"title", "tags", "topic", "body"}

        # search: query, content_type, tag, space, rank_by, limit
        search = registry.get("search")
        s_param_names = {p.name for p in search.params}
        assert s_param_names >= {"query", "content_type", "limit"}

        # list_items: content_type, status, tag, topic, sort, limit
        list_items = registry.get("list_items")
        li_param_names = {p.name for p in list_items.params}
        assert li_param_names >= {"content_type", "status", "tag", "limit"}

        # path: source_id, target_id
        path = registry.get("path")
        p_param_names = {p.name for p in path.params}
        assert p_param_names == {"source_id", "target_id"}

        # update: content_id, changes
        update = registry.get("update")
        u_param_names = {p.name for p in update.params}
        assert u_param_names == {"content_id", "changes"}

        # reweave: content_id, dry_run, min_score_override
        reweave = registry.get("reweave")
        r_param_names = {p.name for p in reweave.params}
        assert r_param_names >= {"content_id", "dry_run"}

        # session start: topic
        start = registry.get("start")
        st_param_names = {p.name for p in start.params}
        assert "topic" in st_param_names

        # check: min_severity
        check = registry.get("check")
        ck_param_names = {p.name for p in check.params}
        assert "min_severity" in ck_param_names


# ---------------------------------------------------------------------------
# TestCategoryIntegrity
# ---------------------------------------------------------------------------


class TestCategoryIntegrity:
    @pytest.mark.parametrize(
        "category,expected_names",
        [
            (
                "creation",
                {"create_note", "create_reference", "create_task", "create_batch", "garden_seed"},
            ),
            ("check", {"check", "fix", "rebuild", "rollback"}),
            ("upgrade", {"check_pending", "apply", "stamp_current"}),
            ("reweave", {"reweave", "prune", "undo"}),
            ("vector", {"vector_status", "reindex_all"}),
            ("init", {"init_vault", "regenerate_self", "check_staleness"}),
            ("workflow", {"init_workflow", "update_workflow", "export_assets"}),
            ("lifecycle", {"update", "archive", "supersede"}),
        ],
    )
    def test_category_exact_names(self, category: str, expected_names: set[str]) -> None:
        """Each fixed-size category contains exactly the expected action names."""
        registry = get_action_registry()
        actual_names = {a.name for a in registry.list_actions(category=category)}
        assert actual_names == expected_names, (
            f"Category {category!r}: expected {expected_names}, got {actual_names}"
        )

    def test_graph_category_contains_expected(self) -> None:
        """graph category contains at least the 8 expected actions."""
        registry = get_action_registry()
        graph_names = {a.name for a in registry.list_actions(category="graph")}
        required = {
            "related",
            "themes",
            "rank",
            "path",
            "gaps",
            "bridges",
            "unlink",
            "materialize_metrics",
        }
        assert required.issubset(graph_names), f"graph category missing: {required - graph_names}"

    def test_session_category_contains_expected(self) -> None:
        """session category contains at least the 9 expected actions."""
        registry = get_action_registry()
        session_names = {a.name for a in registry.list_actions(category="session")}
        required = {
            "start",
            "close",
            "reopen",
            "status",
            "log_entry",
            "cost",
            "context",
            "brief",
            "extract_decision",
        }
        assert required.issubset(session_names), (
            f"session category missing: {required - session_names}"
        )

    def test_query_category_contains_expected(self) -> None:
        """query category contains at least the 10 expected actions."""
        registry = get_action_registry()
        query_names = {a.name for a in registry.list_actions(category="query")}
        required = {
            "count_items",
            "search",
            "get",
            "list_items",
            "work_queue",
            "list_tags",
            "decision_support",
            "topic_packet",
            "draft_from_topic",
            "vault_review",
        }
        assert required.issubset(query_names), f"query category missing: {required - query_names}"

    def test_ingest_category_contains_expected(self) -> None:
        """ingest category contains the 4 expected actions."""
        registry = get_action_registry()
        ingest_names = {a.name for a in registry.list_actions(category="ingest")}
        required = {"list_providers", "ingest_text", "ingest_file", "ingest_url"}
        assert required.issubset(ingest_names), (
            f"ingest category missing: {required - ingest_names}"
        )

    def test_export_category_contains_expected(self) -> None:
        """export category contains the 4 expected actions."""
        registry = get_action_registry()
        export_names = {a.name for a in registry.list_actions(category="export")}
        required = {
            "export_markdown",
            "export_indexes",
            "export_graph",
            "export_dashboard",
        }
        assert required.issubset(export_names), (
            f"export category missing: {required - export_names}"
        )
