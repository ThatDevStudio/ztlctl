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

from sqlalchemy import insert, select, update

from ztlctl.infrastructure.database.schema import event_wal
from ztlctl.services._helpers import now_iso

if TYPE_CHECKING:
    from sqlalchemy.engine import Engine

    from ztlctl.plugins.manager import PluginManager

logger = logging.getLogger(__name__)


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
        max_retries: int = 3,
        max_workers: int = 2,
    ) -> None:
        self._engine = engine
        self._pm = plugin_manager
        self._sync = sync
        self._max_retries = max_retries
        self._executor: ThreadPoolExecutor | None = (
            None if sync else ThreadPoolExecutor(max_workers=max_workers)
        )
        self._futures: list[Future[None]] = []

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
            self._futures.append(future)

        return event_id

    def drain(self) -> list[dict[str, Any]]:
        """Retry pending/failed events synchronously. Sync barrier at session close.

        Returns a summary list of ``{id, hook_name, status}`` for each retried event.
        """
        # Wait for any in-flight async tasks first.
        self._wait_futures()

        results: list[dict[str, Any]] = []

        with self._engine.connect() as conn:
            rows = conn.execute(
                select(event_wal.c.id, event_wal.c.hook_name, event_wal.c.payload)
                .where(event_wal.c.status.in_(["pending", "failed"]))
                .order_by(event_wal.c.id)
            ).fetchall()

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

    def shutdown(self) -> None:
        """Shutdown ThreadPoolExecutor, waiting for pending tasks."""
        self._wait_futures()
        if self._executor is not None:
            self._executor.shutdown(wait=True)
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
        """Attempt to dispatch a hook. Update WAL status on success/failure."""
        hook_fn = getattr(self._pm.hook, hook_name, None)
        if hook_fn is None:
            self._mark_completed(event_id)
            return

        try:
            hook_fn(**payload)
        except Exception as exc:
            logger.debug("Hook %s failed: %s", hook_name, exc)
            self._mark_failed(event_id, str(exc))
        else:
            self._mark_completed(event_id)

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

    def _wait_futures(self) -> None:
        """Wait for all in-flight async futures to complete."""
        for future in self._futures:
            try:
                future.result(timeout=30)
            except Exception:
                pass  # Errors already handled in _execute_hook
        self._futures.clear()
