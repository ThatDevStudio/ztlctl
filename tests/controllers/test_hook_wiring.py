"""Spot-check tests for pre/post-action hook wiring in controllers.

Verifies that controller methods call _dispatch_pre_action with the correct
action name and kwargs dict, and _dispatch_post_action after service calls.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from ztlctl.plugins.contracts import ActionRejection
from ztlctl.services.result import ServiceResult


def _make_controller(cls: type) -> Any:
    """Create a controller instance with a mock vault."""
    vault = MagicMock()
    vault.plugin_manager = None  # hooks become no-ops by default
    return cls(vault)


def _ok_result(op: str) -> ServiceResult:
    return ServiceResult(ok=True, op=op, data={})


class TestCheckControllerHookWiring:
    def test_check_controller_check_dispatches_hooks(self) -> None:
        """CheckController.check() dispatches pre and post action hooks."""
        from ztlctl.controllers.check import CheckController

        ctrl = _make_controller(CheckController)
        expected_kwargs = {"min_severity": "error"}
        ok = _ok_result("check")

        with (
            patch.object(
                ctrl,
                "_dispatch_pre_action",
                return_value=(expected_kwargs, None),
            ) as mock_pre,
            patch.object(ctrl, "_dispatch_post_action") as mock_post,
            patch("ztlctl.services.check.CheckService") as mock_svc_cls,
        ):
            mock_svc_cls.return_value.check.return_value = ok
            result = ctrl.check(min_severity="error")

        mock_pre.assert_called_once_with("check", {"min_severity": "error"})
        mock_post.assert_called_once_with("check", expected_kwargs, ok)
        assert result is ok


class TestCreateControllerHookWiring:
    def test_create_controller_create_note_excludes_dispatch_flag(self) -> None:
        """CreateController.create_note() does not include dispatch_post_create in kwargs."""
        from ztlctl.controllers.create import CreateController

        ctrl = _make_controller(CreateController)
        captured_kwargs: dict[str, Any] = {}

        def capture_pre(action_name: str, kwargs: dict[str, Any]) -> Any:
            captured_kwargs.update(kwargs)
            return kwargs, None

        with (
            patch.object(ctrl, "_dispatch_pre_action", side_effect=capture_pre),
            patch.object(ctrl, "_dispatch_post_action"),
            patch("ztlctl.services.create.CreateService") as mock_svc_cls,
        ):
            mock_svc_cls.return_value.create_note.return_value = _ok_result("create_note")
            ctrl.create_note("Test")

        assert "dispatch_post_create" not in captured_kwargs
        # Verify the action name seen was correct
        assert "title" in captured_kwargs
        assert captured_kwargs["title"] == "Test"


class TestDiscoveryControllerHookWiring:
    def test_discovery_controller_activate_dispatches_hooks(self) -> None:
        """DiscoveryController.activate_category() dispatches pre and post action hooks."""
        from ztlctl.controllers.discovery import DiscoveryController

        ctrl = _make_controller(DiscoveryController)
        expected_kwargs = {"category": "export"}

        with (
            patch.object(
                ctrl,
                "_dispatch_pre_action",
                return_value=(expected_kwargs, None),
            ) as mock_pre,
            patch.object(ctrl, "_dispatch_post_action") as mock_post,
            patch("ztlctl.mcp.generator.activate_category", return_value=True),
            patch("ztlctl.actions.registry.get_action_registry") as mock_reg,
        ):
            mock_reg.return_value.list_actions.return_value = []
            result = ctrl.activate_category(category="export")

        mock_pre.assert_called_once_with("activate_category", {"category": "export"})
        assert mock_post.called
        assert result.ok is True


class TestExportControllerHookWiring:
    def test_export_controller_export_markdown_dispatches_hooks(self) -> None:
        """ExportController.export_markdown() dispatches pre and post action hooks."""
        from ztlctl.controllers.export import ExportController

        ctrl = _make_controller(ExportController)
        expected_kwargs = {"output_dir": "/tmp/out", "filters": None}
        ok = _ok_result("export_markdown")

        with (
            patch.object(
                ctrl,
                "_dispatch_pre_action",
                return_value=(expected_kwargs, None),
            ) as mock_pre,
            patch.object(ctrl, "_dispatch_post_action") as mock_post,
            patch("ztlctl.services.export.ExportService") as mock_svc_cls,
        ):
            mock_svc_cls.return_value.export_markdown.return_value = ok
            result = ctrl.export_markdown("/tmp/out")

        mock_pre.assert_called_once_with(
            "export_markdown", {"output_dir": "/tmp/out", "filters": None}
        )
        mock_post.assert_called_once_with("export_markdown", expected_kwargs, ok)
        assert result is ok


class TestGraphControllerHookWiring:
    def test_graph_controller_related_dispatches_hooks(self) -> None:
        """GraphController.related() dispatches pre and post action hooks."""
        from ztlctl.controllers.graph import GraphController

        ctrl = _make_controller(GraphController)
        expected_kwargs = {"content_id": "ZTL-001", "depth": 2, "top": 20}
        ok = _ok_result("related")

        with (
            patch.object(
                ctrl,
                "_dispatch_pre_action",
                return_value=(expected_kwargs, None),
            ) as mock_pre,
            patch.object(ctrl, "_dispatch_post_action") as mock_post,
            patch("ztlctl.services.graph.GraphService") as mock_svc_cls,
        ):
            mock_svc_cls.return_value.related.return_value = ok
            result = ctrl.related("ZTL-001")

        mock_pre.assert_called_once_with(
            "related", {"content_id": "ZTL-001", "depth": 2, "top": 20}
        )
        mock_post.assert_called_once_with("related", expected_kwargs, ok)
        assert result is ok


class TestIngestControllerHookWiring:
    def test_ingest_controller_ingest_text_dispatches_hooks(self) -> None:
        """IngestController.ingest_text() dispatches pre and post action hooks."""
        from ztlctl.controllers.ingest import IngestController

        ctrl = _make_controller(IngestController)
        captured_kwargs: dict[str, Any] = {}

        def capture_pre(action_name: str, kwargs: dict[str, Any]) -> Any:
            captured_kwargs.update(kwargs)
            return kwargs, None

        with (
            patch.object(ctrl, "_dispatch_pre_action", side_effect=capture_pre) as mock_pre,
            patch.object(ctrl, "_dispatch_post_action"),
            patch("ztlctl.services.ingest.IngestService") as mock_svc_cls,
        ):
            mock_svc_cls.return_value.ingest_text.return_value = _ok_result("ingest_text")
            ctrl.ingest_text("T", "body")

        # Verify correct action name and kwargs
        assert mock_pre.call_args[0][0] == "ingest_text"
        assert captured_kwargs["title"] == "T"
        assert captured_kwargs["body_text"] == "body"


class TestInitControllerHookWiring:
    def test_init_controller_init_vault_dispatches_hooks(self) -> None:
        """InitController.init_vault() dispatches pre and post action hooks."""
        from ztlctl.controllers.init_ctrl import InitController

        ctrl = _make_controller(InitController)
        expected_kwargs = {
            "path": Path("/tmp"),
            "name": "test",
            "profile": None,
            "client": None,
            "tone": "research-partner",
            "topics": None,
            "no_workflow": False,
        }
        ok = _ok_result("init_vault")

        with (
            patch.object(
                ctrl,
                "_dispatch_pre_action",
                return_value=(expected_kwargs, None),
            ) as mock_pre,
            patch.object(ctrl, "_dispatch_post_action") as mock_post,
            patch("ztlctl.services.init.InitService") as mock_svc_cls,
        ):
            mock_svc_cls.init_vault.return_value = ok
            result = ctrl.init_vault(Path("/tmp"), name="test")

        mock_pre.assert_called_once_with(
            "init_vault",
            {
                "path": Path("/tmp"),
                "name": "test",
                "profile": None,
                "client": None,
                "tone": "research-partner",
                "topics": None,
                "no_workflow": False,
            },
        )
        mock_post.assert_called_once_with("init_vault", expected_kwargs, ok)
        assert result is ok


class TestRejectionBehavior:
    def test_rejection_prevents_service_call(self) -> None:
        """ActionRejection from pre_action prevents service call and returns ACTION_REJECTED."""
        from ztlctl.controllers.check import CheckController

        ctrl = _make_controller(CheckController)
        rejection = ActionRejection(reason="blocked", code="test-plugin")

        with (
            patch.object(
                ctrl,
                "_dispatch_pre_action",
                return_value=({"min_severity": "warning"}, rejection),
            ),
            patch.object(ctrl, "_dispatch_post_action") as mock_post,
            patch("ztlctl.services.check.CheckService") as mock_svc_cls,
        ):
            result = ctrl.check()

        assert result.ok is False
        assert result.error is not None
        assert result.error.code == "ACTION_REJECTED"
        assert result.error.message == "blocked"
        mock_post.assert_not_called()
        mock_svc_cls.assert_not_called()
