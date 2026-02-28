"""Add high-resolution node timestamps for deterministic ordering.

Revision ID: 002_node_timestamps
Revises: 001_baseline
Create Date: 2026-02-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "002_node_timestamps"
down_revision: str | None = "001_baseline"
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    op.add_column("nodes", sa.Column("created_at", sa.Text(), nullable=True))
    op.add_column("nodes", sa.Column("modified_at", sa.Text(), nullable=True))

    # Preserve legacy day-granularity frontmatter fields while introducing
    # DB-only timestamp precision for ordering and session selection.
    op.execute(
        """
        UPDATE nodes
        SET
            created_at = COALESCE(created_at, CASE
                WHEN created IS NOT NULL THEN created || 'T00:00:00+00:00'
                ELSE NULL
            END),
            modified_at = COALESCE(modified_at, CASE
                WHEN modified IS NOT NULL THEN modified || 'T00:00:00+00:00'
                ELSE NULL
            END)
        """
    )


def downgrade() -> None:
    op.drop_column("nodes", "modified_at")
    op.drop_column("nodes", "created_at")
