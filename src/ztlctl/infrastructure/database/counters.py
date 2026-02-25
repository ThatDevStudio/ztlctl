"""Atomic sequential ID generation for LOG and TASK content types.

Uses the ``id_counters`` table with serialized transactions to ensure
no gaps or duplicates. Minimum 4 digits, grows naturally past 9999.
(DESIGN.md Section 7)

The caller owns the transaction — pass a ``Connection`` obtained from
``engine.begin()`` so the counter increment participates in the same
atomic transaction as the surrounding writes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update

from ztlctl.infrastructure.database.schema import id_counters

if TYPE_CHECKING:
    from sqlalchemy import Connection

_VALID_PREFIXES = frozenset({"LOG-", "TASK-"})


def next_sequential_id(conn: Connection, type_prefix: str) -> str:
    """Claim the next sequential ID for *type_prefix*.

    The caller must provide a ``Connection`` within an active transaction
    (e.g. from ``engine.begin()``).  The counter increment becomes part
    of that transaction — commit or rollback is the caller's responsibility.

    Args:
        conn: Active SQLAlchemy connection (caller owns the transaction).
        type_prefix: One of ``"LOG-"`` or ``"TASK-"``.

    Returns:
        The new ID string (e.g. ``"LOG-0001"`` or ``"TASK-0042"``).

    Raises:
        ValueError: If *type_prefix* is not a recognized sequential type.
    """
    if type_prefix not in _VALID_PREFIXES:
        msg = (
            f"Unknown sequential type prefix: {type_prefix!r}. "
            f"Expected one of {sorted(_VALID_PREFIXES)}"
        )
        raise ValueError(msg)

    row = conn.execute(
        select(id_counters.c.next_value).where(id_counters.c.type_prefix == type_prefix)
    ).one()

    current_value: int = row.next_value

    conn.execute(
        update(id_counters)
        .where(id_counters.c.type_prefix == type_prefix)
        .values(next_value=current_value + 1)
    )

    return f"{type_prefix}{current_value:04d}"
