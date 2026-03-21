"""WAL-backed async event dispatch via pluggy + ThreadPoolExecutor.

Events are written to the ``event_wal`` table before dispatch, ensuring
no lifecycle events are lost even if the process exits mid-flight.
``drain()`` retries pending events synchronously at session close.

INVARIANT: Plugin failures are warnings, never errors.
"""

from __future__ import annotations

import json
import logging
from concurrent.futures import Future, ThreadPoolExecutor
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, func, insert, select, update

from ztlctl.infrastructure.database.schema import event_wal
from ztlctl.services._helpers import now_iso

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from ztlctl.config.models import EventBusConfig
    from ztlctl.plugins.manager import PluginManager

logger = logging.getLogger(__name__)

# Maps per-event hook names to post_action action names.
# post_create is handled specially: action_name is refined using content_type
# from the payload (e.g. "create_note", "create_reference", "create_task").
_HOOK_TO_ACTION: dict[str, str] = {
    "post_create": "create",  # Refined at dispatch time using content_type
    "post_update": "update",
    "post_close": "close",
    "post_reweave": "reweave",
    "post_session_start": "session_start",
    "post_session_close": "session_close",
    "post_check": "check",
    "post_init": "init",
}


class EventBus:
    """WAL-backed async event dispatch via pluggy + ThreadPoolExecutor.

    Parameters:
        engine: SQLAlchemy engine with ``event_wal`` table.
        plugin_manager: Loaded PluginManager for hook dispatch.
        sync: Force synchronous dispatch (useful for testing / ``--sync``).
        max_retries: Attempts before an event is marked ``dead_letter``.
        max_workers: ThreadPoolExecutor worker count.
    """

    def __init__(
        self,
        engine: Engine,
        plugin_manager: PluginManager,
        *,
        sync: bool = False,
        config: EventBusConfig | None = None,
        max_retries: int = 3,
        max_workers: int = 2,
    ) -> None:
        self._engine = engine
        self._pm = plugin_manager
        self._sync = sync
        if config is not None:
            self._max_retries = config.max_retries
            self._per_future_timeout = config.per_future_timeout_seconds
            self._shutdown_timeout = config.shutdown_timeout_seconds
            self._dead_letter_retention_days = config.dead_letter_retention_days
        else:
            self._max_retries = max_retries
            self._per_future_timeout = 30.0
            self._shutdown_timeout = 5.0
            self._dead_letter_retention_days = 30
        self._executor: ThreadPoolExecutor | None = (
            None if sync else ThreadPoolExecutor(max_workers=max_workers)
        )
        self._futures: list[tuple[int, Future[None]]] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dispatch(
        self,
        hook_name: str,
        payload: dict[str, Any],
        *,
        session_id: str | None = None,
    ) -> int:
        """Write event to WAL, then dispatch async (or sync).

        Returns the WAL event row id.
        """
        event_id = self._write_wal(hook_name, payload, session_id=session_id)

        if self._sync:
            self._execute_hook(event_id, hook_name, payload)
        else:
            assert self._executor is not None
            future = self._executor.submit(self._execute_hook, event_id, hook_name, payload)
            self._futures.append((event_id, future))

        return event_id

    def drain(
        self,
        *,
        event_ids: list[int] | None = None,
        session_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retry pending/failed events synchronously. Sync barrier at session close.

        Returns a summary list of ``{id, hook_name, status}`` for each retried event.
        """
        # Wait only for the target futures when requested.
        future_ids = set(event_ids or ())
        self._wait_futures(event_ids=future_ids if future_ids else None)

        results: list[dict[str, Any]] = []

        with self._engine.connect() as conn:
            stmt = (
                select(event_wal.c.id, event_wal.c.hook_name, event_wal.c.payload)
                .where(event_wal.c.status.in_(["pending", "failed"]))
                .order_by(event_wal.c.id)
            )
            if future_ids:
                stmt = stmt.where(event_wal.c.id.in_(future_ids))
            if session_id is not None:
                stmt = stmt.where(event_wal.c.session_id == session_id)
            rows = conn.execute(stmt).fetchall()

        for row in rows:
            event_id = row.id
            hook_name = row.hook_name
            payload = json.loads(row.payload)
            self._execute_hook(event_id, hook_name, payload)

            # Read back the final status.
            with self._engine.connect() as conn:
                status = conn.execute(
                    select(event_wal.c.status).where(event_wal.c.id == event_id)
                ).scalar_one()

            results.append({"id": event_id, "hook_name": hook_name, "status": status})

        return results

    def purge_dead_letters(self, *, older_than_days: int | None = None) -> int:
        """Delete dead-letter WAL rows older than N days. Returns count deleted.

        If older_than_days is None, uses self._dead_letter_retention_days from config.
        """
        from datetime import UTC, datetime, timedelta

        retention = (
            older_than_days if older_than_days is not None else self._dead_letter_retention_days
        )
        cutoff = (datetime.now(UTC) - timedelta(days=retention)).isoformat()

        with self._engine.begin() as conn:
            count = conn.execute(
                select(func.count()).select_from(event_wal).where(
                    event_wal.c.status == "dead_letter",
                    event_wal.c.created < cutoff,
                )
            ).scalar_one()

            if count > 0:
                conn.execute(
                    delete(event_wal).where(
                        event_wal.c.status == "dead_letter",
                        event_wal.c.created < cutoff,
                    )
                )

        return count

    def shutdown(
        self,
        *,
        wait: bool = True,
        cancel_futures: bool = False,
        timeout: float | None = None,
    ) -> None:
        """Shutdown ThreadPoolExecutor.

        Args:
            wait: Whether to wait for in-flight tasks to finish.
            cancel_futures: Whether pending (not yet running) futures should be cancelled.
            timeout: Per-future timeout override. When None, uses the configured
                ``per_future_timeout_seconds``.
        """
        if wait:
            self._wait_futures(timeout=timeout)
        else:
            self._futures.clear()

        if self._executor is not None:
            self._executor.shutdown(wait=wait, cancel_futures=cancel_futures)
            self._executor = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write_wal(
        self,
        hook_name: str,
        payload: dict[str, Any],
        *,
        session_id: str | None = None,
    ) -> int:
        """Insert a pending event into the WAL. Returns the row id."""
        with self._engine.begin() as conn:
            result = conn.execute(
                insert(event_wal).values(
                    hook_name=hook_name,
                    payload=json.dumps(payload),
                    status="pending",
                    retries=0,
                    session_id=session_id,
                    created=now_iso(),
                )
            )
            assert result.lastrowid is not None
            return result.lastrowid

    def _execute_hook(
        self,
        event_id: int,
        hook_name: str,
        payload: dict[str, Any],
    ) -> None:
        """Attempt to dispatch a hook. Update WAL status on success/failure.

        Handles two dispatch paths:
        - ``post_action``: payload is an ActionEvent dict; calls post_action
          with action_name/kwargs/result extracted from the ActionEvent.
        - All other hooks: dispatches the per-event hook directly, then fires
          the post_action bridge for backward compatibility with legacy plugins.
        """
        if hook_name == "post_action":
            # Canonical post_action: payload is ActionEvent dict (D-15)
            post_action_fn = getattr(self._pm.hook, "post_action", None)
            if post_action_fn is None:
                self._mark_completed(event_id)
                return
            try:
                post_action_fn(
                    action_name=payload["action_name"],
                    kwargs=payload["payload"],
                    result=payload.get("result"),
                )
            except Exception as exc:
                logger.debug("post_action hook failed: %s", exc)
                self._mark_failed(event_id, str(exc))
            else:
                self._mark_completed(event_id)
            return

        # Per-event hook dispatch (deprecated hooks)
        hook_fn = getattr(self._pm.hook, hook_name, None)
        if hook_fn is None:
            self._mark_completed(event_id)
        else:
            try:
                hook_fn(**payload)
            except Exception as exc:
                logger.debug("Hook %s failed: %s", hook_name, exc)
                self._mark_failed(event_id, str(exc))
            else:
                self._mark_completed(event_id)

        # Bridge: also fire post_action so migrated plugins receive lifecycle events.
        # This runs regardless of whether the per-event hook had subscribers or failed.
        # Kept for backward compatibility until Phase 16 removes deprecated per-event hooks.
        action_name = _HOOK_TO_ACTION.get(hook_name)
        if action_name is not None:
            # Refine create action name using content_type from payload
            if hook_name == "post_create":
                content_type = payload.get("content_type", "note")
                action_name = f"create_{content_type}"
            try:
                post_action_fn = getattr(self._pm.hook, "post_action", None)
                if post_action_fn is not None:
                    post_action_fn(action_name=action_name, kwargs=payload, result=None)
            except Exception:
                logger.debug("post_action bridge failed for %s", hook_name, exc_info=True)

    def _mark_completed(self, event_id: int) -> None:
        """Mark an event as completed in the WAL."""
        with self._engine.begin() as conn:
            conn.execute(
                update(event_wal)
                .where(event_wal.c.id == event_id)
                .values(status="completed", completed=now_iso())
            )

    def _mark_failed(self, event_id: int, error: str) -> None:
        """Increment retries, mark failed or dead_letter."""
        with self._engine.begin() as conn:
            row = conn.execute(
                select(event_wal.c.retries).where(event_wal.c.id == event_id)
            ).scalar_one()

            new_retries = row + 1
            new_status = "dead_letter" if new_retries >= self._max_retries else "failed"

            conn.execute(
                update(event_wal)
                .where(event_wal.c.id == event_id)
                .values(
                    status=new_status,
                    error=error,
                    retries=new_retries,
                    completed=now_iso() if new_status == "dead_letter" else None,
                )
            )

    def _wait_futures(
        self,
        *,
        event_ids: set[int] | None = None,
        timeout: float | None = None,
    ) -> None:
        """Wait for all in-flight async futures to complete.

        Args:
            event_ids: When set, only wait for futures with these event IDs.
            timeout: Per-future timeout override. When None, uses the configured
                ``per_future_timeout_seconds``.
        """
        per_future_timeout = timeout if timeout is not None else self._per_future_timeout
        remaining: list[tuple[int, Future[None]]] = []
        for event_id, future in self._futures:
            if event_ids is not None and event_id not in event_ids:
                remaining.append((event_id, future))
                continue
            try:
                future.result(timeout=per_future_timeout)
            except Exception:
                pass  # Errors already handled in _execute_hook
        self._futures = remaining
