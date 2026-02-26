"""UpgradeService — database migration with Alembic.

Pipeline: BACKUP → MIGRATE → VALIDATE → REPORT
"""

from __future__ import annotations

import logging
from typing import Any

from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from ztlctl.infrastructure.database.migrations import build_config
from ztlctl.services.base import BaseService
from ztlctl.services.result import ServiceError, ServiceResult

logger = logging.getLogger(__name__)


class UpgradeService(BaseService):
    """Handles database schema migrations via Alembic."""

    def _db_url(self) -> str:
        db_path = self._vault.root / ".ztlctl" / "ztlctl.db"
        return f"sqlite:///{db_path}"

    def _tables_exist(self) -> bool:
        """Check if core tables exist (pre-Alembic vault detection)."""
        from sqlalchemy import inspect

        insp = inspect(self._vault.engine)
        return "nodes" in insp.get_table_names()

    def check_pending(self) -> ServiceResult:
        """List pending migrations without applying."""
        op = "upgrade"

        try:
            cfg = build_config(self._db_url())
            script = ScriptDirectory.from_config(cfg)
            head = script.get_current_head()

            with self._vault.engine.connect() as conn:
                ctx = MigrationContext.configure(conn)
                current = ctx.get_current_revision()

            # Collect pending revisions by walking from head down to current
            pending: list[dict[str, Any]] = []
            if current != head and head is not None:
                rev_obj = script.get_revision(head)
                while rev_obj is not None and rev_obj.revision != current:
                    pending.append(
                        {
                            "revision": rev_obj.revision,
                            "description": rev_obj.doc or "",
                        }
                    )
                    down = rev_obj.down_revision
                    if down is None:
                        break
                    rev_obj = script.get_revision(str(down))

            return ServiceResult(
                ok=True,
                op=op,
                data={
                    "pending_count": len(pending),
                    "pending": pending,
                    "current": current,
                    "head": head,
                },
            )
        except Exception as exc:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="CHECK_FAILED",
                    message=f"Failed to check migrations: {exc}",
                ),
            )

    def apply(self) -> ServiceResult:
        """BACKUP → MIGRATE → VALIDATE → REPORT pipeline."""
        op = "upgrade"
        warnings: list[str] = []

        # Check current state first
        check_result = self.check_pending()
        if not check_result.ok:
            return check_result

        pending_count = check_result.data["pending_count"]
        if pending_count == 0:
            return ServiceResult(
                ok=True,
                op=op,
                data={
                    "applied_count": 0,
                    "current": check_result.data["head"],
                    "message": "Database is already up to date",
                },
            )

        # BACKUP
        from ztlctl.services.check import CheckService

        try:
            backup_path = CheckService(self._vault)._backup_db()
        except Exception as exc:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="BACKUP_FAILED",
                    message=f"Backup failed: {exc}",
                ),
            )

        # MIGRATE (or STAMP if tables already exist for pre-Alembic vaults)
        try:
            cfg = build_config(self._db_url())
            current = check_result.data.get("current")
            if current is None and self._tables_exist():
                # Pre-Alembic vault: tables exist but no version tracking.
                # Stamp at head instead of running CREATE TABLE migrations.
                command.stamp(cfg, "head")
            else:
                command.upgrade(cfg, "head")
        except Exception as exc:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="MIGRATION_FAILED",
                    message=f"Migration failed: {exc}. Backup at: {backup_path}",
                    detail={"backup_path": str(backup_path)},
                ),
            )

        # VALIDATE
        try:
            check_svc = CheckService(self._vault)
            integrity = check_svc.check()
            if integrity.ok:
                issues = integrity.data.get("issues", [])
                error_count = sum(1 for i in issues if i.get("severity") == "error")
                if error_count > 0:
                    warnings.append(f"Post-migration integrity check found {error_count} errors")
        except Exception:
            warnings.append("Post-migration integrity check could not run")

        return ServiceResult(
            ok=True,
            op=op,
            data={
                "applied_count": pending_count,
                "current": check_result.data["head"],
                "backup_path": str(backup_path),
            },
            warnings=warnings,
        )

    def stamp_current(self) -> ServiceResult:
        """Stamp DB as at current head (for freshly created DBs)."""
        op = "upgrade"

        try:
            cfg = build_config(self._db_url())
            command.stamp(cfg, "head")
            script = ScriptDirectory.from_config(cfg)
            head = script.get_current_head()

            return ServiceResult(
                ok=True,
                op=op,
                data={
                    "stamped": True,
                    "current": head,
                },
            )
        except Exception as exc:
            return ServiceResult(
                ok=False,
                op=op,
                error=ServiceError(
                    code="STAMP_FAILED",
                    message=f"Failed to stamp database: {exc}",
                ),
            )
