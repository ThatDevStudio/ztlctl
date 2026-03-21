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
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {}

        kwargs, rejection = self._dispatch_pre_action("discover_categories", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="discover_categories",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

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

        result = ServiceResult(
            ok=True,
            op="discover_categories",
            data={"categories": categories, "count": len(categories)},
        )
        return result

    def activate_category(self, *, category: str, **_kwargs: Any) -> Any:
        """Activate a tool category; return its tool names on success."""
        from ztlctl.actions.registry import get_action_registry
        from ztlctl.mcp.generator import activate_category as _activate
        from ztlctl.services.result import ServiceError, ServiceResult

        kwargs: dict[str, Any] = {"category": category}

        kwargs, rejection = self._dispatch_pre_action("activate_category", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="activate_category",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        success = _activate(kwargs["category"])
        if not success:
            return ServiceResult(
                ok=False,
                op="activate_category",
                error=ServiceError(
                    code="VALIDATION_FAILED",
                    message=(
                        f"Category {kwargs['category']!r} does not exist in the action registry."
                    ),
                    recovery="Call discover_categories to see all valid category names.",
                ),
            )

        registry = get_action_registry()
        tool_names = sorted(
            a.name for a in registry.list_actions() if a.category == kwargs["category"]
        )
        result = ServiceResult(
            ok=True,
            op="activate_category",
            data={
                "category": kwargs["category"],
                "tools": tool_names,
                "tool_count": len(tool_names),
            },
        )
        return result

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

        kwargs, rejection = self._dispatch_pre_action("deactivate_category", kwargs)
        if rejection is not None:
            return ServiceResult(
                ok=False,
                op="deactivate_category",
                error=ServiceError(
                    code="ACTION_REJECTED",
                    message=rejection.reason,
                    detail=rejection.detail,
                    recovery=f"Action rejected by plugin: {rejection.reason}",
                ),
            )

        # Check upfront so we can return a more specific error
        if kwargs["category"] in _DEFAULT_ACTIVE_CATEGORIES:
            return ServiceResult(
                ok=False,
                op="deactivate_category",
                error=ServiceError(
                    code="VALIDATION_FAILED",
                    message=(
                        f"Category {kwargs['category']!r} is a core category "
                        "and cannot be deactivated."
                    ),
                    recovery=(
                        "Only non-core categories (export, vector, workflow, etc.) "
                        "can be deactivated."
                    ),
                ),
            )

        active = get_active_categories()
        if kwargs["category"] not in active:
            return ServiceResult(
                ok=False,
                op="deactivate_category",
                error=ServiceError(
                    code="NOT_FOUND",
                    message=f"Category {kwargs['category']!r} is not currently active.",
                    recovery="Call discover_categories to see currently active categories.",
                ),
            )

        success = _deactivate(kwargs["category"])
        if not success:
            # Shouldn't reach here given the guards above, but be defensive
            return ServiceResult(
                ok=False,
                op="deactivate_category",
                error=ServiceError(
                    code="VALIDATION_FAILED",
                    message=f"Failed to deactivate category {kwargs['category']!r}.",
                ),
            )

        result = ServiceResult(
            ok=True,
            op="deactivate_category",
            data={"category": kwargs["category"], "deactivated": True},
        )
        return result
