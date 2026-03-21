"""DiscoveryController — category discovery and activation for progressive tool disclosure.

Provides handlers for discover_categories, activate_category, and
deactivate_category ActionDefinitions (AGNT-04).  These handlers expose
category-scoped metadata about the ActionRegistry and let agents manage
the active tool surface at runtime.
"""

from __future__ import annotations

from typing import Any

from ztlctl.controllers.base import BaseController


class DiscoveryController(BaseController):
    """Controller for category-level tool discovery and activation."""

    def discover_categories(self, **_kwargs: Any) -> Any:
        """Return all categories with active/core/tool metadata."""
        from ztlctl.actions.registry import get_action_registry
        from ztlctl.mcp.generator import (
            _DEFAULT_ACTIVE_CATEGORIES,
            get_active_categories,
        )
        from ztlctl.services.result import ServiceResult

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            registry = get_action_registry()
            active = get_active_categories()

            # Group tool names by category
            tools_by_cat: dict[str, list[str]] = {}
            for action in registry.list_actions():
                tools_by_cat.setdefault(action.category, []).append(action.name)

            categories = [
                {
                    "category": cat,
                    "active": cat in active,
                    "core": cat in _DEFAULT_ACTIVE_CATEGORIES,
                    "tools": sorted(tool_names),
                    "tool_count": len(tool_names),
                }
                for cat, tool_names in sorted(tools_by_cat.items())
            ]

            return ServiceResult(
                ok=True,
                op="discover_categories",
                data={"categories": categories, "count": len(categories)},
            )

        return self._run_action("discover_categories", kwargs, _invoke)

    def activate_category(self, *, category: str, **_kwargs: Any) -> Any:
        """Activate a tool category; return its tool names on success."""
        from ztlctl.actions.registry import get_action_registry
        from ztlctl.mcp.generator import activate_category as _activate
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"category": category}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            success = _activate(kw["category"])
            if not success:
                return ServiceResult(
                    ok=False,
                    op="activate_category",
                    error=ServiceError(
                        code="VALIDATION_FAILED",
                        message=(
                            f"Category {kw['category']!r} does not exist in the action registry."
                        ),
                        recovery="Call discover_categories to see all valid category names.",
                    ),
                )

            registry = get_action_registry()
            tool_names = sorted(
                a.name for a in registry.list_actions() if a.category == kw["category"]
            )
            return ServiceResult(
                ok=True,
                op="activate_category",
                data={
                    "category": kw["category"],
                    "tools": tool_names,
                    "tool_count": len(tool_names),
                },
            )

        return self._run_action("activate_category", kwargs, _invoke)

    def deactivate_category(self, *, category: str, **_kwargs: Any) -> Any:
        """Deactivate a non-core category; return confirmation on success."""
        from ztlctl.mcp.generator import (
            _DEFAULT_ACTIVE_CATEGORIES,
            get_active_categories,
        )
        from ztlctl.mcp.generator import (
            deactivate_category as _deactivate,
        )
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"category": category}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            # Check upfront so we can return a more specific error
            if kw["category"] in _DEFAULT_ACTIVE_CATEGORIES:
                return ServiceResult(
                    ok=False,
                    op="deactivate_category",
                    error=ServiceError(
                        code="VALIDATION_FAILED",
                        message=(
                            f"Category {kw['category']!r} is a core category "
                            "and cannot be deactivated."
                        ),
                        recovery=(
                            "Only non-core categories (export, vector, workflow, etc.) "
                            "can be deactivated."
                        ),
                    ),
                )

            active = get_active_categories()
            if kw["category"] not in active:
                return ServiceResult(
                    ok=False,
                    op="deactivate_category",
                    error=ServiceError(
                        code="NOT_FOUND",
                        message=f"Category {kw['category']!r} is not currently active.",
                        recovery="Call discover_categories to see currently active categories.",
                    ),
                )

            success = _deactivate(kw["category"])
            if not success:
                # Shouldn't reach here given the guards above, but be defensive
                return ServiceResult(
                    ok=False,
                    op="deactivate_category",
                    error=ServiceError(
                        code="VALIDATION_FAILED",
                        message=f"Failed to deactivate category {kw['category']!r}.",
                    ),
                )

            return ServiceResult(
                ok=True,
                op="deactivate_category",
                data={"category": kw["category"], "deactivated": True},
            )

        return self._run_action("deactivate_category", kwargs, _invoke)
