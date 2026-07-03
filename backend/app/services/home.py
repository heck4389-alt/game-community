from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import cast, func, select
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.types import Date

from app.models import (
    Announcement,
    Category,
    Comment,
    NewsArticle,
    Post,
    PostView,
    SearchLog,
    SiteBanner,
    SiteEvent,
    User,
)
from app.categories import GUIDE_SLUG, NON_GAME_SLUGS, NOTICE_SLUG
from app.visitor_stats import get_visitor_stats

POST_WEIGHT = 3
COMMENT_WEIGHT = 2
VIEW_WEIGHT = 1
SEARCH_WEIGHT = 4


@dataclass
class PopularGame:
    category: Category
    score: float
    posts_24h: int
    comments_24h: int
    views_24h: int
    searches_24h: int


@dataclass
class HotPostItem:
    post: Post
    view_count: int
    comment_count: int
    hot_score: int


def since_24h() -> datetime:
    return datetime.now(timezone.utc) - timedelta(hours=24)


def get_today_stats(db: Session) -> dict[str, int]:
    today = datetime.now(timezone.utc).date()
    today_visitors, total_visitors = get_visitor_stats()
    return {
        "today_users": db.scalar(select(func.count(User.id)).where(cast(User.created_at, Date) == today)) or 0,
        "today_posts": db.scalar(select(func.count(Post.id)).where(cast(Post.created_at, Date) == today)) or 0,
        "today_comments": db.scalar(select(func.count(Comment.id)).where(cast(Comment.created_at, Date) == today))
        or 0,
        "today_visitors": today_visitors,
        "total_visitors": total_visitors,
    }


def get_popular_games(db: Session, limit: int = 10) -> list[PopularGame]:
    since = since_24h()
    categories = list(
        db.scalars(select(Category).where(Category.slug.notin_(NON_GAME_SLUGS)).order_by(Category.sort_order)).all()
    )

    results: list[PopularGame] = []
    for category in categories:
        posts_24h = db.scalar(
            select(func.count(Post.id)).where(Post.category_id == category.id, Post.created_at >= since)
        ) or 0
        comments_24h = db.scalar(
            select(func.count(Comment.id))
            .join(Post, Comment.post_id == Post.id)
            .where(Post.category_id == category.id, Comment.created_at >= since)
        ) or 0
        views_24h = db.scalar(
            select(func.count(PostView.id))
            .join(Post, PostView.post_id == Post.id)
            .where(Post.category_id == category.id, PostView.created_at >= since)
        ) or 0
        searches_24h = db.scalar(
            select(func.count(SearchLog.id)).where(
                SearchLog.category_id == category.id, SearchLog.created_at >= since
            )
        ) or 0
        score = (
            posts_24h * POST_WEIGHT
            + comments_24h * COMMENT_WEIGHT
            + views_24h * VIEW_WEIGHT
            + searches_24h * SEARCH_WEIGHT
        )
        results.append(
            PopularGame(
                category=category,
                score=score,
                posts_24h=posts_24h,
                comments_24h=comments_24h,
                views_24h=views_24h,
                searches_24h=searches_24h,
            )
        )

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:limit]


def get_popular_searches(db: Session, limit: int = 10) -> list[tuple[str, int]]:
    since = since_24h()
    rows = db.execute(
        select(SearchLog.query, func.count(SearchLog.id).label("cnt"))
        .where(SearchLog.created_at >= since)
        .group_by(SearchLog.query)
        .order_by(func.count(SearchLog.id).desc(), SearchLog.query.asc())
        .limit(limit)
    ).all()
    return [(row.query, row.cnt) for row in rows]


def _attach_post_metrics(db: Session, posts: list[Post]) -> list[HotPostItem]:
    since = since_24h()
    items: list[HotPostItem] = []
    for post in posts:
        view_count = db.scalar(select(func.count(PostView.id)).where(PostView.post_id == post.id)) or 0
        views_24h = db.scalar(
            select(func.count(PostView.id)).where(PostView.post_id == post.id, PostView.created_at >= since)
        ) or 0
        comment_count = len(post.comments)
        hot_score = views_24h * 2 + comment_count * 3
        items.append(
            HotPostItem(post=post, view_count=view_count, comment_count=comment_count, hot_score=hot_score)
        )
    return items


def get_hot_posts(db: Session, tab: str = "all", limit: int = 8) -> list[HotPostItem]:
    stmt = (
        select(Post)
        .join(Category)
        .options(selectinload(Post.author), selectinload(Post.category), selectinload(Post.comments))
        .where(Category.slug != NOTICE_SLUG)
        .order_by(Post.created_at.desc())
        .limit(30)
    )
    posts = list(db.scalars(stmt).all())
    items = _attach_post_metrics(db, posts)

    if tab == "popular":
        items.sort(key=lambda item: item.hot_score, reverse=True)
    elif tab == "comments":
        items.sort(key=lambda item: item.comment_count, reverse=True)
    elif tab == "latest":
        items.sort(key=lambda item: item.post.created_at, reverse=True)
    else:
        items.sort(key=lambda item: item.hot_score, reverse=True)

    return items[:limit]


def get_recommended_guides(db: Session, limit: int = 3) -> list[HotPostItem]:
    since = since_24h()
    posts = list(
        db.scalars(
            select(Post)
            .join(Category)
            .options(selectinload(Post.author), selectinload(Post.category), selectinload(Post.comments))
            .where(Category.slug == GUIDE_SLUG, Post.created_at >= since - timedelta(days=7))
            .order_by(Post.created_at.desc())
            .limit(20)
        ).all()
    )
    items = _attach_post_metrics(db, posts)
    items.sort(key=lambda item: item.view_count + item.comment_count * 2, reverse=True)
    return items[:limit]


def get_recent_comments(db: Session, limit: int = 6) -> list[Comment]:
    return list(
        db.scalars(
            select(Comment)
            .options(selectinload(Comment.author), selectinload(Comment.post).selectinload(Post.category))
            .order_by(Comment.created_at.desc())
            .limit(limit)
        ).all()
    )


def get_announcements(db: Session, limit: int = 5) -> list[Announcement]:
    return list(
        db.scalars(
            select(Announcement).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).limit(limit)
        ).all()
    )


def get_news_articles(db: Session, limit: int = 4) -> list[NewsArticle]:
    return list(db.scalars(select(NewsArticle).order_by(NewsArticle.created_at.desc()).limit(limit)).all())


def get_banners(db: Session) -> list[SiteBanner]:
    return list(
        db.scalars(
            select(SiteBanner).where(SiteBanner.is_active.is_(True)).order_by(SiteBanner.sort_order.asc())
        ).all()
    )


def get_events(db: Session, limit: int = 2) -> list[SiteEvent]:
    return list(
        db.scalars(
            select(SiteEvent).where(SiteEvent.is_active.is_(True)).order_by(SiteEvent.sort_order.asc()).limit(limit)
        ).all()
    )


def get_recent_users(db: Session, limit: int = 5) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc()).limit(limit)).all())
