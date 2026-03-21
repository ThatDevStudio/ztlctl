"""Structural regression test: _dispatch_post_action must not exist in controllers.

Prevents accidental re-introduction of controller-side post_action dispatch.
Service-layer emission via _dispatch_post_action_event() is the single producer.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _get_controller_files() -> list[Path]:
    """Return all Python source files in the controllers package."""
    controllers_dir = Path(__file__).parent.parent.parent / "src" / "ztlctl" / "controllers"
    return sorted(controllers_dir.glob("*.py"))


def _find_dispatch_post_action_calls(tree: ast.AST) -> list[ast.Call]:
    """Walk an AST looking for calls to self._dispatch_post_action(...)."""
    calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            # Match self._dispatch_post_action(...)
            if (
                isinstance(func, ast.Attribute)
                and func.attr == "_dispatch_post_action"
                and isinstance(func.value, ast.Name)
                and func.value.id == "self"
            ):
                calls.append(node)
    return calls


def _find_method_definitions(tree: ast.AST, method_name: str) -> list[ast.FunctionDef]:
    """Walk an AST looking for method definitions matching the given name."""
    defs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            defs.append(node)
    return defs


class TestPostActionRemoval:
    """Structural regression: _dispatch_post_action must not exist in controllers."""

    def test_no_controller_file_calls_dispatch_post_action(self) -> None:
        """No controller file should call self._dispatch_post_action(...)."""
        violations: list[str] = []

        for filepath in _get_controller_files():
            source = filepath.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(filepath))
            calls = _find_dispatch_post_action_calls(tree)
            if calls:
                for call in calls:
                    violations.append(
                        f"{filepath.name}: line {call.lineno} calls self._dispatch_post_action"
                    )

        assert not violations, (
            "Controller files must not call _dispatch_post_action. "
            "Service-side emission via _dispatch_post_action_event() is the single producer.\n"
            + "\n".join(violations)
        )

    def test_base_controller_does_not_define_dispatch_post_action(self) -> None:
        """BaseController must not define _dispatch_post_action as a method."""
        base_path = (
            Path(__file__).parent.parent.parent / "src" / "ztlctl" / "controllers" / "base.py"
        )
        source = base_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(base_path))
        defs = _find_method_definitions(tree, "_dispatch_post_action")
        assert not defs, (
            "BaseController must not define _dispatch_post_action. "
            f"Found {len(defs)} definition(s) in {base_path.name}."
        )

    def test_base_controller_still_has_dispatch_pre_action(self) -> None:
        """BaseController must still define _dispatch_pre_action (not accidentally removed)."""
        base_path = (
            Path(__file__).parent.parent.parent / "src" / "ztlctl" / "controllers" / "base.py"
        )
        source = base_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(base_path))
        defs = _find_method_definitions(tree, "_dispatch_pre_action")
        assert len(defs) == 1, (
            "BaseController must define exactly one _dispatch_pre_action. "
            f"Found {len(defs)} definition(s)."
        )

    def test_base_controller_still_has_dispatch_event(self) -> None:
        """BaseController must still define _dispatch_event (not accidentally removed)."""
        base_path = (
            Path(__file__).parent.parent.parent / "src" / "ztlctl" / "controllers" / "base.py"
        )
        source = base_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(base_path))
        defs = _find_method_definitions(tree, "_dispatch_event")
        assert len(defs) == 1, (
            "BaseController must define exactly one _dispatch_event. "
            f"Found {len(defs)} definition(s)."
        )
