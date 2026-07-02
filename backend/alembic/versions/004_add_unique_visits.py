"""add unique visitor tracking

Revision ID: 004
Revises: 003
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "unique_visits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("visitor_key", sa.String(length=36), nullable=False),
        sa.Column("visit_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visitor_key", "visit_date", name="uq_visitor_day"),
    )
    op.create_index(op.f("ix_unique_visits_visit_date"), "unique_visits", ["visit_date"], unique=False)
    op.create_index(op.f("ix_unique_visits_visitor_key"), "unique_visits", ["visitor_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_unique_visits_visitor_key"), table_name="unique_visits")
    op.drop_index(op.f("ix_unique_visits_visit_date"), table_name="unique_visits")
    op.drop_table("unique_visits")
