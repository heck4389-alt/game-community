from sqlalchemy import select

from app.config import settings
from app.database import SessionLocal
from app.models import Announcement, Category, NewsArticle, SiteBanner, SiteEvent, User

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


def seed_portal_content() -> None:
    db = SessionLocal()
    try:
        if db.scalar(select(Announcement.id).limit(1)):
            return

        db.add_all(
            [
                Announcement(title="[공지] 게임프리 커뮤니티 오픈 안내", is_pinned=True),
                Announcement(title="[안내] 커뮤니티 이용 규칙 및 신고 방법"),
                Announcement(title="[점검] 7/5(토) 02:00~04:00 서버 점검 예정"),
                Announcement(title="[이벤트] 신규 가입자 환영 이벤트 진행 중"),
            ]
        )
        db.add_all(
            [
                NewsArticle(
                    title="2026 e스포츠 월드컵, 국내 대표팀 8강 진출",
                    summary="조별리그 마지막 경기에서 역전승을 거두며 8강에 안착했습니다.",
                    source="GAMEPRY NEWS",
                ),
                NewsArticle(
                    title="발로란트 신규 에이전트 'Veto' 공개",
                    summary="맵 지형을 바꾸는 독특한 스킬셋으로 기대를 모으고 있습니다.",
                    source="GAMEPRY NEWS",
                ),
                NewsArticle(
                    title="스팀 여름 세일, 인기 타이틀 최대 80% 할인",
                    summary="7월 15일까지 진행되는 대규모 할인 이벤트가 시작됐습니다.",
                    source="GAMEPRY NEWS",
                ),
                NewsArticle(
                    title="PS5 독점작 'Stellar Odyssey' 출시 임박",
                    summary="오픈월드 SF RPG, 메타 점수 90점대 예상.",
                    source="GAMEPRY NEWS",
                ),
            ]
        )
        db.add_all(
            [
                SiteBanner(
                    title="게임프리 커뮤니티에 오신 것을 환영합니다",
                    subtitle="공략, 질문, 정보를 카테고리별로 나눠 공유하세요. 지금 바로 글을 작성해 보세요!",
                    button_text="커뮤니티 바로가기",
                    link_url="/board",
                    gradient_class="banner-1",
                    sort_order=1,
                ),
                SiteBanner(
                    title="HOT 게시글 & 추천 공략",
                    subtitle="최근 24시간 조회수와 댓글 수를 기준으로 인기 콘텐츠를 자동 추천합니다.",
                    button_text="HOT 글 보기",
                    link_url="/?tab=popular",
                    gradient_class="banner-2",
                    sort_order=2,
                ),
            ]
        )
        db.add_all(
            [
                SiteEvent(
                    title="여름맞이 포인트 이벤트",
                    description="글 작성, 댓글, 출석으로 포인트를 모아 굿즈에 응모하세요!",
                    link_url="/board",
                    sort_order=1,
                ),
                SiteEvent(
                    title="신규 가입자 환영 이벤트",
                    description="가입 후 첫 글 작성 시 커뮤니티 배지가 지급됩니다.",
                    link_url="/register",
                    sort_order=2,
                ),
            ]
        )
        db.commit()
        print("Portal content seeded.")
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
