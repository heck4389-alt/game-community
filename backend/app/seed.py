from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category

DEFAULT_CATEGORIES = [
    {"name": "리그 오브 레전드", "slug": "lol", "icon": "⚔️", "sort_order": 1},
    {"name": "발로란트", "slug": "valorant", "icon": "🎯", "sort_order": 2},
    {"name": "스팀 / PC", "slug": "steam", "icon": "🖥️", "sort_order": 3},
    {"name": "콘솔", "slug": "console", "icon": "🎮", "sort_order": 4},
    {"name": "모바일", "slug": "mobile", "icon": "📱", "sort_order": 5},
    {"name": "자유게시판", "slug": "free", "icon": "💬", "sort_order": 6},
]


def seed_categories() -> None:
    db = SessionLocal()
    try:
        existing = db.scalar(select(Category.id).limit(1))
        if existing:
            return

        for item in DEFAULT_CATEGORIES:
            db.add(Category(**item))
        db.commit()
        print("Default categories seeded.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()
