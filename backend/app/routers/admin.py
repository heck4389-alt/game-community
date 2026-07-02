from datetime import date

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import cast, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.types import Date

from app.dependencies import CurrentUser, DbSession
from app.models import Comment, Post, User
from app.visitor_stats import get_visitor_stats

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: DbSession, current_user: CurrentUser):
    if not current_user or not current_user.is_admin:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    today = date.today()
    user_count = db.scalar(select(func.count(User.id))) or 0
    post_count = db.scalar(select(func.count(Post.id))) or 0
    comment_count = db.scalar(select(func.count(Comment.id))) or 0
    today_posts = db.scalar(
        select(func.count(Post.id)).where(cast(Post.created_at, Date) == today)
    ) or 0
    today_users = db.scalar(
        select(func.count(User.id)).where(cast(User.created_at, Date) == today)
    ) or 0
    today_visitors, total_visitors = get_visitor_stats()

    recent_users = list(db.scalars(select(User).order_by(User.created_at.desc()).limit(10)).all())
    recent_posts = list(
        db.scalars(
            select(Post)
            .options(selectinload(Post.author), selectinload(Post.category))
            .order_by(Post.created_at.desc())
            .limit(10)
        ).all()
    )

    return request.app.state.templates.TemplateResponse(
        request,
        "admin_dashboard.html",
        {
            "current_user": current_user,
            "user_count": user_count,
            "post_count": post_count,
            "comment_count": comment_count,
            "today_posts": today_posts,
            "today_users": today_users,
            "today_visitors": today_visitors,
            "total_visitors": total_visitors,
            "recent_users": recent_users,
            "recent_posts": recent_posts,
        },
    )
