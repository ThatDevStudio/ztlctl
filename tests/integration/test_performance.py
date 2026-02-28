"""End-to-end performance regression tests.

Uses the telemetry system to capture individual function timings and
wall-clock time for overall workflows. Fails if performance drops
below defined thresholds.

Thresholds are generous (10-50x typical) to avoid CI flakes while
still catching serious regressions (e.g., O(n²) algorithms, missing
indexes, accidental full-table scans).
"""

from __future__ import annotations

import time
from collections.abc import Generator
from typing import Any

import pytest

from ztlctl.infrastructure.vault import Vault
from ztlctl.services.telemetry import _current_span, disable_telemetry, enable_telemetry

# ── Thresholds (milliseconds) ────────────────────────────────────────

# Individual service method calls
SINGLE_OP_MS = 200

# Sub-stage spans inside pipeline methods
SUB_STAGE_MS = 200

# Batch operations (creating 10+ items)
BATCH_MS = 2000

# Full multi-step workflows
WORKFLOW_MS = 5000


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _telemetry_enabled() -> Generator[None]:
    """Enable telemetry for all performance tests, clean up after."""
    enable_telemetry()
    yield
    disable_telemetry()
    _current_span.set(None)


def _get_telemetry(result: Any) -> dict[str, Any]:
    """Extract telemetry dict from a ServiceResult, failing if absent."""
    assert result.ok, f"Operation failed: {result.error}"
    assert result.meta is not None, "No meta — telemetry not captured"
    assert "telemetry" in result.meta, "No telemetry key in meta"
    return result.meta["telemetry"]


def _get_child_durations(telemetry: dict[str, Any]) -> dict[str, float]:
    """Extract {name: duration_ms} for all child spans."""
    return {child["name"]: child["duration_ms"] for child in telemetry.get("children", [])}


# ── Test 1: Content Creation Workflow ────────────────────────────────


class TestContentCreationPerformance:
    """Simulates a user creating a batch of diverse content.

    Workflow: Create 5 notes + 3 references + 2 tasks with tags and links.
    Verifies individual create times and total batch throughput.
    """

    def test_batch_content_creation(self, vault: Vault) -> None:
        from ztlctl.services.create import CreateService

        svc = CreateService(vault)
        durations: list[float] = []
        start = time.perf_counter()

        # Create 5 notes with varying tags
        for i in range(5):
            result = svc.create_note(
                f"Research Note {i}",
                tags=[f"topic-{i}", "research"],
            )
            tel = _get_telemetry(result)
            durations.append(tel["duration_ms"])

            # Verify sub-stages are fast
            children = _get_child_durations(tel)
            for stage_name, stage_ms in children.items():
                assert stage_ms < SUB_STAGE_MS, (
                    f"create_note sub-stage '{stage_name}' took {stage_ms:.1f}ms "
                    f"(threshold: {SUB_STAGE_MS}ms)"
                )

        # Create 3 references
        for i in range(3):
            result = svc.create_reference(
                f"Source Paper {i}",
                tags=["reference", "paper"],
            )
            tel = _get_telemetry(result)
            durations.append(tel["duration_ms"])

        # Create 2 tasks
        for i in range(2):
            result = svc.create_task(
                f"Follow-up Task {i}",
                tags=["todo"],
            )
            tel = _get_telemetry(result)
            durations.append(tel["duration_ms"])

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert individual operations
        for i, dur in enumerate(durations):
            assert dur < SINGLE_OP_MS, (
                f"Content creation #{i} took {dur:.1f}ms (threshold: {SINGLE_OP_MS}ms)"
            )

        # Assert batch total
        assert elapsed_ms < BATCH_MS, (
            f"Batch creation of 10 items took {elapsed_ms:.1f}ms (threshold: {BATCH_MS}ms)"
        )


# ── Test 2: Search & Analysis Workflow ───────────────────────────────


class TestSearchAnalysisPerformance:
    """Simulates a user querying and analyzing their knowledge base.

    Workflow: Create content → search → get → list → work_queue →
    decision_support → graph themes.
    """

    def test_query_and_graph_workflow(self, vault: Vault) -> None:
        from ztlctl.services.create import CreateService
        from ztlctl.services.graph import GraphService
        from ztlctl.services.query import QueryService

        # Setup: create content to query against
        cs = CreateService(vault)
        for i in range(5):
            cs.create_note(
                f"Architecture Decision {i}",
                tags=["architecture", f"sprint-{i}"],
            )
        cs.create_task("Review architecture", tags=["review"])

        start = time.perf_counter()
        timings: dict[str, float] = {}

        # Search
        qs = QueryService(vault)
        result = qs.search("Architecture Decision")
        timings["search"] = _get_telemetry(result)["duration_ms"]

        # Get single item
        assert result.data["items"], "Search returned no results"
        first_id = result.data["items"][0]["id"]
        result = qs.get(first_id)
        timings["get"] = _get_telemetry(result)["duration_ms"]

        # List all notes
        result = qs.list_items(content_type="note")
        timings["list_items"] = _get_telemetry(result)["duration_ms"]

        # Work queue
        result = qs.work_queue()
        timings["work_queue"] = _get_telemetry(result)["duration_ms"]

        # Decision support
        result = qs.decision_support()
        timings["decision_support"] = _get_telemetry(result)["duration_ms"]

        # Graph analysis
        gs = GraphService(vault)
        result = gs.themes()
        tel = _get_telemetry(result)
        timings["themes"] = tel["duration_ms"]

        # Check themes sub-stages
        children = _get_child_durations(tel)
        for stage_name, stage_ms in children.items():
            assert stage_ms < SUB_STAGE_MS, (
                f"themes sub-stage '{stage_name}' took {stage_ms:.1f}ms "
                f"(threshold: {SUB_STAGE_MS}ms)"
            )

        result = gs.related(first_id)
        timings["related"] = _get_telemetry(result)["duration_ms"]

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert individual operations
        for op_name, dur in timings.items():
            assert dur < SINGLE_OP_MS, f"{op_name} took {dur:.1f}ms (threshold: {SINGLE_OP_MS}ms)"

        # Assert workflow total
        assert elapsed_ms < WORKFLOW_MS, (
            f"Search & analysis workflow took {elapsed_ms:.1f}ms (threshold: {WORKFLOW_MS}ms)"
        )


# ── Test 3: Session Lifecycle Workflow ───────────────────────────────


class TestSessionLifecyclePerformance:
    """Simulates a full user session: start → work → close.

    Session close triggers the enrichment pipeline (reweave, orphan sweep,
    integrity check, graph materialization). This test verifies each
    enrichment sub-stage stays within bounds.
    """

    def test_session_start_work_close(self, vault: Vault) -> None:
        from ztlctl.services.create import CreateService
        from ztlctl.services.session import SessionService

        ss = SessionService(vault)
        cs = CreateService(vault)
        start = time.perf_counter()
        timings: dict[str, float] = {}

        # Start session
        result = ss.start(topic="Performance testing session")
        timings["session_start"] = _get_telemetry(result)["duration_ms"]

        # Work: create notes during session
        for i in range(3):
            result = cs.create_note(
                f"Session Note {i}",
                tags=["session-work"],
            )
            timings[f"create_note_{i}"] = _get_telemetry(result)["duration_ms"]

        # Log entry in session
        result = ss.log_entry("Completed initial research phase.")
        timings["log_entry"] = _get_telemetry(result)["duration_ms"]

        # Close session — triggers enrichment pipeline
        result = ss.close(summary="Completed performance testing session.")
        close_tel = _get_telemetry(result)
        timings["session_close"] = close_tel["duration_ms"]

        # Verify enrichment sub-stages
        close_children = _get_child_durations(close_tel)
        enrichment_stages = [
            "cross_session_reweave",
            "orphan_sweep",
            "integrity_check",
            "materialize",
        ]
        assert close_children, "Session close produced no sub-stage spans"
        for stage in enrichment_stages:
            if stage in close_children:
                assert close_children[stage] < SUB_STAGE_MS, (
                    f"Session close sub-stage '{stage}' took "
                    f"{close_children[stage]:.1f}ms (threshold: {SUB_STAGE_MS}ms)"
                )

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert individual operations
        for op_name, dur in timings.items():
            assert dur < SINGLE_OP_MS, f"{op_name} took {dur:.1f}ms (threshold: {SINGLE_OP_MS}ms)"

        # Assert workflow total
        assert elapsed_ms < WORKFLOW_MS, (
            f"Session lifecycle workflow took {elapsed_ms:.1f}ms (threshold: {WORKFLOW_MS}ms)"
        )


# ── Test 4: Vault Maintenance Workflow ───────────────────────────────


class TestVaultMaintenancePerformance:
    """Simulates vault maintenance: check → update → reweave.

    Verifies integrity checking, content updates, and reweave scoring
    all complete within bounds with their sub-stage breakdowns.
    """

    def test_check_update_reweave(self, vault: Vault) -> None:
        from ztlctl.services.check import CheckService
        from ztlctl.services.create import CreateService
        from ztlctl.services.reweave import ReweaveService
        from ztlctl.services.update import UpdateService

        # Setup: create content with overlapping topics for reweave
        cs = CreateService(vault)
        ids: list[str] = []
        for i in range(5):
            result = cs.create_note(
                f"Linked Topic {i}",
                tags=["linked", f"topic-{i}"],
            )
            ids.append(result.data["id"])

        start = time.perf_counter()
        timings: dict[str, float] = {}

        # Check integrity
        result = CheckService(vault).check()
        check_tel = _get_telemetry(result)
        timings["check"] = check_tel["duration_ms"]

        # Verify check sub-stages
        check_children = _get_child_durations(check_tel)
        check_categories = [
            "db_file_consistency",
            "schema_integrity",
            "graph_health",
            "structural_validation",
        ]
        assert check_children, "Check produced no sub-stage spans"
        for cat in check_categories:
            if cat in check_children:
                assert check_children[cat] < SUB_STAGE_MS, (
                    f"Check category '{cat}' took {check_children[cat]:.1f}ms "
                    f"(threshold: {SUB_STAGE_MS}ms)"
                )

        # Update a note
        result = UpdateService(vault).update(
            ids[0],
            changes={"body": "Updated content with new analysis and findings."},
        )
        update_tel = _get_telemetry(result)
        timings["update"] = update_tel["duration_ms"]

        # Verify update sub-stages
        update_children = _get_child_durations(update_tel)
        for stage_name, stage_ms in update_children.items():
            assert stage_ms < SUB_STAGE_MS, (
                f"Update sub-stage '{stage_name}' took {stage_ms:.1f}ms "
                f"(threshold: {SUB_STAGE_MS}ms)"
            )

        # Reweave to discover connections
        result = ReweaveService(vault).reweave(content_id=ids[0])
        reweave_tel = _get_telemetry(result)
        timings["reweave"] = reweave_tel["duration_ms"]

        # Verify reweave sub-stages
        reweave_children = _get_child_durations(reweave_tel)
        for stage_name, stage_ms in reweave_children.items():
            assert stage_ms < SUB_STAGE_MS, (
                f"Reweave sub-stage '{stage_name}' took {stage_ms:.1f}ms "
                f"(threshold: {SUB_STAGE_MS}ms)"
            )

        elapsed_ms = (time.perf_counter() - start) * 1000

        # Assert individual operations
        for op_name, dur in timings.items():
            assert dur < SINGLE_OP_MS, f"{op_name} took {dur:.1f}ms (threshold: {SINGLE_OP_MS}ms)"

        # Assert workflow total
        assert elapsed_ms < WORKFLOW_MS, (
            f"Vault maintenance workflow took {elapsed_ms:.1f}ms (threshold: {WORKFLOW_MS}ms)"
        )
