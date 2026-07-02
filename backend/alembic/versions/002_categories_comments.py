"""add categories and comments

Revision ID: 002
Revises: 001
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    categories = op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("slug", sa.String(length=50), nullable=False),
        sa.Column("icon", sa.String(length=10), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )

    op.bulk_insert(
        categories,
        [
            {"id": 1, "name": "리그 오브 레전드", "slug": "lol", "icon": "⚔️", "sort_order": 1},
            {"id": 2, "name": "발로란트", "slug": "valorant", "icon": "🎯", "sort_order": 2},
            {"id": 3, "name": "스팀 / PC", "slug": "steam", "icon": "🖥️", "sort_order": 3},
            {"id": 4, "name": "콘솔", "slug": "console", "icon": "🎮", "sort_order": 4},
            {"id": 5, "name": "모바일", "slug": "mobile", "icon": "📱", "sort_order": 5},
            {"id": 6, "name": "자유게시판", "slug": "free", "icon": "💬", "sort_order": 6},
        ],
    )

    op.add_column("posts", sa.Column("category_id", sa.Integer(), nullable=True))
    op.execute("UPDATE posts SET category_id = 6 WHERE category_id IS NULL")
    op.alter_column("posts", "category_id", nullable=False)
    op.create_foreign_key("fk_posts_category_id", "posts", "categories", ["category_id"], ["id"])
    op.create_index(op.f("ix_posts_category_id"), "posts", ["category_id"], unique=False)

    op.create_table(
        "comments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_comments_author_id"), "comments", ["author_id"], unique=False)
    op.create_index(op.f("ix_comments_post_id"), "comments", ["post_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_comments_post_id"), table_name="comments")
    op.drop_index(op.f("ix_comments_author_id"), table_name="comments")
    op.drop_table("comments")
    op.drop_index(op.f("ix_posts_category_id"), table_name="posts")
    op.drop_constraint("fk_posts_category_id", "posts", type_="foreignkey")
    op.drop_column("posts", "category_id")
    op.drop_table("categories")
