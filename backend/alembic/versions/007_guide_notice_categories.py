"""add guide and notice categories

Revision ID: 007
Revises: 006
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE categories SET sort_order = sort_order + 2 WHERE slug NOT IN ('guide', 'notice')")
    )
    for name, slug, icon, sort_order in [
        ("공략", "guide", "⭐", 1),
        ("공지", "notice", "📢", 2),
    ]:
        conn.execute(
            sa.text(
                """
                INSERT INTO categories (name, slug, icon, sort_order)
                SELECT :name, :slug, :icon, :sort_order
                WHERE NOT EXISTS (SELECT 1 FROM categories WHERE slug = :slug)
                """
            ),
            {"name": name, "slug": slug, "icon": icon, "sort_order": sort_order},
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM categories WHERE slug IN ('guide', 'notice')"))
    conn.execute(
        sa.text("UPDATE categories SET sort_order = sort_order - 2 WHERE sort_order > 2")
    )
