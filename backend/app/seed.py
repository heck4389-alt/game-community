from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Category, SiteBanner, User

DEFAULT_CATEGORIES = [
    {"name": "공략", "slug": "guide", "icon": "⭐", "sort_order": 1},
    {"name": "공지", "slug": "notice", "icon": "📢", "sort_order": 2},
    {"name": "리그 오브 레전드", "slug": "lol", "icon": "⚔️", "sort_order": 3},
    {"name": "발로란트", "slug": "valorant", "icon": "🎯", "sort_order": 4},
    {"name": "스팀 / PC", "slug": "steam", "icon": "🖥️", "sort_order": 5},
    {"name": "콘솔", "slug": "console", "icon": "🎮", "sort_order": 6},
    {"name": "모바일", "slug": "mobile", "icon": "📱", "sort_order": 7},
    {"name": "자유게시판", "slug": "free", "icon": "💬", "sort_order": 8},
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


def seed_portal_content() -> None:
    """공지·뉴스·이벤트는 관리자만 작성. 초기 더미 데이터는 넣지 않습니다."""
    db = SessionLocal()
    try:
        if db.scalar(select(SiteBanner.id).limit(1)):
            return

        db.add(
            SiteBanner(
                title="게임프리 커뮤니티",
                subtitle="게임 정보와 팁을 함께 나누는 공간입니다. 커뮤니티에서 글을 작성해 보세요!",
                button_text="커뮤니티 바로가기",
                link_url="/board",
                gradient_class="banner-1",
                sort_order=1,
            )
        )
        db.commit()
        print("Default banner seeded.")
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
    seed_portal_content()
    promote_admins()


if __name__ == "__main__":
    run_seed()
