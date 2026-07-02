from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse

from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.services.home import (
    get_announcements,
    get_banners,
    get_events,
    get_hot_posts,
    get_news_articles,
    get_popular_games,
    get_popular_searches,
    get_recent_comments,
    get_recent_users,
    get_recommended_guides,
    get_today_stats,
)

router = APIRouter(tags=["home"])


@router.get("/", response_class=HTMLResponse)
def home_page(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    tab: str = Query(default="all"),
):
    return request.app.state.templates.TemplateResponse(
        request,
        "home.html",
        {
            "current_user": current_user,
            "banners": get_banners(db),
            "hot_posts": get_hot_posts(db, tab=tab),
            "hot_tab": tab,
            "news_articles": get_news_articles(db),
            "recommended_guides": get_recommended_guides(db),
            "recent_comments": get_recent_comments(db),
            "announcements": get_announcements(db),
            "popular_games": get_popular_games(db),
            "popular_searches": get_popular_searches(db),
            "events": get_events(db),
            "recent_users": get_recent_users(db),
            "today_stats": get_today_stats(db),
        },
    )
