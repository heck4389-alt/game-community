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

    next_id = conn.execute(sa.text("SELECT COALESCE(MAX(id), 0) FROM categories")).scalar() or 0
    for offset, (name, slug, icon, sort_order) in enumerate(
        [
            ("공략", "guide", "⭐", 1),
            ("공지", "notice", "📢", 2),
        ],
        start=1,
    ):
        conn.execute(
            sa.text(
                """
                INSERT INTO categories (id, name, slug, icon, sort_order)
                SELECT :id, :name, :slug, :icon, :sort_order
                WHERE NOT EXISTS (SELECT 1 FROM categories WHERE slug = :slug)
                """
            ),
            {
                "id": next_id + offset,
                "name": name,
                "slug": slug,
                "icon": icon,
                "sort_order": sort_order,
            },
        )

    conn.execute(sa.text("CREATE SEQUENCE IF NOT EXISTS categories_id_seq"))
    conn.execute(
        sa.text(
            "SELECT setval('categories_id_seq', GREATEST((SELECT COALESCE(MAX(id), 1) FROM categories), 1))"
        )
    )
    conn.execute(sa.text("ALTER TABLE categories ALTER COLUMN id SET DEFAULT nextval('categories_id_seq')"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM categories WHERE slug IN ('guide', 'notice')"))
    conn.execute(
        sa.text("UPDATE categories SET sort_order = sort_order - 2 WHERE sort_order > 2")
    )
