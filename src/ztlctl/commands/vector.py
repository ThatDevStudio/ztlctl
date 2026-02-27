"""Command group: semantic search vector operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import click

from ztlctl.commands._base import ZtlGroup
from ztlctl.services.vector import VectorService

if TYPE_CHECKING:
    from ztlctl.commands._context import AppContext

_VECTOR_EXAMPLES = """\
  ztlctl vector status
  ztlctl vector reindex
  ztlctl --json vector status"""


@click.group(cls=ZtlGroup, examples=_VECTOR_EXAMPLES)
@click.pass_obj
def vector(app: AppContext) -> None:
    """Manage semantic search vector index."""


@vector.command(
    examples="""\
  ztlctl vector status
  ztlctl --json vector status"""
)
@click.pass_obj
def status(app: AppContext) -> None:
    """Check semantic search availability and index status."""
    from ztlctl.services.result import ServiceResult

    vec_svc = VectorService(app.vault)
    available = vec_svc.is_available()

    data = {"available": available, "message": ""}
    if available:
        data["message"] = "Semantic search is available"
    else:
        data["message"] = (
            "Semantic search unavailable — install sqlite-vec and sentence-transformers"
        )

    app.emit(ServiceResult(ok=True, op="vector_status", data=data))


@vector.command(
    examples="""\
  ztlctl vector reindex
  ztlctl --json vector reindex"""
)
@click.pass_obj
def reindex(app: AppContext) -> None:
    """Rebuild the vector index for all content."""
    vec_svc = VectorService(app.vault)
    if not vec_svc.is_available():
        from ztlctl.services.result import ServiceError, ServiceResult

        app.emit(
            ServiceResult(
                ok=False,
                op="vector_reindex",
                error=ServiceError(
                    code="SEMANTIC_UNAVAILABLE",
                    message="Semantic search unavailable — install ztlctl[semantic]",
                ),
            )
        )
        return
    vec_svc.ensure_table()
    result = vec_svc.reindex_all()
    app.emit(result)
