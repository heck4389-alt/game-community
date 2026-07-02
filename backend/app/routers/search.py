from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.models import Post
from app.services.tracking import match_category_id, record_search

router = APIRouter(tags=["search"])


@router.get("/search", response_class=HTMLResponse)
def search_posts(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    q: str = Query(default=""),
):
    query = q.strip()
    visitor_key = request.cookies.get(settings.visitor_cookie_name)
    category_id = None

    if query:
        category_id = match_category_id(db, query)
        record_search(db, query, category_id=category_id, visitor_key=visitor_key)

    posts = []
    if query:
        posts = list(
            db.scalars(
                select(Post)
                .options(selectinload(Post.author), selectinload(Post.category), selectinload(Post.comments))
                .where(or_(Post.title.ilike(f"%{query}%"), Post.content.ilike(f"%{query}%")))
                .order_by(Post.created_at.desc())
                .limit(30)
            ).all()
        )

    return request.app.state.templates.TemplateResponse(
        request,
        "search_results.html",
        {"current_user": current_user, "query": query, "posts": posts},
    )
