from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.dependencies import CurrentUser, DbSession
from app.models import Category, Comment, Post
from app.permissions import can_manage_comment, can_manage_post
from app.services.tracking import record_post_view

router = APIRouter(prefix="/board", tags=["board"])


def get_categories(db: DbSession) -> list[Category]:
    return list(db.scalars(select(Category).order_by(Category.sort_order)).all())


def render_form(request: Request, status_code: int = 200, **context):
    defaults = {"current_user": None, "post": None, "error": None, "action": "create", "categories": []}
    defaults.update(context)
    return request.app.state.templates.TemplateResponse(
        request, "post_form.html", defaults, status_code=status_code
    )


@router.get("", response_class=HTMLResponse)
def board_list(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    category: str | None = Query(default=None),
):
    categories = get_categories(db)
    stmt = (
        select(Post)
        .options(selectinload(Post.author), selectinload(Post.category), selectinload(Post.comments))
        .order_by(Post.created_at.desc())
    )

    active_category = None
    if category:
        active_category = db.scalar(select(Category).where(Category.slug == category))
        if active_category:
            stmt = stmt.where(Post.category_id == active_category.id)

    posts = list(db.scalars(stmt).all())
    return request.app.state.templates.TemplateResponse(
        request,
        "board_list.html",
        {
            "current_user": current_user,
            "posts": posts,
            "categories": categories,
            "active_category": active_category,
        },
    )


@router.get("/new", response_class=HTMLResponse)
def new_post_page(request: Request, db: DbSession, current_user: CurrentUser):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return render_form(request, current_user=current_user, categories=get_categories(db))


@router.post("/new")
def create_post(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    categories = get_categories(db)
    title = title.strip()
    content = content.strip()
    category = db.get(Category, category_id)

    if not title or not content or not category:
        return render_form(
            request,
            current_user=current_user,
            categories=categories,
            post=None,
            error="제목, 내용, 카테고리를 모두 입력해 주세요.",
            action="create",
            title=title,
            content=content,
            selected_category_id=category_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    post = Post(title=title, content=content, author_id=current_user.id, category_id=category.id)
    db.add(post)
    db.commit()
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{post_id}", response_class=HTMLResponse)
def post_detail(request: Request, post_id: int, db: DbSession, current_user: CurrentUser):
    post = db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .options(
            selectinload(Post.author),
            selectinload(Post.category),
            selectinload(Post.comments).selectinload(Comment.author),
        )
    )
    if not post:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    visitor_key = request.cookies.get(settings.visitor_cookie_name)
    record_post_view(db, post.id, visitor_key)

    return request.app.state.templates.TemplateResponse(
        request,
        "post_detail.html",
        {"current_user": current_user, "post": post, "comment_error": None},
    )


@router.post("/{post_id}/comments")
def create_comment(
    request: Request,
    post_id: int,
    db: DbSession,
    current_user: CurrentUser,
    content: str = Form(...),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.scalar(
        select(Post)
        .where(Post.id == post_id)
        .options(
            selectinload(Post.author),
            selectinload(Post.category),
            selectinload(Post.comments).selectinload(Comment.author),
        )
    )
    if not post:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    content = content.strip()
    if not content:
        return request.app.state.templates.TemplateResponse(
            request,
            "post_detail.html",
            {"current_user": current_user, "post": post, "comment_error": "댓글 내용을 입력해 주세요."},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db.add(Comment(content=content, post_id=post.id, author_id=current_user.id))
    db.commit()
    return RedirectResponse(f"/board/{post_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{post_id}/comments/{comment_id}/delete")
def delete_comment(
    request: Request,
    post_id: int,
    comment_id: int,
    db: DbSession,
    current_user: CurrentUser,
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    comment = db.get(Comment, comment_id)
    if comment and can_manage_comment(current_user, comment):
        db.delete(comment)
        db.commit()
    return RedirectResponse(f"/board/{post_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{post_id}/edit", response_class=HTMLResponse)
def edit_post_page(request: Request, post_id: int, db: DbSession, current_user: CurrentUser):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.get(Post, post_id)
    if not post or not can_manage_post(current_user, post):
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    return render_form(
        request,
        current_user=current_user,
        categories=get_categories(db),
        post=post,
        error=None,
        action="edit",
    )


@router.post("/{post_id}/edit")
def update_post(
    request: Request,
    post_id: int,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    content: str = Form(...),
    category_id: int = Form(...),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.get(Post, post_id)
    categories = get_categories(db)
    if not post or not can_manage_post(current_user, post):
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    title = title.strip()
    content = content.strip()
    category = db.get(Category, category_id)

    if not title or not content or not category:
        return render_form(
            request,
            current_user=current_user,
            categories=categories,
            post=post,
            error="제목, 내용, 카테고리를 모두 입력해 주세요.",
            action="edit",
            title=title,
            content=content,
            selected_category_id=category_id,
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    post.title = title
    post.content = content
    post.category_id = category.id
    db.commit()
    return RedirectResponse(f"/board/{post_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{post_id}/delete")
def delete_post(request: Request, post_id: int, db: DbSession, current_user: CurrentUser):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.get(Post, post_id)
    if post and can_manage_post(current_user, post):
        db.delete(post)
        db.commit()
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
