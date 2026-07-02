from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select

from app.dependencies import CurrentUser, DbSession
from app.models import Post

router = APIRouter(prefix="/board", tags=["board"])


@router.get("", response_class=HTMLResponse)
def board_list(request: Request, db: DbSession, current_user: CurrentUser):
    posts = db.scalars(select(Post).order_by(Post.created_at.desc())).all()
    return request.app.state.templates.TemplateResponse(
        request,
        "board_list.html",
        {"current_user": current_user, "posts": posts},
    )


@router.get("/new", response_class=HTMLResponse)
def new_post_page(request: Request, current_user: CurrentUser):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    return request.app.state.templates.TemplateResponse(
        request,
        "post_form.html",
        {"current_user": current_user, "post": None, "error": None, "action": "create"},
    )


@router.post("/new")
def create_post(
    request: Request,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    content: str = Form(...),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    title = title.strip()
    content = content.strip()
    if not title or not content:
        return request.app.state.templates.TemplateResponse(
            request,
            "post_form.html",
            {
                "current_user": current_user,
                "post": None,
                "error": "제목과 내용을 모두 입력해 주세요.",
                "action": "create",
                "title": title,
                "content": content,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    post = Post(title=title, content=content, author_id=current_user.id)
    db.add(post)
    db.commit()
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/{post_id}", response_class=HTMLResponse)
def post_detail(request: Request, post_id: int, db: DbSession, current_user: CurrentUser):
    post = db.get(Post, post_id)
    if not post:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
    return request.app.state.templates.TemplateResponse(
        request,
        "post_detail.html",
        {"current_user": current_user, "post": post},
    )


@router.get("/{post_id}/edit", response_class=HTMLResponse)
def edit_post_page(request: Request, post_id: int, db: DbSession, current_user: CurrentUser):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.get(Post, post_id)
    if not post or post.author_id != current_user.id:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    return request.app.state.templates.TemplateResponse(
        request,
        "post_form.html",
        {"current_user": current_user, "post": post, "error": None, "action": "edit"},
    )


@router.post("/{post_id}/edit")
def update_post(
    request: Request,
    post_id: int,
    db: DbSession,
    current_user: CurrentUser,
    title: str = Form(...),
    content: str = Form(...),
):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.get(Post, post_id)
    if not post or post.author_id != current_user.id:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)

    title = title.strip()
    content = content.strip()
    if not title or not content:
        return request.app.state.templates.TemplateResponse(
            request,
            "post_form.html",
            {
                "current_user": current_user,
                "post": post,
                "error": "제목과 내용을 모두 입력해 주세요.",
                "action": "edit",
                "title": title,
                "content": content,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    post.title = title
    post.content = content
    db.commit()
    return RedirectResponse(f"/board/{post_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/{post_id}/delete")
def delete_post(request: Request, post_id: int, db: DbSession, current_user: CurrentUser):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    post = db.get(Post, post_id)
    if post and post.author_id == current_user.id:
        db.delete(post)
        db.commit()
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
