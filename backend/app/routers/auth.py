from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import CurrentUser, DbSession
from app.models import User
from app.security import hash_password, verify_password

router = APIRouter(tags=["auth"])


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request, current_user: CurrentUser):
    if current_user:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
    return request.app.state.templates.TemplateResponse(
        request, "register.html", {"current_user": None, "error": None}
    )


@router.post("/register")
def register(
    request: Request,
    db: DbSession,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    error = None
    if len(username) < 3:
        error = "아이디는 3자 이상이어야 합니다."
    elif len(password) < 6:
        error = "비밀번호는 6자 이상이어야 합니다."
    elif password != password_confirm:
        error = "비밀번호가 일치하지 않습니다."

    if error:
        return request.app.state.templates.TemplateResponse(
            request,
            "register.html",
            {"current_user": None, "error": error, "username": username, "email": email},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    user = User(username=username.strip(), email=email.strip().lower(), hashed_password=hash_password(password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return request.app.state.templates.TemplateResponse(
            request,
            "register.html",
            {
                "current_user": None,
                "error": "이미 사용 중인 아이디 또는 이메일입니다.",
                "username": username,
                "email": email,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, current_user: CurrentUser):
    if current_user:
        return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
    return request.app.state.templates.TemplateResponse(
        request, "login.html", {"current_user": None, "error": None}
    )


@router.post("/login")
def login(
    request: Request,
    db: DbSession,
    username: str = Form(...),
    password: str = Form(...),
):
    user = db.scalar(select(User).where(User.username == username.strip()))
    if not user or not verify_password(password, user.hashed_password):
        return request.app.state.templates.TemplateResponse(
            request,
            "login.html",
            {"current_user": None, "error": "아이디 또는 비밀번호가 올바르지 않습니다.", "username": username},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    request.session["user_id"] = user.id
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/board", status_code=status.HTTP_303_SEE_OTHER)
