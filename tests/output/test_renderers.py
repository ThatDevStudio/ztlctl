"""Tests for operation-specific Rich renderers."""

from ztlctl.output.renderers import render_quiet, render_result
from ztlctl.services.result import ServiceError, ServiceResult

# ── Helpers ───────────────────────────────────────────────────────────


def _ok(op: str, **data: object) -> ServiceResult:
    return ServiceResult(ok=True, op=op, data=dict(data))


def _err(op: str, code: str, message: str, **detail: object) -> ServiceResult:
    return ServiceResult(
        ok=False,
        op=op,
        error=ServiceError(code=code, message=message, detail=dict(detail)),
    )


# ── Error rendering ──────────────────────────────────────────────────


class TestErrorRenderer:
    def test_basic_error(self) -> None:
        result = _err("create_note", "VALIDATION", "Title is required")
        output = render_result(result)
        assert "ERROR" in output
        assert "create_note" in output
        assert "Title is required" in output

    def test_verbose_shows_detail(self) -> None:
        result = _err("create_note", "VALIDATION", "Bad", field="title")
        output = render_result(result, verbose=True)
        assert "detail" in output
        assert "field" in output
        assert "title" in output

    def test_no_error_object(self) -> None:
        result = ServiceResult(ok=False, op="test")
        output = render_result(result)
        assert "Unknown error" in output


# ── Mutation renderer ────────────────────────────────────────────────


class TestMutationRenderer:
    def test_create_note(self) -> None:
        result = _ok(
            "create_note",
            id="ztl_abc12345",
            path="notes/ztl_abc12345.md",
            title="My Note",
            type="note",
        )
        output = render_result(result)
        assert "OK" in output
        assert "create_note" in output
        assert "ztl_abc12345" in output
        assert "notes/ztl_abc12345.md" in output
        assert "My Note" in output

    def test_update_shows_fields_changed(self) -> None:
        result = _ok(
            "update",
            id="ztl_abc12345",
            path="notes/ztl_abc12345.md",
            fields_changed=["title", "status"],
            status="linked",
        )
        output = render_result(result)
        assert "fields_changed" in output
        assert "title" in output

    def test_archive(self) -> None:
        result = _ok("archive", id="ztl_abc12345", path="notes/ztl_abc12345.md")
        output = render_result(result)
        assert "OK" in output
        assert "ztl_abc12345" in output

    def test_session_start(self) -> None:
        result = _ok(
            "session_start",
            id="LOG-0001",
            topic="Research",
            path="ops/logs/LOG-0001.jsonl",
            status="open",
        )
        output = render_result(result)
        assert "session_start" in output
        assert "LOG-0001" in output

    def test_rollback(self) -> None:
        result = _ok(
            "rollback",
            backup_file="ztlctl-20260225T120000.db",
            restored_from="ztlctl-20260225T120000.db",
        )
        output = render_result(result)
        assert "rollback" in output
        assert "ztlctl-20260225T120000.db" in output


# ── Batch renderer ───────────────────────────────────────────────────


class TestBatchRenderer:
    def test_batch_success(self) -> None:
        result = _ok(
            "create_batch",
            created=[
                {"id": "ztl_a", "path": "notes/ztl_a.md", "title": "A", "type": "note"},
            ],
            errors=[],
        )
        output = render_result(result)
        assert "create_batch" in output
        assert "1" in output  # created count

    def test_batch_with_errors(self) -> None:
        result = _ok(
            "create_batch",
            created=[],
            errors=[{"index": 0, "error": "bad title"}],
        )
        output = render_result(result)
        assert "error" in output.lower()
        assert "bad title" in output


# ── Query renderers ──────────────────────────────────────────────────


class TestItemTableRenderer:
    def test_search_results(self) -> None:
        result = _ok(
            "search",
            query="test",
            count=1,
            items=[
                {
                    "id": "ztl_a",
                    "title": "Result",
                    "type": "note",
                    "subtype": None,
                    "status": "draft",
                    "path": "notes/ztl_a.md",
                    "created": "2026-01-01",
                    "modified": "2026-01-02",
                    "score": -1.234,
                }
            ],
        )
        output = render_result(result)
        assert "ztl_a" in output
        assert "Result" in output
        assert "1 items" in output

    def test_list_items(self) -> None:
        result = _ok(
            "list_items",
            count=2,
            items=[
                {
                    "id": "ztl_a",
                    "title": "A",
                    "type": "note",
                    "status": "draft",
                    "subtype": None,
                    "path": "a.md",
                    "topic": None,
                    "created": "2026-01-01",
                    "modified": "2026-01-02",
                },
                {
                    "id": "ztl_b",
                    "title": "B",
                    "type": "note",
                    "status": "linked",
                    "subtype": None,
                    "path": "b.md",
                    "topic": None,
                    "created": "2026-01-01",
                    "modified": "2026-01-02",
                },
            ],
        )
        output = render_result(result)
        assert "ztl_a" in output
        assert "ztl_b" in output
        assert "2 items" in output

    def test_verbose_shows_modified(self) -> None:
        result = _ok(
            "list_items",
            count=1,
            items=[
                {
                    "id": "ztl_a",
                    "title": "A",
                    "type": "note",
                    "status": "draft",
                    "subtype": None,
                    "path": "a.md",
                    "topic": None,
                    "created": "2026-01-01",
                    "modified": "2026-02-15",
                }
            ],
        )
        output = render_result(result, verbose=True)
        assert "2026-02-15" in output


class TestSingleItemRenderer:
    def test_get_result(self) -> None:
        result = _ok(
            "get",
            id="ztl_a",
            title="My Note",
            type="note",
            subtype=None,
            status="draft",
            path="notes/ztl_a.md",
            topic="python",
            session="LOG-0001",
            created="2026-01-01",
            modified="2026-01-02",
            tags=["domain/python", "domain/ai"],
            body="This is the note body.",
            links_out=[{"id": "ztl_b", "edge_type": "relates"}],
            links_in=[],
        )
        output = render_result(result)
        assert "ztl_a" in output
        assert "My Note" in output
        assert "domain/python" in output
        assert "note body" in output
        assert "ztl_b" in output


class TestWorkQueueRenderer:
    def test_work_queue(self) -> None:
        result = _ok(
            "work_queue",
            count=1,
            items=[
                {
                    "id": "TASK-0001",
                    "title": "Do thing",
                    "status": "active",
                    "path": "ops/tasks/TASK-0001.md",
                    "priority": "high",
                    "impact": "high",
                    "effort": "low",
                    "score": 10.5,
                    "created": "2026-01-01",
                    "modified": "2026-01-02",
                }
            ],
        )
        output = render_result(result)
        assert "TASK-0001" in output
        assert "Do thing" in output
        assert "high" in output
        assert "10.50" in output
        assert "1 tasks" in output


class TestDecisionSupportRenderer:
    def test_decision_support(self) -> None:
        result = _ok(
            "decision_support",
            topic="databases",
            decisions=[
                {
                    "id": "ztl_d",
                    "title": "Use Postgres",
                    "type": "note",
                    "subtype": "decision",
                    "status": "accepted",
                    "path": "notes/ztl_d.md",
                    "topic": "databases",
                    "created": "2026-01-01",
                    "modified": "2026-01-02",
                },
            ],
            notes=[],
            references=[],
            counts={"decisions": 1, "notes": 0, "references": 0},
        )
        output = render_result(result)
        assert "databases" in output
        assert "1 decisions" in output
        assert "Use Postgres" in output


# ── Graph renderers ──────────────────────────────────────────────────


class TestScoredTableRenderer:
    def test_related(self) -> None:
        result = _ok(
            "related",
            source_id="ztl_a",
            count=1,
            items=[{"id": "ztl_b", "title": "Related", "type": "note", "score": 0.75, "depth": 1}],
        )
        output = render_result(result)
        assert "ztl_b" in output
        assert "Related" in output
        assert "0.7500" in output

    def test_rank(self) -> None:
        result = _ok(
            "rank",
            count=1,
            items=[{"id": "ztl_a", "title": "Important", "type": "note", "score": 0.042}],
        )
        output = render_result(result)
        assert "Important" in output
        assert "0.0420" in output

    def test_gaps(self) -> None:
        result = _ok(
            "gaps",
            count=1,
            items=[{"id": "ztl_a", "title": "Isolated", "type": "note", "constraint": 0.95}],
        )
        output = render_result(result)
        assert "0.9500" in output

    def test_bridges(self) -> None:
        result = _ok(
            "bridges",
            count=1,
            items=[{"id": "ztl_a", "title": "Bridge", "type": "note", "centrality": 0.33}],
        )
        output = render_result(result)
        assert "0.3300" in output


class TestThemesRenderer:
    def test_themes(self) -> None:
        result = _ok(
            "themes",
            count=1,
            communities=[
                {
                    "community_id": 0,
                    "size": 2,
                    "members": [
                        {"id": "ztl_a", "title": "Note A", "type": "note"},
                        {"id": "ztl_b", "title": "Note B", "type": "note"},
                    ],
                }
            ],
        )
        output = render_result(result)
        assert "1 communities" in output
        assert "Community 0" in output
        assert "ztl_a" in output
        assert "ztl_b" in output


class TestPathRenderer:
    def test_path(self) -> None:
        result = _ok(
            "path",
            source_id="ztl_a",
            target_id="ztl_c",
            length=2,
            steps=[
                {"id": "ztl_a", "title": "Start", "type": "note"},
                {"id": "ztl_b", "title": "Middle", "type": "note"},
                {"id": "ztl_c", "title": "End", "type": "note"},
            ],
        )
        output = render_result(result)
        assert "ztl_a" in output
        assert "ztl_b" in output
        assert "ztl_c" in output

    def test_no_path(self) -> None:
        result = _ok("path", source_id="a", target_id="b", length=0, steps=[])
        output = render_result(result)
        assert "No path found" in output


# ── Check renderers ──────────────────────────────────────────────────


class TestCheckRenderer:
    def test_no_issues(self) -> None:
        result = _ok("check", issues=[], count=0)
        output = render_result(result)
        assert "No issues found" in output

    def test_with_issues(self) -> None:
        result = _ok(
            "check",
            count=2,
            issues=[
                {
                    "category": "db-file",
                    "severity": "error",
                    "node_id": "ztl_a",
                    "message": "Missing file",
                    "fix_action": "remove row",
                },
                {
                    "category": "graph",
                    "severity": "warning",
                    "node_id": None,
                    "message": "Orphan node",
                    "fix_action": None,
                },
            ],
        )
        output = render_result(result)
        assert "db-file" in output
        assert "Missing file" in output
        assert "1 errors" in output
        assert "1 warnings" in output

    def test_verbose_shows_fix_action(self) -> None:
        result = _ok(
            "check",
            count=1,
            issues=[
                {
                    "category": "db-file",
                    "severity": "error",
                    "node_id": "ztl_a",
                    "message": "Missing",
                    "fix_action": "remove row",
                },
            ],
        )
        output = render_result(result, verbose=True)
        assert "remove row" in output


class TestFixRenderer:
    def test_fix(self) -> None:
        result = _ok("fix", count=2, fixes=["removed orphan", "re-synced FTS5"])
        output = render_result(result)
        assert "fix" in output
        assert "2" in output

    def test_verbose_lists_fixes(self) -> None:
        result = _ok("fix", count=1, fixes=["removed orphan"])
        output = render_result(result, verbose=True)
        assert "removed orphan" in output


class TestRebuildRenderer:
    def test_rebuild(self) -> None:
        result = _ok("rebuild", nodes_indexed=10, edges_created=5, tags_found=3)
        output = render_result(result)
        assert "10" in output
        assert "5" in output
        assert "3" in output


# ── Session renderers ────────────────────────────────────────────────


class TestSessionCloseRenderer:
    def test_session_close(self) -> None:
        result = _ok(
            "session_close",
            session_id="LOG-0001",
            status="closed",
            reweave_count=3,
            orphan_count=1,
            integrity_issues=0,
        )
        output = render_result(result)
        assert "session_close" in output
        assert "LOG-0001" in output
        assert "closed" in output
        assert "3" in output  # reweave_count


# ── Reweave renderers ───────────────────────────────────────────────


class TestReweaveRenderer:
    def test_reweave_connected(self) -> None:
        result = _ok(
            "reweave",
            target_id="ztl_a",
            count=1,
            connected=[{"id": "ztl_b", "title": "Linked"}],
        )
        output = render_result(result)
        assert "ztl_a" in output
        assert "ztl_b" in output

    def test_reweave_dry_run(self) -> None:
        result = _ok(
            "reweave",
            target_id="ztl_a",
            count=1,
            dry_run=True,
            suggestions=[
                {
                    "id": "ztl_b",
                    "title": "Suggestion",
                    "score": 0.85,
                    "signals": {
                        "lexical": 0.9,
                        "tag_overlap": 0.5,
                        "graph_proximity": 0.0,
                        "topic": 1.0,
                    },
                }
            ],
        )
        output = render_result(result)
        assert "DRY RUN" in output
        assert "0.8500" in output

    def test_prune(self) -> None:
        result = _ok(
            "prune",
            target_id="ztl_a",
            count=1,
            pruned=[{"id": "ztl_b", "title": "Removed"}],
        )
        output = render_result(result)
        assert "ztl_b" in output


class TestUndoRenderer:
    def test_undo(self) -> None:
        result = _ok(
            "undo",
            count=1,
            undone=[
                {
                    "log_id": 42,
                    "source_id": "ztl_a",
                    "target_id": "ztl_b",
                    "action": "add",
                    "reversed": "remove",
                }
            ],
        )
        output = render_result(result)
        assert "42" in output
        assert "ztl_a" in output


# ── Generic / fallback ───────────────────────────────────────────────


class TestGenericRenderer:
    def test_unknown_op(self) -> None:
        result = _ok("some_future_op", key="value", nested={"a": 1})
        output = render_result(result)
        assert "OK" in output
        assert "some_future_op" in output
        assert "value" in output


# ── Quiet mode ───────────────────────────────────────────────────────


class TestQuietMode:
    def test_mutation_quiet(self) -> None:
        result = _ok("create_note", id="ztl_a", path="a.md", title="T", type="note")
        output = render_quiet(result)
        assert output == "OK: create_note"

    def test_table_quiet_returns_ids(self) -> None:
        result = _ok(
            "list_items",
            count=2,
            items=[
                {"id": "ztl_a", "title": "A"},
                {"id": "ztl_b", "title": "B"},
            ],
        )
        output = render_quiet(result)
        assert output == "ztl_a\nztl_b"

    def test_error_quiet(self) -> None:
        result = _err("create_note", "VALIDATION", "Bad input")
        output = render_quiet(result)
        assert output == "ERROR: create_note — Bad input"

    def test_themes_quiet_returns_community_ids(self) -> None:
        result = _ok(
            "themes",
            count=2,
            communities=[
                {
                    "community_id": 0,
                    "size": 2,
                    "members": [
                        {"id": "ztl_a"},
                        {"id": "ztl_b"},
                    ],
                },
                {
                    "community_id": 1,
                    "size": 1,
                    "members": [
                        {"id": "ztl_c"},
                    ],
                },
            ],
        )
        output = render_quiet(result)
        assert output == "0\n1"
