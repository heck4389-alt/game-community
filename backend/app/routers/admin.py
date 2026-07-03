from datetime import date

from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import cast, func, select
from sqlalchemy.orm import selectinload
from sqlalchemy.types import Date

from app.dependencies import CurrentUser, DbSession
from app.models import Announcement, Comment, NewsArticle, Post, User
from app.visitor_stats import get_visitor_stats

router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(current_user: CurrentUser):
    if not current_user or not current_user.is_admin:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
    return None


@router.get("", response_class=HTMLResponse)
def admin_dashboard(request: Request, db: DbSession, current_user: CurrentUser):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

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


@router.get("/content", response_class=HTMLResponse)
def admin_content_page(request: Request, db: DbSession, current_user: CurrentUser):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    announcements = list(
        db.scalars(select(Announcement).order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())).all()
    )
    news_articles = list(db.scalars(select(NewsArticle).order_by(NewsArticle.created_at.desc())).all())

    return request.app.state.templates.TemplateResponse(
        request,
        "admin_content.html",
        {
            "current_user": current_user,
            "announcements": announcements,
            "news_articles": news_articles,
            "error": None,
        },
    )


@router.post("/announcements")
def create_announcement(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    content: str = Form(...),
    is_pinned: str | None = Form(default=None),
):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    title = title.strip()
    content = content.strip()
    if not title or not content:
        return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)

    db.add(Announcement(title=title, content=content, is_pinned=bool(is_pinned)))
    db.commit()
    return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/announcements/{announcement_id}/edit", response_class=HTMLResponse)
def edit_announcement_page(
    request: Request,
    announcement_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    announcement = db.get(Announcement, announcement_id)
    if not announcement:
        return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)

    return request.app.state.templates.TemplateResponse(
        request,
        "admin_announcement_edit.html",
        {"current_user": current_user, "announcement": announcement, "error": None},
    )


@router.post("/announcements/{announcement_id}/edit")
def update_announcement(
    announcement_id: int,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    content: str = Form(...),
    is_pinned: str | None = Form(default=None),
):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    announcement = db.get(Announcement, announcement_id)
    if not announcement:
        return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)

    title = title.strip()
    content = content.strip()
    if not title or not content:
        return RedirectResponse(
            f"/admin/announcements/{announcement_id}/edit",
            status_code=status.HTTP_303_SEE_OTHER,
        )

    announcement.title = title
    announcement.content = content
    announcement.is_pinned = bool(is_pinned)
    db.commit()
    return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/announcements/{announcement_id}/delete")
def delete_announcement(
    announcement_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    item = db.get(Announcement, announcement_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/news")
def create_news(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    summary: str = Form(...),
    source: str = Form(default="GAMEPRY"),
):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    title = title.strip()
    summary = summary.strip()
    if not title or not summary:
        return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)

    db.add(NewsArticle(title=title, summary=summary, source=source.strip() or "GAMEPRY"))
    db.commit()
    return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/news/{news_id}/delete")
def delete_news(news_id: int, db: DbSession, current_user: CurrentUser):
    redirect = require_admin(current_user)
    if redirect:
        return redirect

    item = db.get(NewsArticle, news_id)
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse("/admin/content", status_code=status.HTTP_303_SEE_OTHER)
