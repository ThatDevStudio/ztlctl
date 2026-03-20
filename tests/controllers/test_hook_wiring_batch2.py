"""Spot-check tests for batch-2 controller hook wiring (PLUG-02).

Verifies that _dispatch_pre_action and _dispatch_post_action are called
with the correct action names and kwargs for all 7 batch-2 controllers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from ztlctl.controllers.query import QueryController
from ztlctl.controllers.reweave import ReweaveController
from ztlctl.controllers.session import SessionController
from ztlctl.controllers.update import UpdateController
from ztlctl.controllers.upgrade import UpgradeController
from ztlctl.controllers.vector import VectorController
from ztlctl.controllers.workflow import WorkflowController
from ztlctl.infrastructure.vault import Vault
from ztlctl.services.result import ServiceResult
from ztlctl.services.workflow import WorkflowChoices


def _mock_service_result(op: str) -> ServiceResult:
    """Return a successful ServiceResult for testing."""
    return ServiceResult(ok=True, op=op, data={})


def test_query_controller_search_dispatches_hooks(vault: Vault) -> None:
    """QueryController.search() calls _dispatch_pre_action with correct action name/kwargs."""
    ctrl = QueryController(vault)

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.search("test query")

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    assert action_name == "search"
    assert kwargs["query"] == "test query"
    assert kwargs["content_type"] is None
    assert kwargs["tag"] is None
    assert kwargs["space"] is None
    assert kwargs["rank_by"] == "relevance"
    assert kwargs["limit"] == 20


def test_reweave_controller_reweave_dispatches_hooks(vault: Vault) -> None:
    """ReweaveController.reweave() calls _dispatch_pre_action with correct action name."""
    ctrl = ReweaveController(vault)

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.reweave(content_id="ZTL-001")

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    assert action_name == "reweave"
    assert kwargs["content_id"] == "ZTL-001"
    assert kwargs["dry_run"] is False
    assert kwargs["min_score_override"] is None


def test_session_controller_start_dispatches_hooks(vault: Vault) -> None:
    """SessionController.start() calls _dispatch_pre_action with correct action name/kwargs."""
    ctrl = SessionController(vault)

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.start("my topic")

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    assert action_name == "start"
    assert kwargs["topic"] == "my topic"


def test_update_controller_update_dispatches_hooks(vault: Vault) -> None:
    """UpdateController.update() calls _dispatch_pre_action with correct action name/kwargs."""
    ctrl = UpdateController(vault)

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.update("ZTL-001", changes={"title": "new"})

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    assert action_name == "update"
    assert kwargs["content_id"] == "ZTL-001"
    assert kwargs["changes"] == {"title": "new"}


def test_upgrade_controller_apply_dispatches_hooks(vault: Vault) -> None:
    """UpgradeController.apply() calls _dispatch_pre_action with correct action name/kwargs."""
    ctrl = UpgradeController(vault)

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.apply()

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    assert action_name == "apply"
    assert kwargs == {}


def test_vector_controller_status_uses_vector_status_action(vault: Vault) -> None:
    """VectorController.status() calls _dispatch_pre_action with 'vector_status', NOT 'status'."""
    ctrl = VectorController(vault)

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.status()

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    # CRITICAL: must be "vector_status" not "status"
    assert action_name == "vector_status"
    assert action_name != "status"
    assert kwargs == {}


def test_workflow_controller_init_dispatches_hooks(vault: Vault) -> None:
    """WorkflowController.init_workflow() calls _dispatch_pre_action with correct kwargs."""
    ctrl = WorkflowController(vault)

    choices = WorkflowChoices(
        source_control="git",
        profile="default",
        workflow="claude-driven",
        skill_set="engineering",
    )

    captured_pre: list[tuple[str, dict[str, Any]]] = []

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        captured_pre.append((action_name, dict(kwargs)))
        return original_pre(action_name, kwargs)

    # Mock WorkflowService.init_workflow to avoid actual copier execution
    mock_result = _mock_service_result("init_workflow")
    with (
        patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre),
        patch(
            "ztlctl.services.workflow.WorkflowService.init_workflow",
            return_value=mock_result,
        ),
    ):
        ctrl.init_workflow(Path("/tmp"), choices)

    assert len(captured_pre) == 1
    action_name, kwargs = captured_pre[0]
    assert action_name == "init_workflow"
    assert kwargs["vault_root"] == Path("/tmp")
    assert kwargs["choices"] is choices
    assert kwargs["force_trust"] is False


def test_workflow_controller_skip_non_service_result_methods(vault: Vault) -> None:
    """read_answers, profile_choices, and default_choices do NOT call _dispatch_pre_action."""
    ctrl = WorkflowController(vault)

    pre_call_count = 0

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        nonlocal pre_call_count
        pre_call_count += 1
        return kwargs, None

    mock_choices = WorkflowChoices(
        source_control="git",
        profile="default",
        workflow="manual",
        skill_set="minimal",
    )

    with (
        patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre),
        patch(
            "ztlctl.services.workflow.WorkflowService.read_answers",
            return_value=mock_choices,
        ),
        patch(
            "ztlctl.services.workflow.WorkflowService.profile_choices",
            return_value=["default"],
        ),
        patch(
            "ztlctl.services.workflow.WorkflowService.default_choices",
            return_value=mock_choices,
        ),
    ):
        ctrl.read_answers(Path("/tmp"))
        ctrl.profile_choices(Path("/tmp"))
        ctrl.default_choices()

    assert pre_call_count == 0, (
        "_dispatch_pre_action should NOT be called for non-ServiceResult methods "
        f"(was called {pre_call_count} times)"
    )


def test_session_controller_log_entry_kwargs_complete(vault: Vault) -> None:
    """SessionController.log_entry() passes all 8 kwargs to _dispatch_pre_action."""
    ctrl = SessionController(vault)

    captured_kwargs: dict[str, Any] = {}

    original_pre = ctrl._dispatch_pre_action

    def spy_pre(action_name: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], Any]:
        if action_name == "log_entry":
            captured_kwargs.update(kwargs)
        return original_pre(action_name, kwargs)

    # Start a session first so log_entry can succeed
    ctrl.start("test session")

    with patch.object(ctrl, "_dispatch_pre_action", side_effect=spy_pre):
        ctrl.log_entry("test message", pin=True, cost=100)

    # Verify all 8 expected keys are present
    expected_keys = {
        "message",
        "pin",
        "cost",
        "detail",
        "entry_type",
        "subtype",
        "references",
        "metadata",
    }
    assert expected_keys == set(captured_kwargs.keys()), (
        f"Expected keys {expected_keys}, got {set(captured_kwargs.keys())}"
    )
    assert captured_kwargs["message"] == "test message"
    assert captured_kwargs["pin"] is True
    assert captured_kwargs["cost"] == 100
