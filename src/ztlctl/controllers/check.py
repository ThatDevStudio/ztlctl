"""CheckController — orchestration wrapper for CheckService."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ztlctl.controllers.base import BaseController

if TYPE_CHECKING:
    from ztlctl.services.result import ServiceResult


class CheckController(BaseController):
    """Thin wrapper over CheckService. All methods return ServiceResult."""

    def check(self, *, min_severity: str = "warning") -> ServiceResult:
        """Report integrity issues without modifying anything."""
        from ztlctl.services.check import CheckService

        kwargs: dict[str, Any] = {"min_severity": min_severity}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CheckService(self._vault).check(min_severity=kw["min_severity"])

        return self._run_action("check", kwargs, _invoke)

    def fix(self, *, level: str = "safe") -> ServiceResult:
        """Automatically repair issues. Level: 'safe' or 'aggressive'."""
        from ztlctl.services.check import CheckService

        kwargs: dict[str, Any] = {"level": level}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CheckService(self._vault).fix(level=kw["level"])

        return self._run_action("fix", kwargs, _invoke)

    def rebuild(self) -> ServiceResult:
        """Full DB rebuild from filesystem (files are truth)."""
        from ztlctl.services.check import CheckService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CheckService(self._vault).rebuild()

        return self._run_action("rebuild", kwargs, _invoke)

    def rollback(self) -> ServiceResult:
        """Restore DB from latest backup."""
        from ztlctl.services.check import CheckService

        kwargs: dict[str, Any] = {}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CheckService(self._vault).rollback()

        return self._run_action("rollback", kwargs, _invoke)

    def check_alignment(self, *, decision: str) -> ServiceResult:
        """Check decision alignment against polaris priorities."""
        from ztlctl.services.check import CheckService

        kwargs: dict[str, Any] = {"decision": decision}

        def _invoke(kw: dict[str, Any]) -> ServiceResult:
            return CheckService(self._vault).check_alignment(**kw)

        return self._run_action("check_alignment", kwargs, _invoke)

    def event_purge(self, *, older_than_days: int | None = None) -> ServiceResult:
        """Purge dead-letter events from the WAL.

        Deletes dead-letter rows older than older_than_days (defaults to
        config dead_letter_retention_days). Returns count purged.
        """
        from ztlctl.services.result import ServiceError, ServiceResult

        bus = self._vault.event_bus
        if bus is None:
            return ServiceResult(
                ok=False,
                op="event_purge",
                error=ServiceError(
                    code="EVENT_BUS_NOT_INITIALIZED",
                    message="Event bus not initialized",
                ),
            )

        days = (
            older_than_days
            if older_than_days is not None
            else self._vault.settings.eventbus.dead_letter_retention_days
        )
        count = bus.purge_dead_letters(older_than_days=days)

        return ServiceResult(
            ok=True,
            op="event_purge",
            data={"purged_count": count, "older_than_days": days},
        )
