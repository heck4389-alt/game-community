from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Category, User

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


def promote_admins() -> None:
    admin_names = [name.strip() for name in settings.admin_usernames.split(",") if name.strip()]
    if not admin_names:
        return

    db = SessionLocal()
    try:
        users = db.scalars(select(User).where(User.username.in_(admin_names))).all()
        changed = False
        for user in users:
            if not user.is_admin:
                user.is_admin = True
                changed = True
        if changed:
            db.commit()
            print(f"Admin privileges granted: {', '.join(user.username for user in users)}")
    finally:
        db.close()


def run_seed() -> None:
    seed_categories()
    promote_admins()


if __name__ == "__main__":
    run_seed()
